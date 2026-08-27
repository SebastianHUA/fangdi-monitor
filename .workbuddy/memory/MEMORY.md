# 项目记忆

## fangdi-monitor 系统
仓库 SebastianHUA/fangdi-monitor，看板 https://sebastianhua.github.io/fangdi-monitor/
脚本：fangdi_cdp_proxy_scraper.js(--mode=newhouse|secondhand)，cdp_proxy.js(端口3456，在Claw非本目录)，generate_daily_report.js
数据：一手房=首页当日(午夜归零)；二手房=昨日；楼市回顾=首页；认购公示 new_house_jjswlpgs.html 须CDP抓取

### 日期口径
记录date=数据归属日。D-1晚23:50抓当天一手房→写D-1；D早07:00抓前日二手+回顾→写D-1，同属一条D-1记录
脚本默认取UTC(第577行)：上海08:00为界，08:00后跑错位→须显式--date=

### CDP排障与调用约定
代理活：curl localhost:3456/ (无/health，404正常)
ECONNREFUSED 9222=调试Chrome退出→重拉(有头模式，禁--headless=new，禁启动Chrome调试.bat)
412反爬→建tab后reload；等15-20s eval innerText搜"今日签约"
过午夜禁跑newhouse(归零)；一手房失败用回顾"预/出售N套"回补
**CDP 调用约定**：`/new` 是 **POST**（2026-08-27已踩坑），从 query 参数 `url` 取地址；响应字段名 `targetId`；eval 用 `POST /eval?target=<targetId>`，表达式作为body原文；关tab `GET /close?target=<targetId>`

### 自动化
23:50一手房(本地+腾讯，不推GitHub)；07:00二手+回顾(本地+腾讯bwHrDx+GxaSD5+GitHub，发梦比鱿鱼丝+沈胄磊)；07:15认购；17:00土地
fangdi_data.json必为数组按日期降序；取最新用date精确匹配，禁取"最后一条"
禁止手动改fangdi_data.json(例外：自动化失败且能从腾讯文档取正确值；23:50一手房失败用回顾回补)

### 腾讯文档smartsheet通用约定
add/update_records必用field_values数组：`records:[{field_values:[{field:"字段名",type_value:值}]}]`。用fields对象=假成功只留日期auto_fill("只有日期无内容")
- 文本：`text_value:{items:[{text,type:"text"}]}` (type必须text非plain)
- 日期：GxaSD5用string_value UTC午夜毫秒戳；bwHrDx用text_value「YYYY-MM-DD」文本
- 数字：`number_value`
- 字段查询：`smartsheet.list_fields`
- `smartsheet.fetch` 基本不可用，别调
- mcporter会挂起，改用 `tencentdocs.py` 直接调用：`python3 tencentdocs.py tdoc_call tencent-docs smartsheet.add_records '<json>'`
- `tencentdocs.py` 路径：`C:\Users\huaxi\.workbuddy\plugins\cache\workbuddy-builtin\tencent-docs-plugin\1.0.0\skills\tencent-docs\tencentdocs.py`
- `smartsheet.update_records`/`delete_records` 返回silent success，不验证生效；优先delete+新add(用record_ids字段)

<<<<<<< Updated upstream
### 腾讯文档 DTnNsSXVoc21TbkhF
bwHrDx(成交)/0g5JQL(认购)/GxaSD5(回顾)
bwHrDx字段带单位后缀(如"一手房成交面积（㎡）")
=======
**CDP 调用约定**：`/new` 是 **POST**（非 GET！8-27 已踩坑，scrape_subscription_data.js 之前用 GET 一直侥幸成功，2026-08-27 起必须改 POST），从 **query 参数** `url` 取地址（不解析 POST body）；响应字段名是 **`targetId`**；eval 用 `POST /eval?target=<targetId>`，**表达式作为 body 原文**（纯字符串）；关 tab `GET /close?target=<targetId>`。
>>>>>>> Stashed changes

### 数据字段
- `newHouse`: `todaySignUnits` / `todaySignArea` / `availableUnits`
- `secondHand`: `yesterdaySaleCount` / `yesterdaySaleArea` / `listingCount`
<<<<<<< Updated upstream
- 顶层可选 `marketReview`（字符串）；面积统一㎡
=======
- 顶层可选 `marketReview`（字符串）；面积统一㎡；`fangdi_data.json` 必为数组

