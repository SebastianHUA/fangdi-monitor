# LPR 利率查询（月度任务通用规则）

配套公共铁律：`C:\Users\huaxi\WorkBuddy\Claw\task_rules\common.md`（必读）

> 本文件是**模板**。具体日期由创建任务时填入，文中 `{PUB_DATE}` `{YEAR}` `{MONTH}` `{WEEKDAY}` 为占位符。
> 年度生成器（每年 1/1）创建 12 个月度任务时，prompt 只需写"按此规则执行，公布日期 = YYYY-MM-DD"。

## 🚨 零号铁律：必须真的动手

土地主任务出现过"零工具调用、28 秒 end_turn"的假成功。本任务同样：
**第一轮就必须调用工具**（访问央行页面或执行脚本），不允许只输出计划再结束。

## 步骤 1：查询 LPR

1. 访问央行 LPR 公告页：https://www.pbc.gov.cn/zhengcehuobisi/125207/125213/125440/3876551/index.html
2. 找到 `{PUB_DATE}` 公布的公告，记录：1 年期 LPR、5 年期以上 LPR、上次调整（无调整写"与上月持平"）
3. 🚨 记录**完整 URL**（以 `.../3876551/` 开头 + 数字编号 + `/index.html`），
   正确示例：`https://www.pbc.gov.cn/zhengcehuobisi/125207/125213/125440/3876551/2026052008080196671/index.html`
   **禁止**用 `[具体日期]` 占位符结尾

## 步骤 2：更新腾讯文档

1. "LPR查询日期计划-2026年v2"：file_id `NrSmgzndmVxy`，链接 https://docs.qq.com/doc/DTnJTbWd6bmRtVnh5
2. "梦比王国知识索引"记录本次结果
3. "LPR历史数据完整版"表格追加一行（file_id `DTkVQTWp0UFJqaEdv`，sheet_id `000001`）：
   - 先 `mcp__tencent-docs__sheet.get_cell_data` 读 A 列，检查 `{PUB_DATE}` 是否已存在
   - 不存在则 `insert_dimension`（row, index=1, count=1）+ `set_range_value`：
     A=发布日期 / B=1年期 / C=5年期以上 / D=公告链接 / E=更新时间(YYYY-MM-DD HH:mm:ss)
   - 不要改动其他行的"更新时间"

## 🚨 步骤 3：文档工具不可用时的降级（必做）

`mcp__tencent-docs__sheet.*` 在自动化独立会话中可能 unavailable —— 最多重试 1 次，仍失败立即降级：

1. 结果落盘 `C:\Users\huaxi\WorkBuddy\Claw\data\lpr_pending_sync.json`（UTF-8，目录不存在则建）：
   `{"date":"{PUB_DATE}","lpr_1y":"X.X","lpr_5y":"X.X","url":"<官方完整URL>","note":"待补录到 LPR历史数据完整版 DTkVQTWp0UFJqaEdv / 000001"}`
2. 微信消息**末尾**追加：`⚠️ 注：腾讯文档表格未能自动写入（文档工具不可用），数据已暂存本地待补录。`
3. 对话里说明需人工补录 + JSON 路径 + 目标表信息

写入成功则跳过本步骤，不追加提示。**严禁卡住反复重试、严禁谎报成功。**

## 步骤 4：微信发送结果

1. 读收件人配置：`C:\Users\huaxi\.workbuddy\skills\arcwechat\config\wechat_recipients.json`，取所有 enabled=true
2. 正文（用步骤 1 的实际 URL）：

```
📊 【LPR利率查询】

✅ 查询成功！

📅 公布日期：{YEAR}年{MONTH}月{DD}日（{WEEKDAY}）
🔄 调整情况：_____

📌 最新LPR利率：
• 1年期LPR：___%
• 5年期以上LPR：___%

📝 数据来源：中国人民银行
🔗 官方公告：<实际完整URL>

📂 历史数据查询：
• LPR历史数据完整版：https://docs.qq.com/sheet/DTkVQTWp0UFJqaEdv
• LPR查询日期计划-2026年v2：https://docs.qq.com/doc/DTnJTbWd6bmRtVnh5

---
【来自梦小喵🐱】
```

3. 发完按 common.md 第 2 条**截屏核验**，图存 `data\wechat_verify_lpr.png`

## 合规

只写官方公开利率数据，不涉及任何客户信息。
