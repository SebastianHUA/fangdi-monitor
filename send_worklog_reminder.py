# -*- coding: utf-8 -*-
"""通过微信向主人(梦比鱿鱼丝)发送工作日志提醒"""
import subprocess
import sys

PY311 = r"C:\Users\huaxi\AppData\Local\Programs\Python\Python311\python.exe"
SENDER = r"C:\Users\huaxi\.workbuddy\skills\arcwechat\scripts\wechat_sender.py"
CONTACT = "梦比鱿鱼丝"

MESSAGE = """📝 工作日志提醒

今天是8月31日，快记录一下今天做了什么吧～

直接回复我："记录工作：XXX"，我会帮你自动添加到工作日志。

📋 工作日志链接：
https://docs.qq.com/smartsheet/DTkZDSWpxbWVUa1NN"""


def main():
    print("=" * 50)
    print(f"发送给: {CONTACT}")
    print("-" * 50)
    print(MESSAGE)
    print("=" * 50)

    result = subprocess.run(
        [PY311, SENDER, CONTACT, MESSAGE],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    print("\n--- stdout ---")
    print(result.stdout)
    if result.stderr:
        print("--- stderr ---")
        print(result.stderr)
    print("--- returncode ---")
    print(result.returncode)

    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
