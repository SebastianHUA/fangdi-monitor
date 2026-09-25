# 上海土地市场每日监控（主任务 17:00）

配套公共铁律：`C:\Users\huaxi\WorkBuddy\Claw\task_rules\common.md`（必读）

## 🚨 零号铁律：必须真的动手

2026-09-23、09-24 连续两天本任务出现"假成功"：宿主记录 success=true，但会话日志显示
**全程零工具调用、28 秒后 end_turn**，CSV 根本没更新，最后由 17:25 看门狗补跑。

因此：**收到本任务后，第一轮就必须调用 Bash 执行下面的步骤 1 抓取命令。
不允许先输出计划/说明文字再结束。一轮内没执行任何工具 = 本任务失败。**

## 步骤 1：抓取（约 1-2 分钟）

```
C:\Users\huaxi\AppData\Local\Programs\Python\Python311\python.exe "C:\Users\huaxi\.workbuddy\skills\shanghai-land-monitor\scripts\land_monitor_curl.py" 3
```

结果写入 `C:\Users\huaxi\WorkBuddy\Claw\land_monitor_results.csv`。确认抓到条数与最新发布日期。

## 步骤 2：生成 XLSX（仅本地留存，不发微信）

```
python311 C:\Users\huaxi\WorkBuddy\Claw\gen_land_xlsx.py
```

## 步骤 3：同步腾讯文档

```
python311 C:\Users\huaxi\WorkBuddy\Claw\land_tdoc_sync.py --dry-run
python311 C:\Users\huaxi\WorkBuddy\Claw\land_tdoc_sync.py
```

去重键 = 发布日期 + 公告类型 + 地块公告号 + 地块名称，重复执行不会写坏。
目标 file_id `NHsPBsupJrkx` / sheet `000001`，数据表 https://docs.qq.com/sheet/DTkhzUEJzdXBKcmt4

## 步骤 4：台账判定要不要推送

```
python311 C:\Users\huaxi\WorkBuddy\Claw\land_pending_push.py
```

维护 `data\land_pushed_keys.txt` 已推送台账：待推送 = CSV 中涉宅公告 − 台账已有键。
断档、人工补跑、上次推送失败积压的涉宅公告都会被推到，且绝不重复推送。

- `PENDING_COUNT 0` → 步骤 5B（无涉宅，只发梦比鱿鱼丝）
- `PENDING_COUNT N>0` → 步骤 5A（完整简报发三人）；含早于今天的日期则标题加「（含补报）」并逐条标注发布日期

## 步骤 5A：有涉宅 → 完整简报发三人（梦比鱿鱼丝 / 沈胄磊 / 周凯琦）

```
【上海土地市场日报】（有补报时加"（含补报）"）

YYYY年MM月DD日

本次公告 X 条（涉宅 Y 条）

【住宅/居住用地】
1. **地块名称**（发布日期 MM-DD，容积率 x.x）
   - 竞得人：xxx

【其他用地】
1. **地块名称**（发布日期 MM-DD）
   - 土地用途：xxx

官网链接：https://biz.ghzyj.sh.gov.cn/shtdsc/wz/
数据表链接：https://docs.qq.com/sheet/DTkhzUEJzdXBKcmt4

---
【来自梦小喵🐱】
```

## 步骤 5B：无涉宅 → 简短提示只发梦比鱿鱼丝一人

主人 2026-09-24 明确要求：**每天都要有交代，不能石沉大海**；但无涉宅时**严禁发给沈胄磊、周凯琦**。

```
【上海土地市场】今日无涉宅公告

YYYY年MM月DD日 17:00
本次抓取 N 条公告，最新发布日期 MM-DD，其中无住宅/居住/商品房用地。

数据表链接：https://docs.qq.com/sheet/DTkhzUEJzdXBKcmt4

---
【来自梦小喵🐱】
```

## 步骤 6：核验 + 写台账

1. 至少对梦比鱿鱼丝这一次截屏核验（见 common.md 第 2 条）。
2. **仅当走了 5A 且确认送达后**执行：`python311 ...\land_pending_push.py --mark`
3. 发送失败 → 不 mark，留作下次待推送。
