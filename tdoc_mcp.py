# -*- coding: utf-8 -*-
"""腾讯文档 MCP 直连封装。

端点候选顺序（2026-09-21 重写）：
  ① 环境变量 TDOC_OAUTH_ACCESS_TOKEN / TDOC_ONEID_ACCESS_TOKEN（宿主直接注入）
  ② **V2 Gateway 票据通道**（本次新增，根治方案）：
     用 CODEBUDDY_MCP_CONFIG 里 connector-proxy 的 url + 整组 headers，
     GET {gateway}/internal/tencent-docs/tokens 换取 personal / enterprise 票据，
     再直连 https://docs.qq.com/openapi/mcp（224 个工具，含 30 个 smartsheet.*）。
  ③ env 里的 tencent-docs 条目（宿主把连接器挂进本会话时才有）
  ④ 本地缓存 data/.tdoc_endpoint.json（端口会随主程序重启变化，仅兜底）

背景：2026-09 起宿主把 mcpServers 改成统一的 connector-proxy，env 里查不到
tencent-docs 条目，旧版只能等宿主挂载，导致同步长期失败。② 绕开了这个依赖：
只要连接器授权过，网关就能发票据，不要求连接器出现在当前会话。

用法：
    from tdoc_mcp import call, list_tools, load_table
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


_CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "data", ".tdoc_endpoint.json")


_EP_STATE = {"url": None, "headers": None}

# 票据进程内缓存（网关是本地调用，很便宜，但仍避免 tools/list 反复取）
_TOK_STATE = {"fetched": False, "oauth": "", "oneid": "", "api_base": "", "reason": ""}

_DEFAULT_API_BASE = "https://docs.qq.com"


def _no_proxy_opener():
    return _u.build_opener(_u.ProxyHandler({}))


def _gateway_token():
    """从宿主 V2 MCP Gateway 换取腾讯文档票据。

    成功返回 (oauth, oneid, api_base)；任一为空表示对应侧不可用，reason 记录原因。
    🚨 请求必须整组透传 connector-proxy 的 headers：除 Authorization 外还有
    X-WorkBuddy-MCP-Context（宿主签发的会话信封），只带 Authorization 会被 401。
    """
    if _TOK_STATE["fetched"]:
        return (_TOK_STATE["oauth"], _TOK_STATE["oneid"], _TOK_STATE["api_base"])

    _TOK_STATE["fetched"] = True
    cfg = os.environ.get("CODEBUDDY_MCP_CONFIG")
    if not cfg:
        _TOK_STATE["reason"] = "no_mcp_config"
        return "", "", ""
    try:
        servers = json.loads(cfg).get("mcpServers") or {}
        # 宿主 V2 Gateway 条目名是 connector-proxy（workbuddy 是迁移期旧名，兜底）
        server = servers.get("connector-proxy") or servers.get("workbuddy") or {}
        gateway_url = server.get("url") or ""
        gw_headers = {k: v for k, v in (server.get("headers") or {}).items()
                      if isinstance(k, str) and isinstance(v, str) and v}
    except ValueError:
        _TOK_STATE["reason"] = "bad_mcp_config"
        return "", "", ""

    if not (gateway_url.endswith("/mcp") and
            any(k.lower() == "authorization" for k in gw_headers)):
        _TOK_STATE["reason"] = "no_gateway_entry"
        return "", "", ""

    try:
        req = _u.Request(gateway_url + "/internal/tencent-docs/tokens",
                         headers=gw_headers, method="GET")
        with _no_proxy_opener().open(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:  # noqa: BLE001
        _TOK_STATE["reason"] = "provider_unreachable(%s)" % type(e).__name__
        return "", "", ""

    personal = data.get("personal") or {}
    enterprise = data.get("enterprise") or {}
    oauth = str(personal["token"]) if personal.get("available") and personal.get("token") else ""
    oneid = str(enterprise["token"]) if enterprise.get("available") and enterprise.get("token") else ""
    api_base = data.get("apiBase") or ""
    _TOK_STATE.update({"oauth": oauth, "oneid": oneid, "api_base": api_base,
                       "reason": "" if (oauth or oneid) else
                                 "personal=%s enterprise=%s" % (
                                     personal.get("reason") or "unavailable",
                                     enterprise.get("reason") or "unavailable")})
    return oauth, oneid, api_base


def _candidates():
    """候选端点，按优先级 yield (url, headers, src)。

    2026-09-21 变更：新增 V2 Gateway 票据通道。env 里没有 tencent-docs 条目也能用，
    只要连接器授权过即可。apiBase 由网关下发（专享版域名），本环境常不可达，
    故同时给出 docs.qq.com 公网兜底，由 _alive 探活剔除不可达者。
    """
    oauth, oneid, api_base = "", "", ""
    # ① 宿主直接注入的环境变量优先
    env_oauth = os.environ.get("TDOC_OAUTH_ACCESS_TOKEN", "")
    env_oneid = os.environ.get("TDOC_ONEID_ACCESS_TOKEN", "")
    if env_oauth or env_oneid:
        oauth, oneid = env_oauth, env_oneid
        api_base = os.environ.get("TDOC_API_BASE_URL", "")
    else:
        oauth, oneid, api_base = _gateway_token()

    if oauth or oneid:
        headers = {"User-Agent": "Workbuddy Plugin"}
        if oauth:
            headers["Authorization"] = "Bearer " + oauth
        if oneid:
            headers["X-Oneid-Access-Token"] = oneid
        if api_base:
            yield api_base.rstrip("/") + "/openapi/mcp", headers, "gateway(apibase)"
        yield _DEFAULT_API_BASE + "/openapi/mcp", headers, "gateway"

    # ③ env 里的 tencent-docs 条目（宿主把连接器挂进本会话时才有）
    cfg = os.environ.get("CODEBUDDY_MCP_CONFIG")
    srv = None
    if cfg:
        try:
            srv = (json.loads(cfg).get("mcpServers") or {}).get(_SERVICE)
        except ValueError:
            srv = None
    if srv and srv.get("url"):
        yield srv["url"], srv.get("headers", {}), "env"

    # ④ 本地缓存兜底（端口随主程序重启变化，多数情况已失效）
    try:
        with open(_CACHE_FILE, "r", encoding="utf-8") as f:
            cache = json.load(f)
        if cache.get("url"):
            yield cache["url"], cache.get("headers", {}), "cache"
    except (OSError, ValueError):
        pass


def _alive(url, headers):
    """探活：tools/list 能通即认为端点有效；任何异常一律 False（不外抛）。"""
    try:
        _post(url, headers, {"jsonrpc": "2.0", "id": 0,
                             "method": "tools/list", "params": {}}, timeout=10)
        return True
    except Exception:
        return False


def _endpoint():
    """选可用端点并进程内缓存；取用前先探活，避免死端口静默 502。

    返回 (url, headers)。全部不可用时抛出带明确原因的 RuntimeError。
    """
    if _EP_STATE["url"]:
        return _EP_STATE["url"], _EP_STATE["headers"]

    tried = []
    for url, headers, src in _candidates():
        if _alive(url, headers):
            _EP_STATE["url"], _EP_STATE["headers"] = url, headers
            # 落盘兜底：自动化会话里可能拿不到 CODEBUDDY_MCP_CONFIG，缓存端点可救命。
            # 票据过期时 _alive 会失败并自动回退到后续候选，不会静默写坏数据。
            if src.startswith("gateway") or src == "env":
                try:
                    import datetime
                    os.makedirs(os.path.dirname(_CACHE_FILE), exist_ok=True)
                    with open(_CACHE_FILE, "w", encoding="utf-8") as f:
                        json.dump({"url": url, "headers": headers, "src": src,
                                   "cached_at": datetime.datetime.now().isoformat(timespec="seconds")}, f)
                except OSError:
                    pass
            return url, headers
        tried.append("%s(%s)" % (src, url))

    tok_reason = _TOK_STATE.get("reason") or "n/a"
    raise RuntimeError(
        "TDOC_UNREACHABLE: 腾讯文档端点均不可用（已试=%s；票据通道=%s）。"
        "排查：①网关票据通道应在连接器已授权时可用，若显示 not_connected/"
        "connector_disabled，需在宿主里重新连接腾讯文档；②主程序重启后旧端口失效。"
        % (", ".join(tried) or "无候选", tok_reason))


def _post(url, headers, payload, timeout=120):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = _u.Request(url, data=body, method="POST")
    for k, v in headers.items():
        req.add_header(k, v)
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json, text/event-stream")
    # 本机系统代理常返回 502（尤其专享版域名），公网端点先直连、失败再退回系统代理
    try:
        with _no_proxy_opener().open(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", "replace")
    except Exception:
        with _u.urlopen(req, timeout=timeout) as resp:
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
