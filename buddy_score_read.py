# -*- coding: utf-8 -*-
"""Buddy 积分后台读取（零干扰版）。

用途：不移动真实鼠标、不抢焦点、不置前窗口，后台读取 WorkBuddy 头像菜单里的积分余额。

原理：
  1. 按进程名定位 WorkBuddy 主窗口（Electron）
  2. PrintWindow(PW_RENDERFULLCONTENT) 抓基线帧（对非前台窗口有效，不需要 SetForegroundWindow）
  3. PostMessage 后台合成点击「头像」→ 头像菜单弹出（积分余额直接显示在菜单里）
  4. 再抓一帧菜单截图 → PostMessage 点空白处关闭菜单
  5. 输出 JSON 给调用方（自动化会话用视觉读图取数字）

用法（Python311，需 pywin32）：
  python buddy_score_read.py --outdir C:\\Users\\huaxi\\WorkBuddy\\Claw\\data
输出（stdout，单行 JSON）：
  {"ok":true,"hwnd":...,"menu_png":"...","baseline_png":"..."}
  {"ok":false,"code":"SKIP_MINIMIZED"}        窗口最小化（PrintWindow 会截到空帧，不强制恢复以免打扰）
  {"ok":false,"code":"WINDOW_NOT_FOUND"}      找不到主窗口
  {"ok":false,"code":"CAPTURE_FAILED"}        截图失败

坐标按窗口尺寸比例换算（基准 1024x728 的布局）：
  头像 ≈ (50, 695)/1024x728；空白关闭点 ≈ (700, 300)/1024x728
"""
import sys, os, json, time, ctypes, argparse

import win32gui, win32process, win32con

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

PW_RENDERFULLCONTENT = 0x2
BASE_W, BASE_H = 1024.0, 728.0
AVATAR = (50 / BASE_W, 695 / BASE_H)     # 左下角头像
BLANK = (700 / BASE_W, 300 / BASE_H)     # 空白处（用于关闭菜单）


def set_dpi_aware():
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            user32.SetProcessDPIAware()
        except Exception:
            pass


def find_main_window():
    """按进程名 WorkBuddy.exe 找可见、有尺寸的顶层窗口。"""
    hits = []

    def cb(h, _):
        if not win32gui.IsWindowVisible(h):
            return True
        # 排除普通弹窗类（无标题的小工具窗）
        if not win32gui.GetWindowText(h):
            return True
        try:
            _, pid = win32process.GetWindowThreadProcessId(h)
            import win32api
            ph = win32api.OpenProcess(0x0400 | 0x0010, False, pid)  # QUERY_INFO|VM_READ
            exe = win32process.GetModuleFileNameEx(ph, 0)
            win32api.CloseHandle(ph)
        except Exception:
            return True
        name = os.path.basename(exe).lower()
        if name == 'workbuddy.exe':
            l, t, r, b = win32gui.GetWindowRect(h)
            if (r - l) > 400 and (b - t) > 300:  # 主窗口尺寸
                hits.append((h, r - l, b - t))
        return True

    win32gui.EnumWindows(cb, None)
    if not hits:
        return None
    # 取最大的那个作为主窗口
    hits.sort(key=lambda x: -(x[1] * x[2]))
    return hits[0][0]


