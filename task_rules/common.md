# 公共铁律（所有自动化任务通用）

> 本文件是自动化任务的**公共部分**，被各任务规则文件引用。
> 修改本文件即可同时影响所有任务，无需改动 automation prompt（prompt 是整块字段，改一个字也要全量重传，很贵）。

## 1. 环境与路径

- 工作目录：`C:\Users\huaxi\WorkBuddy\Claw`（自动化跑在独立工作区，脚本一律用绝对路径）
- **Python 必须用 Python311**：`C:\Users\huaxi\AppData\Local\Programs\Python\Python311\python.exe`
  （抓取依赖 bs4、微信/截屏依赖 pywin32，托管版 3.13 没有）
- 日期一律用 Bash 命令获取：`date "+%Y-%m-%d %H:%M:%S %z"`
  **禁止用 PowerShell 表达式，禁止凭记忆猜测**
- 脚本输出较长时**不要用 `| head` 截断**（会触发 SIGPIPE 误报失败），需要时用 `tail -40`

## 2. 微信发送

- 脚本：`C:\Users\huaxi\.workbuddy\skills\arcwechat\scripts\wechat_sender.py`
- 🚨 **编码铁律**：中文正文必须写入 UTF-8 临时文件后用 `--file` 发送，
  **严禁把中文/emoji 当命令行参数**（Windows 按 GBK 传参会整段乱码）。收件人作为参数正常。
- 🚨 **回显 DONE ≠ 真送达**（2026-09-24 实测：微信新版把 Ctrl+F 劫持成"搜一搜"，脚本照样回显 DONE 但没发出去）。
  发送后必须截屏核验：
  ```
  python311 C:\Users\huaxi\WorkBuddy\Claw\screenshot_hwnd.py <微信HWND> C:\Users\huaxi\WorkBuddy\Claw\data\wechat_verify.png
  ```
  HWND 用 Python311 + `win32gui.EnumWindows` 找标题含"微信"的窗口。
  然后视觉 Read 该图确认消息真的出现；没送达就重发一次（修复后的脚本会先点击搜索框，约 178,57）。

## 3. 腾讯文档

- 🚨 **绝不调用 `mcp__tencent-docs__*` 内置工具**：自动化跑在独立会话，该工具历史上返回 unavailable。
- 一律走脚本通道（内部用 `tdoc_mcp.py` 网关票据，已实测稳定）：
  - 土地：`C:\Users\huaxi\WorkBuddy\Claw\land_tdoc_sync.py`（先 `--dry-run` 再实跑，全量比对+幂等去重）
- 报 `TDOC_UNREACHABLE` → 不重试，记录"同步失败，数据已落本地"。

## 4. 收尾汇报

必须在**当前对话**输出一段结论（不要只写文件）：抓了多少条、判定结果、发给了谁、截屏核验结果。
