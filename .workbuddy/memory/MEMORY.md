# 项目记忆

## fangdi-monitor 系统
仓库 SebastianHUA/fangdi-monitor，看板 https://sebastianhua.github.io/fangdi-monitor/
脚本: fangdi_cdp_proxy_scraper.js(--mode=newhouse|secondhand), cdp_proxy.js(端口3456), generate_daily_report.js
同步: sync_07am_bwHrDx.py(成交)/sync_07am_GxaSD5.py(回顾)/sync_subscription_0g5JQL.py(认购), 均须Python311
数据: 一手房=首页当日(午夜重置); 二手房=昨日; 回顾=首页; 认购公示须CDP抓取

### 日期口径(最易错)
记录date=数据归属日。D-1晚23:50抓当天一手房→写D-1; D早07:00抓前日二手+回顾→写D-1
脚本默认取UTC: 上海08:00为界, 08:00后跑须显式--date=
判据一律查D-1; 查"今天D"恒空→误报

### CDP排障
代理活: curl localhost:3456/ (无/health,404正常)
ECONNREFUSED 9222=调试Chrome退出→重拉(有头模式,禁--headless=new)
412反爬→建tab后reload; 等15-20s eval innerText搜"今日签约"
过午夜禁跑newhouse(归零); 一手房失败用回顾回补

### 自动化
23:50一手房(本地+腾讯,不推GitHub); 07:00二手+回顾(本地+腾讯+GitHub,发梦比鱿鱼丝+沈胄磊+周凯琦); 07:15认购; 17:00土地
哨兵 `data/.sent_<D-1>` 供07:10看门狗判读
git commit 用 ASCII 消息防 Git Bash 中文乱码
fangdi_data.json必为数组按日期降序; 取最新用date精确匹配,禁取"最后一条"
⚠️禁止手动改fangdi_data.json(例外:①自动化失败且能从腾讯文档取正确值;②23:50一手房失败用回顾回补)

### 腾讯文档smartsheet通用约定
🚨add/update_records必用field_values数组: records:[{field_values:[{field,tvalue}]}]
文本: text_value:{items:[{text,type:"text"}]} (type必须text非plain)
日期: string_value:"毫秒戳"; auto_fill=true列强填当前时间→历史日期先建内容再update
🚨日期解析必用 get_field()：按 `r['fields']` 解析会全判 MISSING → 重复add_records

### 腾讯文档调用通道
唯一通道 = **`tdoc_mcp.py`(Claw根目录)**：读环境变量 CODEBUDDY_MCP_CONFIG 里 tencent-docs 的 url+Bearer+context，直连 JSON-RPC。
接口: `from tdoc_mcp import call, ok, get_field, find_record_id`
tdoc_helper.py 已改为垫片(优先import tdoc_mcp) → 历史脚本零改动可用。
自动化环境无 tencent-docs 服务时，用 `run_sync_via_plugin.py`(Claw根目录,Python311) 桥接 plugin 的 tencentdocs.py。
核心脚本 tdoc_mcp.py/tdoc_helper.py/work_log_sync.py/sync_*.py 等均已入库。

### 腾讯文档 DTnNsSXVoc21TbkhF
bwHrDx(成交)/0g5JQL(认购)/GxaSD5(回顾,TS=UTC午夜)
bwHrDx字段带单位后缀(如"一手房成交面积（㎡）")；共12字段
🚨GxaSD5字段名是「楼市回顾内容」(不是「楼市回顾」)

