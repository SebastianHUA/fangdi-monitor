# 项目记忆（fangdi-monitor）

## 系统概览
仓库 `SebastianHUA/fangdi-monitor`（SSH），看板 https://sebastianhua.github.io/fangdi-monitor/
核心脚本（Claw 根目录）：`fangdi_cdp_proxy_scraper.js`(--mode=newhouse|secondhand|subscription) / `cdp_proxy.js`(3456) / `generate_daily_report.js` / `sync_07am_bwHrDx.py` / `sync_07am_GxaSD5.py` / `sync_2350_bwHrDx.py` / `sync_subscription_0g5JQL.py` / `work_log_sync.py` / `tdoc_mcp.py` / `tdoc_helper.py`(垫片) / `land_tdoc_sync.py` / `gen_land_xlsx.py`
数据：一手房=首页当日(午夜归零)；二手房=昨日；楼市回顾=首页；认购公示须 CDP 抓 new_house_jjswlpgs.html

## 日期口径（最易错）
记录 `date` = 数据归属日。D-1 晚 23:50 抓当天一手房 → 写 D-1；D 早 07:00 抓前日二手+回顾 → 同写 D-1（同一条记录）。
脚本默认取 UTC：上海 08:00 为界，晚跑会错位 → **必须显式 `--date=`**。
判据一律查 D-1；查"今天 D"恒空 → 误报。
`fangdi_data.json` 必为按日期降序数组；取最新用 date 精确匹配，禁取"最后一条"。
⚠️ 禁止手动改 fangdi_data.json（例外：①自动化失败且能从腾讯文档取正确值 ②23:50 一手房失败用回顾回补）。

## 自动化
- 23:50 一手房（本地+腾讯 bwHrDx，不推 GitHub；过午夜禁跑，官网已归零）
- 07:00 二手+回顾（本地+腾讯 bwHrDx/GxaSD5+GitHub，微信发 梦比鱿鱼丝/沈胄磊/周凯琦，写哨兵）
- 07:15 认购公示；17:00 土地；17:30 工作日志提醒
- 哨兵 `data/.sent_<D-1>` 供看门狗判读，.gitignore 已忽略
- git commit 用 ASCII 消息（`update data <D-1>`）防 Git Bash 中文乱码
- **07:10 看门狗竞态**：主任务 07:00→约 07:20 才发完，07:10 必然抢跑误判补发。🚨 哨兵必须写**带内容**格式 `sent_at=<ISO+08:00> by main`，空文件看门狗不认（09-07 因此重复推送）。待主人把看门狗推迟到 07:30+ 并补上周凯琦。
- ⚠️ **连接器会话级断开是常见故障**：某些自动化会话里 tencent-docs 不挂载（tdoc_mcp 报 `NO_SERVICE`）或 GitHub SSH 被沙箱拦 → 数据只落本地。**事后任意会话（连接器恢复后）可无缝补账**：`sync_07am_bwHrDx.py <日期>` + `sync_07am_GxaSD5.py <日期>` 逐日重跑即可（脚本自带查重，有则 update 无则 add），再 `git pull --rebase --autostash` + push。2026-09-16 已用此法补回 9/13~9/15 三天。

## CDP 排障
代理存活：`curl localhost:3456/`（无 /health，404 正常）。ECONNREFUSED 9222 = 调试 Chrome 退出 → 用 `ensure_scrape_env.ps1`（有头模式）重拉；412 反爬 → 建 tab 后 reload，等 15~20s eval innerText 搜"今日签约"。
🚨 拉起进程/跑 ps1：只能在 PowerShell 工具里 `powershell.exe -ExecutionPolicy Bypass -File "绝对路径"`（Bash 调 ps1 被安全策略拦；Git Bash `start` 无效）。

## 数据规律
二手房周末显著高于工作日属正常：周六 1000~1250、周日 900~1040、工作日 600~730（2026-08-15~09-07 实测）。一手房相反，周末偏低 250~450。

## 腾讯文档（通道 + 通用约定）
🚨 唯一通道 = `tdoc_mcp.py`（读 `CODEBUDDY_MCP_CONFIG` 中 tencent-docs 的 url+Bearer，直连 127.0.0.1 MCP，自动解 SSE，3 次重试）。`from tdoc_mcp import call, ok, get_field, find_record_id`。旧 mcporter/tencentdocs.py(no_token) 已失效；`tdoc_helper.py` 改为垫片保持旧脚本可用。
- add/update 必须用 `records:[{field_values:[{field, ...}]}]`；用 `fields` 对象 = 假成功只留 auto_fill
- 文本 `text_value:{items:[{text,type:"text"}]}`；日期 `string_value:"毫秒戳"`
- 解析日期必用 `get_field()`（返回 field_values 列表，按 `r['fields']` 解析会全判 MISSING → 重复新增）
- 写后一律回读校验