def capture(hwnd, path):
    """PrintWindow 抓帧，不恢复、不置前。"""
    class RECT(ctypes.Structure):
        _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                    ("right", ctypes.c_long), ("bottom", ctypes.c_long)]
    rc = RECT()
    if not user32.GetWindowRect(hwnd, ctypes.byref(rc)):
        return None
    w, h = rc.right - rc.left, rc.bottom - rc.top
    if w <= 0 or h <= 0:
        return None
    hdc = user32.GetWindowDC(hwnd)
    mem = gdi32.CreateCompatibleDC(hdc)
    bmp = gdi32.CreateCompatibleBitmap(hdc, w, h)
    gdi32.SelectObject(mem, bmp)
    try:
        if not user32.PrintWindow(hwnd, mem, PW_RENDERFULLCONTENT):
            return None
        # BMP -> PNG（纯 Python zlib，无第三方图像库依赖）
        import struct, zlib
        data = ctypes.create_string_buffer(w * h * 4)
        gdi32.GetDIBits(mem, bmp, 0, h, data, None, 0) if False else None
        # 用 GetDIBits 需要 BITMAPINFO，改走简单路径：直接构造 24bpp DIB
        class BMIH(ctypes.Structure):
            _fields_ = [("biSize", ctypes.c_uint32), ("biWidth", ctypes.c_int32),
                        ("biHeight", ctypes.c_int32), ("biPlanes", ctypes.c_uint16),
                        ("biBitCount", ctypes.c_uint16), ("biCompression", ctypes.c_uint32),
                        ("biSizeImage", ctypes.c_uint32), ("biXPelsPerMeter", ctypes.c_int32),
                        ("biYPelsPerMeter", ctypes.c_int32), ("biClrUsed", ctypes.c_uint32),
                        ("biClrImportant", ctypes.c_uint32)]
        bi = BMIH(ctypes.sizeof(BMIH), w, -h, 1, 32, 0, 0, 0, 0, 0, 0)
        buf = ctypes.create_string_buffer(w * h * 4)
        if not gdi32.GetDIBits(mem, bmp, 0, h, buf, ctypes.byref(bi), 0):
            return None
        raw = buf.raw  # BGRA, top-down
        rows = []
        for y in range(h):
            row = bytearray()
            base = y * w * 4
            for x in range(w):
                b_, g_, r_ = raw[base + x * 4], raw[base + x * 4 + 1], raw[base + x * 4 + 2]
                row += bytes((r_, g_, b_))
            rows.append(b'\x00' + bytes(row))  # filter type 0
        def chunk(tag, payload):
            c = struct.pack('>I', len(payload)) + tag + payload
            return c + struct.pack('>I', zlib.crc32(tag + payload) & 0xFFFFFFFF)
        ihdr = struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)
        png = (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr)
               + chunk(b'IDAT', zlib.compress(b''.join(rows), 6)) + chunk(b'IEND', b''))
        with open(path, 'wb') as f:
            f.write(png)
        return path
    finally:
        gdi32.DeleteObject(bmp)
        gdi32.DeleteDC(mem)
        user32.ReleaseDC(hwnd, hdc)


def bg_click(hwnd, fx, fy):
    l, t, r, b = win32gui.GetWindowRect(hwnd)
    w, h = r - l, b - t
    x = max(1, min(w - 2, int(fx * w)))
    y = max(1, min(h - 2, int(fy * h)))
    lp = (y << 16) | (x & 0xFFFF)
    user32.PostMessageW(hwnd, win32con.WM_MOUSEMOVE, 0, lp)
    time.sleep(0.05)
    user32.PostMessageW(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lp)
    time.sleep(0.08)
    user32.PostMessageW(hwnd, win32con.WM_LBUTTONUP, 0, lp)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--outdir', default=os.path.dirname(os.path.abspath(__file__)))
    a = ap.parse_args()
    set_dpi_aware()
    os.makedirs(a.outdir, exist_ok=True)
    ts = time.strftime('%Y%m%d_%H%M%S')

    hwnd = find_main_window()
    if not hwnd:
        print(json.dumps({"ok": False, "code": "WINDOW_NOT_FOUND"}))
        return
    if win32gui.IsIconic(hwnd):
        print(json.dumps({"ok": False, "code": "SKIP_MINIMIZED"}))
        return

    base_png = os.path.join(a.outdir, 'buddy_base_latest.png')   # 固定文件名，每日覆盖不堆积
    menu_png = os.path.join(a.outdir, 'buddy_menu_latest.png')
    if not capture(hwnd, base_png):
        print(json.dumps({"ok": False, "code": "CAPTURE_FAILED"}))
        return
    bg_click(hwnd, *AVATAR)
    time.sleep(4.0)   # 积分余额异步加载，实测 1.6s 时显示"获取中"，4s 较稳
    ok = capture(hwnd, menu_png)
    bg_click(hwnd, *BLANK)          # 关闭菜单，不留残影
    time.sleep(0.3)
    if not ok:
        print(json.dumps({"ok": False, "code": "CAPTURE_FAILED"}))
        return
    print(json.dumps({"ok": True, "hwnd": hwnd, "menu_png": menu_png, "baseline_png": base_png}, ensure_ascii=False))


if __name__ == '__main__':
    main()