### 认购公示同步 0g5JQL
`sync_subscription_0g5JQL.py`(Python311): --date/--name(可多次)/--dry-run; 三级去重; 写后回读校验
10字段: 数据日期/认购开始/结束日期(string_value) / 项目名称·所在区·开发企业·认购比(text) / 套数·上市面积·备案均价(number)
🚨字段映射: 本地JSON无单位后缀,表字段带后缀且"入围比"→"认购比"。映射错=静默丢字段
🚨同步已焊进抓取脚本: scrape_subscription_data.js 发现新增后自动调 sync_subscription_0g5JQL.py（--no-sync可关）
🚨list_records服务端单页上限100条(page_size=200也截断),响应带has_more/next/total须循环翻页; load_table已修(09-15,commit bee1a43)。超过100条前,窗口外记录对去重/回读不可见→VERIFY_FAIL误报+重复写入
⚠️核查顺序: 报"同步失败"时先 `--dry-run` 复核是否其实已同步
⚠️遗留待办: 14条历史真缺失待主人决定; 5条字段缺失待修(rNCLMh/r7oFEA/reZxet/rwbVgb/reDrHb); 5条重复记录待主人决定是否删(rRznFI/rQ7YKD/rtijFj/rcBYgk/rkSqqH, 09-15窗口外盲区所致, 与09-12批次同键)

## 工作日志
腾讯文档 smartsheet DTkZDSWpxbWVUa1NN sheet NxtEWi
固化脚本 `work_log_sync.py <YYYY-MM-DD> "条目1"...`：先查重→同天续号→写后回读校验，已固化去重(全重复→SKIP_DUP不写)
🚨 主人工作日志只记腾讯文档，不写本地 .workbuddy/memory/*.md
🚨 17:30提醒通道(09-01拍板): 工作日志提醒发在当前对话，不发微信
⚠️ 自动化 1782772611455 prompt 仍是"首步强制发微信"状态，待 automation_update 改回对话输出

## 看板(dashboard)约定
Pages 部署仓库根目录 → 主看板 = 根目录 index.html；docs/dashboard 是旧副本
认购表 fetch data/subscription_data.json（.gitignore例外放行）
认购过滤窗口=过去10天~未来14天

## 工作区整洁约定(09-04拍板)
临时产物一律不落工作区、不进git，用完即删
核心脚本必须入库: tdoc_mcp.py/tdoc_helper.py/work_log_sync.py/sync_*.py/scrape_subscription_data.js/land_tdoc_sync.py/gen_land_xlsx.py/send_*.py
清理用回收站: Python311 win32com SHFileOperation(FO_DELETE, FOF_ALLOWUNDO|FOF_NOCONFIRMATION|FOF_SILENT)

## 微信日报格式
📊上海房地产市场日报/📅数据日期/🏗️一手房/🏘️二手/📰楼市回顾/📈看板URL/📋表格URL
纯数据发梦比鱿鱼丝+沈胄磊+周凯琦; 异常只发梦比鱿鱼丝
🚨 微信发送"假DONE"坑: send_to_wechat 已加固(activate失败return False; 粘贴后等0.6s)，但仍无真送达校验

## 截图偏好(09-30固化)
通道: 截图只走对话框 present_files，不发微信
方法: screenshot_hwnd.py + PrintWindow(须Python311 pywin32)
纯桌面/全屏图在对话通道必 previewed:[]（环境限制）

## 环境坑
微信/pywin32须Python311(托管3.13.12无pywin32)
mcporter传中文JSON用Python subprocess列表传参,禁Node execFileSync
启动常驻后台进程只能用 PowerShell Start-Process(Hidden)，Bash的&会被回收
写.ps1必须存UTF-8 with BOM；执行用 `powershell.exe -ExecutionPolicy Bypass -File "绝对路径"`

## GitHub SSH
git@github.com:SebastianHUA/fangdi-monitor.git
rebase冲突: fangdi_data.json取--ours(远端权威); index.html取--theirs(本地修复)
脏工作区做rebase一律 `git pull --rebase --autostash`，禁手动git stash

## 土地市场监测
抓取: land_monitor_curl.py(技能目录,Python311+bs4) → land_monitor_results.csv
XLSX: gen_land_xlsx.py(标黄关键词)
同步: land_tdoc_sync.py(Claw根目录,--dry-run预演)
腾讯 NHsPBsupJrkx/000001 = 传统电子表格(非smartsheet),用sheet.*工具
get_cell_data参数是start_row/end_row/start_col/end_col(0-based),不是range
去重键=发布日期+公告类型+地块公告号+地块名称
公告17:00后才上网→必须全量比对补录