## 三张业务表（file DTnNsSXVoc21TbkhF）
- `bwHrDx` 每日成交：字段带单位后缀（如"一手房成交面积（㎡）"）；23:50 只写一手房 4 字段，07:00 补齐
- `GxaSD5` 楼市回顾：字段名是「**楼市回顾内容**」；TS=UTC 午夜毫秒戳
- `0g5JQL` 认购公示：10 字段；本地「套数/上市面积/备案均价/入围比」→表「套数（套）/上市面积（㎡）/备案均价（元/㎡）/**认购比**」；数据日期=发现日≠认购开始日；三级去重幂等；同步已焊进 `scrape_subscription_data.js`
- 遗留：14 条历史缺失待补录；5 条字段缺失待修(rNCLMh/r7oFEA/reZxet/rwbVgb/reDrHb)；GxaSD5 08-15/08-19 各 2 条未定夺勿删

## 主人工作日志
腾讯文档 `DTkZDSWpxbWVUa1NN` sheet `NxtEWi`（唯一落点）；字段=日期毫秒戳(上海00:00)+工作内容多行序号。
固化脚本 `work_log_sync.py <YYYY-MM-DD> "条目"...`：查重→同天续号→回读校验；内置 `strip_no()` 去重，全重复输出 `NO_CHANGE` 不写，部分重复只追加差异。
⚠️ 中文条目用 Python 临时脚本塞 sys.argv 驱动（Git Bash 直传中文会吞引号/乱码），用完即删。
主人工作日志只记腾讯文档，不写本地 `.workbuddy/memory/*.md`（那是助手日志）。

## 看板约定
Pages 部署仓库根目录 → 主看板 = 根目录 `index.html`；`docs/`、`dashboard/` 是旧副本，改看板要三份同步。
认购过滤窗口=过去10天~未来14天（旧 `startDate<=today` 会漏掉未开认购的新盘）。改完 push 等 ~75s curl 线上 html grep 验证。

## 整洁约定（2026-09-04 主人拍板"不要存不想干的"）
临时产物（抓取日志/告警/微信文本/截屏/一次性脚本）用完即删或进 .gitignore；核心脚本必须 `git ls-files` 自查入库。
删除走**回收站**：Python311 `win32com.shell.shell.SHFileOperation(...FOF_ALLOWUNDO...)`（PowerShell Add-Type 被安全策略拦）。
2026-09-04 已清理 old_scripts/58 个 + 废弃脚本若干 → 未跟踪文件归零。清理后必做回归：py_compile + node --check + tdoc 连通性。

## 微信推送
格式：📊标题/📅数据日期/🏗️一手房/🏘️二手/📰楼市回顾/📈看板URL/📋表格URL；纯数据发三人，异常只发梦比鱿鱼丝。
🚨 **正文必须走 `--file` 读 UTF-8 文件**，禁把中文/emoji 当命令行参数（GBK 必乱码）；须 Python311（pywin32）。
⚠️ wechat_sender 曾"假 DONE"（按键走完≠送达），已加固 activate 失败 return False + 粘贴后等 0.6s，但仍无真送达回执。

## 截图
只走对话 present_files 发主人，**不发微信**。可行：Python ctypes 找 WorkBuddy 窗口 + `screenshot_hwnd.py <hwnd> <out>`。纯桌面全屏图在对话通道必失败。present_files 偶发 previewed:[]→重试。脚本 screenshot_hwnd.py/crop_wb.py/crop_wechat.py 已入库。

## GitHub
`git@github.com:SebastianHUA/fangdi-monitor.git`；rebase 冲突：fangdi_data.json 取记录更完整一方，index.html 取 --theirs。
⚠️ 脏工作区一律 `git pull --rebase --autostash`，禁手动 stash（曾 stash 忘 pop 丢一整天数据）。

## 土地市场监测
`land_monitor_curl.py 3` → land_monitor_results.csv；`gen_land_xlsx.py`（标黄 住宅/居住/商品房）；`land_tdoc_sync.py --dry-run`。
腾讯 `NHsPBsupJrkx/000001` 是传统电子表（sheet.* 工具）。🚨 `get_cell_data` 参数 start_row/end_row/start_col/end_col（0-based），传 range 被静默忽略只返 A1。表第 1 行表头，越往下越旧；去重键=发布日期+公告类型+公告号+地块名称。公告 17:00 后上网 → 必须全量比对补录。