### 腾讯文档（smartsheet `DTnNsSXVoc21TbkhF`）
- 每日成交 `bwHrDx`、认购明细 `0g5JQL`、楼市回顾 `GxaSD5`
- 字段：number→`number_value`，text→`text_value{items:[{text,type}]}`，日期→毫秒时间戳字符串（GxaSD5 沿用 **UTC 午夜**约定）
- bwHrDx 字段标题带单位后缀，如"一手房成交面积（㎡）"、"二手房套均面积（㎡/套）"，简称会报 field not found
- ✅ **2026-08-27：smartsheet `add_records` 必须用 list+字段名 格式**（8-27 实测）
  - ⚠️ 错误格式：`{"field_values": {"fIDxxx": {"text_value": ...}}}`（dict+field_id）→ 静默失败，返回空 records
  - ⚠️ 错误格式：`{"field_values": {"fIDxxx": {...}}}`（dict, 字段名 `fields_values` 带 s）→ 创建空记录，无字段值
  - ⚠️ 错误格式：`{"field_values": [{"field_id": "fIDxxx", "date_time_value": ...}]}`（list, field_id）→ `code:22004 mutation failed`
  - ✅ 正确格式：`{"file_id":"...","sheet_id":"...","records":[{"field_values":[{"field":"数据日期","date_time_value":"毫秒时间戳"},{"field":"所在区","text_value":{"items":[{"text":"...","type":"text"}]}},{"field":"套数（套）","number_value":123}]}]}` — **`field_values` 是 list，字段标识用中文 `field` 名（非 field_id）**
  - ⚠️ mcporter（`tdoc_helper.py`）会挂起，改用 `tencentdocs.py` 直接调用：`python3 tencentdocs.py tdoc_call tencent-docs smartsheet.add_records '<json>'`
  - `tencentdocs.py` 路径：`C:\Users\huaxi\.workbuddy\plugins\cache\workbuddy-builtin\tencent-docs-plugin\1.0.0\skills\tencent-docs\tencentdocs.py`
  - 字段查询工具名是 `smartsheet.list_fields`（非 `get_fields`）
  - `smartsheet.fetch` 接口要求 `pad_id`/`sub_id`（不是 `file_id`/`sheet_id`），且 `sub_id` 校验严苛，常报 `invalid sheet id` → **基本不可用，别浪费时间调 fetch，直接信任 add 返回的 record_id**
  - `smartsheet.update_records` / `delete_records` 返回 silent success 但**不验证生效**；别寄希望于 update，先 delete + 新 add 更可靠（用 `record_ids` 字段，非 `records`）
  - 历史问题（8-17~8-19）：`add_records` 仅创建空记录、`update_records` 不生效、`fetch` 返回 -32602/-32603；8-20 修复过一次，8-27 又变了数据格式
>>>>>>> Stashed changes

### 看板
只显示最近"部分完整"数据（新房或二手>0）；根目录/dashboard/docs三处index.html+chart.umd.min.js须一致

## 认购公示系统
<<<<<<< Updated upstream
URL `new_house/new_house_jjswlpgs.html`，本地 `data/subscription_data.json`。表格JS动态渲染，必须用CDP Proxy(WebFetch只能拿表头)。页面可能重定向到首页，脚本会自动重新导航。
- 2026-08-27修复：`scrape_subscription_data.js` 的 `createTab` 必须用 `POST /new`
- 数据真实性：网站DOM `<span>390000</span>` 即可信字段值；官网备案均价可能异常，按"忠实记录官网"原则不手动改，仅在微信提醒主人核对
=======
URL `new_house/new_house_jjswlpgs.html`，本地 `data/subscription_data.json`。表格 JS 动态渲染，必须用 CDP Proxy（WebFetch 只能拿表头）。页面可能重定向到首页，脚本会自动重新导航。
- ⚠️ **2026-08-27 修复**：`scrape_subscription_data.js` 的 `createTab` 必须用 `POST /new`（之前写 GET 是错的，仅在旧版 CDP Proxy 时偶然工作）。如果 CDP Proxy 升级后脚本报错 `{"error":"not found: GET /new"}`，把这个改回 POST 即可。
- ⚠️ **数据真实性**：网站 DOM `<span>390000</span>` 即可信字段值；当前已多次出现官网备案均价字段异常（如 2026-08-27 乐满庭 "390000 元/㎡" vs 同区其他楼盘 3-7 万元/㎡），但按"忠实记录官网"原则不手动改，仅在微信提醒主人核对。
>>>>>>> Stashed changes

## 土地市场监测
脚本 land_monitor_curl.py(需bs4，Python311)/update_sheet.py；腾讯 NHsPBsupJrkx 是传统电子表格(非smartsheet)，用sheet.insert_dimension+set_range_value
公告17:00后才上网→全量比对补录；set_range_value偶no_token→sleep重试

## 工作日志(强约定)
腾讯文档 smartsheet DTkZDSWpxbWVUa1NN sheet NxtEWi
字段：日期毫秒戳(上海00:00)+工作内容text多行序号
先查后追加，同天不替换；更新附链接
.workbuddy/memory/*.md是助手日志，非主人工作日志

## 微信日报格式
📊上海房地产市场日报/📅数据日期/🏗️一手房(✅当日签约X套/X㎡,📐套均,🏢可售)/🏘️二手(✅当日签约,📐套均,📋挂牌)/📰楼市回顾(不清洗)/📈看板URL/📋表格URL
纯数据发梦比鱿鱼丝+沈胄磊；异常只发梦比鱿鱼丝

## 环境坑
微信/pywin32须Python311(托管3.13.12无pywin32)
mcporter传中文JSON用Python subprocess列表传参，禁Node execFileSync(吞引号)
腾讯文档票据间歇性：调用前tdoc_init探READY

## GitHub SSH
git@github.com:SebastianHUA/fangdi-monitor.git (2026-08-14起，HTTPS443 reset+旧PAT失效)
rebase冲突：fangdi_data.json取--ours(远端权威)；index.html取--theirs(本地修复)
脏工作区做rebase一律`git pull --rebase --autostash`，禁手动git stash
