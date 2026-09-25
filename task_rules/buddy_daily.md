# Buddy 每日任务规则（07:20）

适用自动化：`Buddy积分每日播报（07:20）` id `ce238189-c565-4a13-a728-95f4b995ea4c`

包含两个动作：**① 先领通用积分 → ② 再读余额并播报**。领取必须在读取之前，
这样播报出来的余额才是"领完之后"的最新数字。

---

## 铁律

- 🚨 **日期一律用 Bash `date "+%Y-%m-%d"` 获取**，禁止凭记忆或 PowerShell 表达式猜测。
- 🚨 **Python 一律用 Python311 绝对路径**：
  `C:\Users\huaxi\AppData\Local\Programs\Python\Python311\python.exe`
  （需要 pywin32；托管版 3.13 没有）
- 🚨 **严禁调用 `mcp__tencent-docs__*` 内置工具**（本会话不可用）。
- 🚨 脚本输出较长时用 `tail -30`，**禁止 `| head`**（SIGPIPE 会误报失败）。
- 🚨 严禁自行写 GUI 点击逻辑（SetCursorPos / mouse_event / SetForegroundWindow / ShowWindow / SendInput），
  所有窗口操作必须走已固化的脚本。
- 🚨 **微信中文正文必须写 UTF-8 临时文件后用 `--file` 发送**，严禁把正文当命令行参数。

## 依赖说明（重要）

`buddy_claim.py` 依赖 `uiautomation / comtypes`，已装在**隔离目录**（不污染系统 Python）：

```
C:\Users\huaxi\.workbuddy\binaries\python\pkgs311
```

脚本内部已自动 `sys.path.insert`，无需手动设置 PYTHONPATH。
若报 `UIA_IMPORT_FAIL`，说明该目录缺失 → **不要自己 pip 安装**，直接按步骤 0 的降级处理走，并在回复里说明。

---

## 步骤 0：领取每日通用积分

```
python311 C:\Users\huaxi\WorkBuddy\Claw\buddy_claim.py
```

输出单行 JSON，按 `code` 分支处理：

| code | 含义 | 处理 |
|---|---|---|
| `CLAIM_OK` | 领取成功 | 正常继续，播报里注明"已自动领取" |
| `ALREADY_CLAIMED` | 今天已领过（主人可能手工领了） | 正常继续，不加额外说明 |
| `NO_PANEL` | 加油站面板没打开且打不开 | **等 5 秒重试一次**；仍失败 → 视为"未自动领取"，在播报末尾追加提示 |
| `BUTTON_NOT_FOUND` | 面板打开了但没找到领取按钮 | 同上，重试一次后仍失败则提示 |
| `CLAIM_UNVERIFIED` | 点了但状态没变化 | 播报里注明"领取结果待确认" |
| `WINDOW_NOT_FOUND` / `SKIP_MINIMIZED` | WorkBuddy 没运行或窗口最小化 | **静默**，不打扰主人（属正常情况） |
| `UIA_IMPORT_FAIL` | 依赖缺失 | 播报里注明"自动领取组件缺失" |

> ⚠️ 只有上面明确列出"静默"的情况才静默。其他异常都要在播报里让主人知道 —— 他要的是"别漏领"。

## 步骤 1：读取积分余额

```
python311 C:\Users\huaxi\WorkBuddy\Claw\buddy_score_read.py --outdir C:\Users\huaxi\WorkBuddy\Claw\data
```

约 8 秒（含等待积分异步加载）。stdout 是单行 JSON。

- `ok=false` 且 code 为 `SKIP_MINIMIZED` / `WINDOW_NOT_FOUND` / `CAPTURE_FAILED`
  → 追加一行到 `C:\Users\huaxi\WorkBuddy\Claw\data\buddy_score_run.log`（`<日期> | <code> | 静默跳过`），
  **静默结束**，不发微信。连续 3 天失败才给梦比鱿鱼丝发一条简短告警（读 log 尾部判断）。
- `ok=true` → 截图在 `C:\Users\huaxi\WorkBuddy\Claw\data\buddy_menu_latest.png`，继续步骤 2。

## 步骤 2：视觉读数

用视觉（Read 图片）读取 `buddy_menu_latest.png`：左侧弹出菜单中「积分余额」那一行的数字
（形如 520.87，可能带旋转刷新图标）。

- 若显示"获取中"或读不出数字 → 记日志 `<日期> | READ_FAIL | 静默`，不发微信，结束。
- ⚠️ 若当前模型不支持读图（返回不支持图片），不要硬猜数字 —— 记日志并跳过播报，
  但**步骤 0 的领取结果仍要用一句话告诉主人**（领取成功与否比余额数字更重要）。

## 步骤 3：写历史 CSV

追加到 `C:\Users\huaxi\WorkBuddy\Claw\data\buddy_score_history.csv`
（不存在则先写表头 `date,score`），再读出昨天的 score 用于对比。

## 步骤 4：微信播报（只发梦比鱿鱼丝一人）

正文写入 UTF-8 临时文件 `C:\Users\huaxi\WorkBuddy\Claw\data\tmp_buddy_msg.txt`：

```
🐱 Buddy积分 | 09-25 余额 267.66
```

- 若昨日对比下降超过 100 → 追加 `（较昨日 -X）`
- 若当天是 9/28 或 9/29 → 追加 `（ Buddy加油站9期活动最后一天/临近结束，别断签）`
- 步骤 0 领取成功 → 追加 `（今日通用积分已自动领取）`
- 步骤 0 失败且不应静默 → 追加 `（⚠️ 今日通用积分未能自动领取，请手工确认）`

发送：

```
python311 C:\Users\huaxi\.workbuddy\skills\arcwechat\scripts\wechat_sender.py "梦比鱿鱼丝" --file C:\Users\huaxi\WorkBuddy\Claw\data\tmp_buddy_msg.txt
```

失败等 30 秒重试一次；仍失败记日志 `<日期> | WECHAT_FAIL`。成功后删除临时文件。

## 步骤 5：核验（务必做）

🚨 **微信回显 DONE 不等于真送达**（2026-09-24 实测：Ctrl+F 被微信新版劫持成"搜一搜"，脚本照样回显 DONE 但消息没发出去）。
发送后必须：

```
python311 C:\Users\huaxi\WorkBuddy\Claw\screenshot_hwnd.py <微信HWND> C:\Users\huaxi\WorkBuddy\Claw\data\wechat_verify_buddy.png
```

（HWND 用 Python311 + `win32gui.EnumWindows` 找标题含"微信"的窗口）
用视觉 Read 确认消息真的出现；没送达就重发一次（修复后的脚本会先点击搜索框，约 178,57）。
若当前模型读不了图，**不要谎报成功**，在回复里说明"未做视觉核验"。

---

## 收尾

在回复里用一句话汇报：领取结果、余额、是否发微信、核验结论、有无异常。
