# -*- coding: utf-8 -*-
"""Buddy 加油站 —— 每日通用积分自动领取（零干扰，无需看图）。

背景：
  API 路线已封死（新版客户端 auth.accessToken 加密，MCP token/内部票据端点均不可用），
  截图路线又依赖视觉模型，因此改走 Windows UI Automation 读控件树——**按 Name 判断按钮状态**，
  不需要看懂图片，也不需要堆截图壮志 Energie。

原理：
  1. 按进程名定位 WorkBuddy 主窗口
  2. 确保「Buddy 加油站」面板已打开（未打开则后台点击头像 → 菜单里找加油站入口）
  3. 在面板内找底部按钮组里的「领取 / 今日已领」按钮：
     - Name 含「今日已领」「已领取」→ 今天已领，跳过
     - Name 含「领取」→ 用 UIA Invoke 后台点击，再回读确认状态变化
  4. 输出单行 JSON

依赖（已装在隔离目录，不污染宿主 Python 环境）：
  Python311 + pywin32 + uiautomation/comtypes
  uiautomation 装在 C:\\Users\\huaxi\\.workbuddy\\binaries\\python\\pkgs311

用法：
  python buddy_claim.py            # 检测 + 领取（默认）
  python buddy_claim.py --scan     # 只检测不点击（安全预演）
输出：
  {"ok":true,"code":"CLAIM_OK","button_before":"领取","button_after":"今日已领"}
  {"ok":true,"code":"ALREADY_CLAIMED","button":"今日已领"}
  {"ok":true,"code":"NO_PANEL"}                 面板没打开且打不开
  {"ok":false,"code":"WINDOW_NOT_FOUND"}
  {"ok":false,"code":"SKIP_MINIMIZED"}
"""
import sys
import os
import json
import time
import argparse
import ctypes

# uiautomation 装在隔离目录（不污染系统 Python）
PKGS = r"C:\Users\huaxi\.workbuddy\binaries\python\pkgs311"
if PKGS not in sys.path:
    sys.path.insert(0, PKGS)

import win32gui
import win32process
import win32api
import win32con

try:
    import uiautomation as auto
except Exception as e:  # pragma: no cover
    print(json.dumps({"ok": False, "code": "UIA_IMPORT_FAIL", "msg": str(e)}, ensure_ascii=False))
    sys.exit(2)

CLOSE_BTN = "关闭 Buddy 加油站"
PANEL_MARK = "Buddy加油站"
OPEN_KEYS = ("Buddy 加油站", "Buddy加油站")
CLAIMED_KEYS = ("今日已领", "已领取", "今日已领取")
CLAIM_KEYS = ("领取",)

BASE_W, BASE_H = 1024.0, 728.0
AVATAR = (50 / BASE_W, 695 / BASE_H)  # 左下角头像（与 buddy_score_read.py 保持一致）


def out(obj):
    print(json.dumps(obj, ensure_ascii=False))
    sys.stdout.flush()


def find_main_window():
    hits = []

    def cb(h, _):
        if not win32gui.IsWindowVisible(h):
            return True
        if not win32gui.GetWindowText(h):
            return True
        try:
            _, pid = win32process.GetWindowThreadProcessId(h)
            ph = win32api.OpenProcess(0x0400 | 0x0010, False, pid)
            exe = win32process.GetModuleFileNameEx(ph, 0)
        except Exception:
            return True
        if exe.lower().endswith("workbuddy.exe"):
            l, t, r, b = win32gui.GetWindowRect(h)
            hits.append((h, max(0, r - l) * max(0, b - t)))
        return True

    win32gui.EnumWindows(cb, None)
    return max(hits, key=lambda x: x[1])[0] if hits else None


def bg_click(hwnd, fx, fy):
    """后台合成点击（不移动真实鼠标、不抢焦点）。"""
    l, t, r, b = win32gui.GetWindowRect(hwnd)
    w, h = r - l, b - t
    if w <= 0 or h <= 0:
        return False
    x = int(l + fx * w)
    y = int(t + fy * h)
    lp = (y << 16) | (x & 0xFFFF)
    try:
        win32gui.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, 0, lp)
        time.sleep(0.08)
        win32gui.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, lp)
        return True
    except Exception:
        return False


def walk(ctl, max_depth=16, max_nodes=6000):
    n = 0
    for c, d in auto.WalkControl(ctl, maxDepth=max_depth):
        n += 1
        if n > max_nodes:
            return
        yield c, d


def name_of(c):
    try:
        return c.Name or ""
    except Exception:
        return ""


def find_panel(ctl):
    """加油站面板容器：由「关闭 Buddy 加油站」按钮往上找到宽度>200 的祖先。"""
    target = None
    for c, _d in walk(ctl):
        if name_of(c) == CLOSE_BTN:
            target = c
            break
    if target is None:
        return None
    root = target
    for _ in range(8):
        try:
            p = root.GetParentControl()
        except Exception:
            break
        if p is None:
            break
        root = p
        try:
            rc = root.BoundingRectangle
            if (rc.right - rc.left) > 200:
                return root
        except Exception:
            pass
    return target


