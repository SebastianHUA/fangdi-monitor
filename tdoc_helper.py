# -*- coding: utf-8 -*-
"""腾讯文档 smartsheet 调用封装（兼容垫片）。

🚨 2026-09-04 改造：旧实现依赖 `mcporter.cmd`，该命令在本机**早已不存在**，
导致所有走本模块的脚本静默失败（自动化任务表现为「腾讯文档同步失败 no_token」）。

现在改为**优先走 tdoc_mcp.py**（从环境变量 CODEBUDDY_MCP_CONFIG 取 MCP url + Bearer，
HTTP JSON-RPC 直连，实测可用）；仅当 tdoc_mcp 不可用时才回退旧逻辑。

对外接口（call / ok）签名完全不变，历史脚本无需改动即可恢复工作。

用法：
    from tdoc_helper import call, ok
    r = call('smartsheet.list_records', {'file_id': 'xxx', 'sheet_id': 'yyy'})

判成败务必解析 JSON 的 error 字段，不要用字符串包含 "error"：
响应恒含 "error": "" ，字符串判断会误判失败并导致重复写入。
"""

import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from tdoc_mcp import call as _mcp_call, ok as _mcp_ok  # noqa: E402
    _USE_MCP = True
except Exception:  # pragma: no cover
    _USE_MCP = False


def _legacy_call(tool, args):
    """旧的 mcporter 调用路径（已废弃，仅作兜底保留）。"""
    proc = subprocess.run(
        [
            'mcporter.cmd', 'call', 'tencent-docs', tool,
            '--args', json.dumps(args, ensure_ascii=False),
        ],
        capture_output=True,
        text=True,
        encoding='utf-8',
        shell=False,
    )
    out = (proc.stdout or '') + (proc.stderr or '')
    start = out.find('{')
    if start == -1:
        return out.strip()
    depth = 0
    for i, ch in enumerate(out[start:], start):
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(out[start:i + 1])
                except json.JSONDecodeError:
                    return out.strip()
    return out.strip()


def call(tool, args):
    """调用腾讯文档 MCP 工具，返回解析后的 dict（失败时返回含 error 的 dict）。"""
    if _USE_MCP:
        return _mcp_call(tool, args)
    return _legacy_call(tool, args)


def ok(resp):
    """解析响应是否成功：error 字段为空即成功。"""
    if isinstance(resp, dict):
        return not resp.get('error')
    return False


if __name__ == '__main__':
    print('通道:', 'tdoc_mcp (直连)' if _USE_MCP else 'mcporter (已废弃)')
    r = call('smartsheet.list_records',
             {'file_id': 'DTnNsSXVoc21TbkhF', 'sheet_id': '0g5JQL', 'page_size': 1})
    print('探测结果:', 'OK' if ok(r) else 'FAIL %s' % str(r)[:200])
