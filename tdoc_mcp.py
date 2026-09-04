# -*- coding: utf-8 -*-
"""腾讯文档 MCP 直连封装（http://127.0.0.1:49451/.../mcp）。

背景：历史用的 mcporter.cmd 在本机已不存在，且 tencentdocs.py 依赖宿主注入
TDOC_OAUTH_ACCESS_TOKEN（Bash 环境里没有）。但宿主把 connector 的 url + Bearer
token 放在了环境变量 CODEBUDDY_MCP_CONFIG 里，可直接 HTTP JSON-RPC 调用。

用法：
    from tdoc_mcp import call, list_tools
    r = call('smartsheet.list_records', {'file_id': 'xxx', 'sheet_id': 'yyy'})
    list_tools()   # 打印可用工具名

判成败：解析 JSON 的 error 字段（响应恒含 "error": ""，不能用字符串包含判断）。
"""

import json
import os
import sys

try:
    import urllib.request as _u
except ImportError:  # pragma: no cover
    import urllib2 as _u  # type: ignore

_SERVICE = "tencent-docs"


def _endpoint():
    """从 CODEBUDDY_MCP_CONFIG 读出 tencent-docs 的 url 与 headers。"""
    cfg = os.environ.get("CODEBUDDY_MCP_CONFIG")
    if not cfg:
        raise RuntimeError("NO_CONFIG: CODEBUDDY_MCP_CONFIG 未设置")
    try:
        data = json.loads(cfg)
    except ValueError as e:
        raise RuntimeError("BAD_CONFIG: %s" % e)
    srv = (data.get("mcpServers") or {}).get(_SERVICE)
    if not srv:
        raise RuntimeError("NO_SERVICE: %s 不在 mcpServers 中" % _SERVICE)
    return srv["url"], srv.get("headers", {})


def _post(url, headers, payload):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = _u.Request(url, data=body, method="POST")
    for k, v in headers.items():
        req.add_header(k, v)
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json, text/event-stream")
    with _u.urlopen(req, timeout=120) as resp:
        return resp.read().decode("utf-8", "replace")


def _parse(raw):
    """解析 MCP 响应：可能是裸 JSON，也可能是 SSE（data: {...}）。"""
    raw = (raw or "").strip()
    if not raw:
        return {"error": "empty response"}
    # SSE：取最后一条 data:
    if raw.startswith("event:") or "\ndata:" in raw or raw.startswith("data:"):
        chunks = [ln[5:].strip() for ln in raw.splitlines() if ln.startswith("data:")]
        chunks = [c for c in chunks if c and c != "[DONE]"]
        if chunks:
            raw = chunks[-1]
    try:
        return json.loads(raw)
    except ValueError:
        return {"error": "unparsable: %s" % raw[:400]}


_RPC_ID = [0]


def call(tool, args, retries=3, wait=10):
    """调用 MCP 工具，返回解析后的 dict。失败重试。"""
    import time

    url, headers = _endpoint()
    last = None
    for attempt in range(retries):
        _RPC_ID[0] += 1
        payload = {
            "jsonrpc": "2.0",
            "id": _RPC_ID[0],
            "method": "tools/call",
            "params": {"name": tool, "arguments": args},
        }
        try:
            resp = _parse(_post(url, headers, payload))
        except Exception as e:  # 网络层异常
            resp = {"error": "HTTP_ERROR: %s" % e}
        # MCP 业务结果包在 result.content[0].text 里（内容是 JSON 字符串）
        result = None
        if isinstance(resp, dict):
            if resp.get("error"):
                last = resp
            else:
                result = resp.get("result")
        if result is not None:
            content = result.get("content")
            if isinstance(content, list) and content:
                txt = content[0].get("text", "")
                try:
                    parsed = json.loads(txt)
                except ValueError:
                    parsed = {"raw": txt}
                # 业务层 error 为空串即成功
                if isinstance(parsed, dict) and parsed.get("error"):
                    last = parsed
                else:
                    return parsed
                last = parsed
            else:
                return result
        if attempt < retries - 1:
            sys.stderr.write(
                "[retry %d/%d] %s -> %s\n" % (attempt + 1, retries, tool, str(last)[:200])
            )
            time.sleep(wait * (attempt + 1))
    return last if last is not None else {"error": "unknown failure"}


def ok(resp):
    """响应是否成功：error 字段为空即成功。"""
    if isinstance(resp, dict):
        return not resp.get("error")
    return False


def get_field(record, name):
    """取记录里某个字段的值（文本/数字/日期戳统一转 str；取不到返回 None）。

    🚨 腾讯文档 smartsheet 的 list_records 返回的是 **field_values 列表**，
    不是 fields 字典。历史脚本按 `r['fields']` 解析，会把全部日期判成 MISSING，
    进而每��都走 add_records 重复新增（2026-08-20~25 曾连续 6 天双记录）。
    """
    for fv in record.get("field_values") or []:
        if fv.get("field") != name:
            continue
        tv = fv.get("text_value")
        if isinstance(tv, dict):
            for it in tv.get("items") or []:
                if it.get("text") is not None:
                    return str(it["text"])
        if fv.get("number_value") is not None:
            return str(fv["number_value"])
        if fv.get("string_value") is not None:
            return str(fv["string_value"])
        return None
    # 兼容少数返回 fields 字典的情况
    v = (record.get("fields") or {}).get(name)
    if isinstance(v, dict):
        tv = v.get("text_value")
        if isinstance(tv, dict):
            for it in tv.get("items") or []:
                if it.get("text") is not None:
                    return str(it["text"])
        for k in ("number_value", "string_value"):
            if v.get(k) is not None:
                return str(v[k])
        return None
    return str(v) if v is not None else None


def find_record_id(records, date_field, expect):
    """在 records 里按日期字段找 record_id，expect 用 str 比较。"""
    for r in records:
        if get_field(r, date_field) == str(expect):
            return r.get("record_id")
    return None


def list_tools():
    url, headers = _endpoint()
    _RPC_ID[0] += 1
    payload = {"jsonrpc": "2.0", "id": _RPC_ID[0], "method": "tools/list"}
    resp = _parse(_post(url, headers, payload))
    names = []
    for t in (resp.get("result") or {}).get("tools", []) or []:
        names.append(t.get("name"))
    return names


if __name__ == "__main__":
    names = list_tools()
    hit = [n for n in names if "smart" in n.lower()]
    print("total tools:", len(names))
    print("--- smartsheet 相关 ---")
    for n in hit:
        print(" ", n)