def ensure_panel(ctl, hwnd):
    """面板没开就后台点点头像 → 菜单里找加油站入口。返回 (panel, note)"""
    panel = find_panel(ctl)
    if panel is not None:
        return panel, "already_open"
    # 1) 点击头像打开菜单
    bg_click(hwnd, *AVATAR)
    time.sleep(1.2)
    # 2) 在菜单里找入口
    clicked = False
    for c, _d in walk(ctl, max_depth=10):
        nm = name_of(c)
        if nm and any(k in nm for k in OPEN_KEYS):
            clicked = uia_invoke(c) or do_invoke_fallback(c, hwnd)
            if clicked:
                break
    if not clicked:
        return None, "open_failed"
    time.sleep(2.0)
    return find_panel(ctl), "opened"


def find_claim_button(panel):
    """面板内的领取按钮 + 累计领取数值。"""
    btn = None
    total_txt = None
    for c, _d in walk(panel, max_depth=8, max_nodes=800):
        nm = name_of(c)
        try:
            ct = c.ControlTypeName
        except Exception:
            ct = ""
        if ct != "ButtonControl":
            continue
        if nm and any(k in nm for k in CLAIMED_KEYS):
            return c, "claimed", total_txt
        if nm and any(k in nm for k in CLAIM_KEYS):
            if btn is None:
                btn = c
    # 顺带读「累计领取」后面的数字
    try:
        for c, _d in walk(panel, max_depth=8, max_nodes=800):
            nm = name_of(c)
            if nm and nm.isdigit() and total_txt is None:
                total_txt = nm
            if nm == "分" and total_txt:
                break
    except Exception:
        pass
    return (btn, "claimable" if btn else "not_found", total_txt)


def uia_invoke(c):
    """后台触发控件（不移动鼠标、不抢焦点）。

    uiautomation 2.x 里 Control 没有 .Invoke()，要走 GetInvokePattern()。
    不支持 InvokePattern 时返回 False，由调用方回退到坐标点击。
    """
    try:
        pat = c.GetInvokePattern()
        if pat is not None:
            pat.Invoke()
            return True
    except Exception:
        pass
    return False


def click_control(c, hwnd):
    """优先 UIA Invoke，失败回退到后台坐标点击。"""
    if uia_invoke(c):
        return True
    return do_invoke_fallback(c, hwnd)


def do_invoke_fallback(btn, hwnd):
    try:
        rc = btn.BoundingRectangle
        l, t, r, b = win32gui.GetWindowRect(hwnd)
        w, hh = r - l, b - t
        if w > 0 and hh > 0:
            fx = (rc.left + rc.right) / 2.0 / w
            fy = (rc.top + rc.bottom) / 2.0 / hh
            return bg_click(hwnd, fx, fy)
    except Exception:
        pass
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scan", action="store_true", help="只检测不点击")
    ap.add_argument("--timeout", type=float, default=12.0, help="等待面板超时秒数")
    args = ap.parse_args()

    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

    hwnd = find_main_window()
    if not hwnd:
        out({"ok": False, "code": "WINDOW_NOT_FOUND"})
        return
    try:
        if win32gui.IsIconic(hwnd):
            out({"ok": False, "code": "SKIP_MINIMIZED"})
            return
    except Exception:
        pass

    try:
        ctl = auto.ControlFromHandle(hwnd)
    except Exception as e:
        out({"ok": False, "code": "CONTROL_FAIL", "msg": str(e)[:120]})
        return

    panel, note = ensure_panel(ctl, hwnd)
    if panel is None:
        out({"ok": True, "code": "NO_PANEL", "note": note})
        return

    btn, state, total = find_claim_button(panel)
    info = {"panel_note": note, "button": name_of(btn) if btn else None, "total": total}

    if state == "claimed":
        info.update({"ok": True, "code": "ALREADY_CLAIMED"})
        out(info)
        return
    if state == "not_found":
        info.update({"ok": True, "code": "BUTTON_NOT_FOUND"})
        out(info)
        return

    info["button_before"] = name_of(btn)
    if args.scan:
        info.update({"ok": True, "code": "SCAN_CLAIMABLE", "action": "none(--scan)"})
        out(info)
        return

    ok_click = click_control(btn, hwnd)
    time.sleep(2.5)
    panel2 = find_panel(ctl) or panel
    btn2, state2, total2 = find_claim_button(panel2)
    name2 = name_of(btn2) if btn2 else None
    info.update({
        "ok": True,
        "click_sent": ok_click,
        "button_after": name2,
        "state_after": state2,
        "total_after": total2,
        "code": "CLAIM_OK" if (state2 == "claimed" or (name2 and name2 != info["button_before"])) else "CLAIM_UNVERIFIED",
    })
    out(info)


if __name__ == "__main__":
    main()
