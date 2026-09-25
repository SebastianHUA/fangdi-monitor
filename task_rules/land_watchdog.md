# 上海土地监测 健康看门狗（17:25）

配套公共铁律：`C:\Users\huaxi\WorkBuddy\Claw\task_rules\common.md`（必读）

## 定位

检查 17:00 主任务是否有产出，没有就自动补跑。**已连续两天救场成功**（9/23、9/24 主任务均"假成功"未干活）。

## 🚨 零号铁律：必须真的动手

主任务曾出现"零工具调用、28 秒 end_turn"的假成功。本任务同样：**第一轮就必须调用 Bash**（第 1 步判定脚本），不允许只输出计划。

## 🚨 铁律一：A 类静默（防重复打扰）

主任务 17:00 已给梦比鱿鱼丝发过交代了，所以 **A 类一律静默**：只追加一行本地日志，严禁发任何微信
（包括"✅ 正常运行"——曾因天天发确认消息导致主人每天收到两条，此规则不得回退）。

**唯一例外**：台账 `PENDING_COUNT > 0`（有积压未推送的涉宅公告）→ 必须补推（9/21 三宗就是这么漏的）。

## 🚨 铁律二：B 类补跑后必须给梦比鱿鱼丝交代

主任务没跑 = 没人发过消息，所以补跑后**必须**发（见第 4 步）。

## 第 1 步：判定 A / B

```
C:\Users\huaxi\AppData\Local\Programs\Python\Python311\python.exe - <<'PY'
import os, datetime
TZ = datetime.timezone(datetime.timedelta(hours=8))
now = datetime.datetime.now(TZ)
csv = r'C:\Users\huaxi\WorkBuddy\Claw\land_monitor_results.csv'
mt = datetime.datetime.fromtimestamp(os.path.getmtime(csv), TZ)
cutoff = now.replace(hour=17, minute=0, second=0, microsecond=0)
print('NOW', now.strftime('%Y-%m-%d %H:%M:%S'))
print('CSV_MTIME', mt.strftime('%Y-%m-%d %H:%M:%S'))
print('STATUS', 'A' if (mt.date() == now.date() and mt >= cutoff) else 'B')
PY
```

## 第 2 步：A 类处理

追加日志：`<日期> 17:25 | A-OK | 主任务已产出(CSV mtime=<时间>)，静默`

1. `python311 land_tdoc_sync.py --dry-run`；待补录 >0 则实跑（**不推微信**），记 `A-SYNC-FIX | 已补录 N 条`
2. 台账判定 `land_pending_push.py`：
   - `PENDING_COUNT 0` → 静默结束
   - `>0` → 补推（记 `A-BACKLOG`），走第 4 步**分支一**

## 第 3 步：B 类处理（补跑）

先查 `data\land_watchdog_run.log` 是否已有今天的 `B-RESCUE` 行：有 → 结束（防重复）。

1. 抓取：`python311 "C:\Users\huaxi\.workbuddy\skills\shanghai-land-monitor\scripts\land_monitor_curl.py" 3`
   失败 → 等 60 秒重试一次；仍失败 → 第 5 步告警
2. `python311 C:\Users\huaxi\WorkBuddy\Claw\gen_land_xlsx.py`
3. `land_tdoc_sync.py --dry-run` → 实跑
4. 台账判定 → 第 4 步
5. 追加日志：`B-RESCUE | ... | 抓取N条/补录K条/待推送M条/推送<三人|梦比鱿鱼丝一人>`

## 第 4 步：推送

🚨 判定依据是**台账输出**，不是"今天有没有新公告"。正文一律 `--file` 发 UTF-8。

**分支一（PENDING_COUNT > 0）→ 完整简报发三人**，标题加「（含补报）」，格式同 `land_main.md` 步骤 5A，
并在末尾注明"17:25 看门狗补跑"。发完核验，确认送达才 `--mark`。

**分支二（PENDING_COUNT = 0）→ 简短提示只发梦比鱿鱼丝一人**（严禁发给沈胄磊、周凯琦）：

```
【上海土地市场】今日无涉宅公告（17:25 看门狗补跑）

YYYY年MM月DD日
本次抓取 N 条公告，最新发布日期 MM-DD，其中无住宅/居住/商品房用地。
注：17:00 主任务未产出，已由看门狗自动补跑。

数据表链接：https://docs.qq.com/sheet/DTkhzUEJzdXBKcmt4

---
【来自梦小喵🐱】
```

此分支**不执行 --mark**。

## 第 5 步：告警（救不了时）

补跑两次都失败 → 只给**梦比鱿鱼丝**发一条：

```
⚠️ 上海土地监测异常
17:00 主任务未产出，17:25 看门狗补跑失败：<原因>
数据尚未更新到 <最新发布日期>。
人工处理：cd C:\Users\huaxi\WorkBuddy\Claw 后跑
python311 "C:\Users\huaxi\.workbuddy\skills\shanghai-land-monitor\scripts\land_monitor_curl.py" 3
```

并追加日志 `C-ALERT`。

## 说明

土地同步脚本全量比对 + 幂等去重，连续几天没跑也不丢数据，最多晚一天。不用惊慌，也别跳过检查。
