# -*- coding: utf-8 -*-
import sys
import time
import pyperclip
import win32gui
import win32con
import win32api

CONTACT = sys.argv[1] if len(sys.argv) > 1 else "文件传输助手"
MESSAGE = sys.argv[2] if len(sys.argv) > 2 else ""

WECHAT_CLASS = "WeChatMainWndForPC"


def find_wechat_window():
    """按类名查找微信主窗口"""
    hwnd = win32gui.FindWindow(WECHAT_CLASS, None)
    if hwnd:
        return hwnd
    # 兜底：枚举顶层窗口找标题含"微信"的
    result = []
    def enum_cb(hwnd, extra):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            cls = win32gui.GetClassName(hwnd)
            if "微信" in title or cls == WECHAT_CLASS:
                extra.append(hwnd)
    win32gui.EnumWindows(enum_cb, result)
    return result[0] if result else None


def send_keys(hwnd, keys):
    """向窗口发送按键序列，支持修饰键组合，如 ^f 表示 Ctrl+F"""
    win32gui.SetForegroundWindow(hwnd)
    time.sleep(0.3)
    for key in keys:
        if key.startswith("^"):
            # 组合键
            main_key = key[1:].upper()
            vk = getattr(win32con, "VK_" + main_key, ord(main_key))
            win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
            win32api.keybd_event(vk, 0, 0, 0)
            win32api.keybd_event(vk, 0, win32con.KEYEVENTF_KEYUP, 0)
            win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
        elif key == "Enter":
            win32api.keybd_event(win32con.VK_RETURN, 0, 0, 0)
            win32api.keybd_event(win32con.VK_RETURN, 0, win32con.KEYEVENTF_KEYUP, 0)
        elif key == "Escape":
            win32api.keybd_event(win32con.VK_ESCAPE, 0, 0, 0)
            win32api.keybd_event(win32con.VK_ESCAPE, 0, win32con.KEYEVENTF_KEYUP, 0)
        else:
            # 单个字符
            for ch in key:
                vk = win32api.VkKeyScan(ch)
                if vk == -1:
                    # 无法直接输入的字符（如中文）跳过，这里用剪贴板粘贴
                    continue
                win32api.keybd_event(vk & 0xFF, 0, 0, 0)
                win32api.keybd_event(vk & 0xFF, 0, win32con.KEYEVENTF_KEYUP, 0)
        time.sleep(0.2)


def paste_text(text):
    pyperclip.copy(text)
    time.sleep(0.2)
    win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
    win32api.keybd_event(ord("V"), 0, 0, 0)
    win32api.keybd_event(ord("V"), 0, win32con.KEYEVENTF_KEYUP, 0)
    win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
    time.sleep(0.3)


def main():
    print(f"[微信发送] 联系人: {CONTACT}")
    hwnd = find_wechat_window()
    if not hwnd:
        print("❌ 未找到微信窗口，请确认微信 PC 客户端已登录")
        sys.exit(1)
    print(f"✅ 找到微信窗口: hwnd={hwnd}")

    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    win32gui.SetForegroundWindow(hwnd)
    time.sleep(0.5)

    # 打开搜索框 Ctrl+F
    send_keys(hwnd, ["^f"])
    time.sleep(0.5)
    paste_text(CONTACT)
    time.sleep(1.0)
    send_keys(hwnd, ["Enter"])
    time.sleep(1.5)

    # 粘贴消息并发送
    paste_text(MESSAGE)
    time.sleep(0.5)
    send_keys(hwnd, ["Enter"])
    time.sleep(0.5)

    print("✅ 消息已发送")


if __name__ == "__main__":
    main()
