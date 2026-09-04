# 项目记忆

## fangdi-monitor 系统
仓库 SebastianHUA/fangdi-monitor，看板 https://sebastianhua.github.io/fangdi-monitor/
脚本: fangdi_cdp_proxy_scraper.js(--mode=newhouse|secondhand), cdp_proxy.js(端口3456,在Claw非本目录), generate_daily_report.js, tdoc_helper.py(Claw根目录)
同步: sync_07am_bwHrDx.py(每日成交)/sync_07am_GxaSD5.py(回顾), Python311跑
数据: 一手房=首页当日(午夜重置); 二手房=昨日; 回顾=首页; 认购公示 new_house_jjswlpgs.html 须CDP抓取

### 日期口径(最易错)
记录date=数据归属日。D-1晚23:50抓当天一手房→写D-1; D早07:00抓前日二手+回顾→写D-1, 同属一条D-1记录
脚本默认取UTC(第577行): 上海08:00为界, 08:00后跑错位→须显式--date=
判据一律查D-1; 查"今天D"恒空→误报

### CDP排障
代理活: curl localhost:3456/ (无/health,404正常)
ECONNREFUSED 9222=调试Chrome退出→重拉(有头模式,禁--headless=new,禁启动Chrome调试.bat)
412反爬→建tab后reload; 等15-20s eval innerText搜"今日签约"
过午夜禁跑newhouse(归零); 一手房失败用回顾"预/出售N套"回补

### 自动化
23:50一手房(本地+腾讯,不推GitHub); 07:00二手+回顾(本地+腾讯bwHrDx+GxaSD5+GitHub,发梦比鱿鱼丝+沈胄磊+**周凯琦**); 07:15认购; 17:00土地
哨兵 `data/.sent_<D-1>` 供07:10看门狗判读; ⚠️ .gitignore 规则 `data/.sent_*` 于2026-09-01补加(此前实际未忽略)
git commit 用 ASCII 消息("update data <D-1>")防 Git Bash 中文乱码
fangdi_data.json必为数组按日期降序; 取最新用date精确匹配,禁取"最后一条"
⚠️禁止手动改fangdi_data.json(例外:①自动化失败且能从腾讯文档取正确值;②23:50一手房失败用回顾回补)

### 腾讯文档smartsheet通用约定
🚨add/update_records必用field_values数组: records:[{field_values:[{field,tvalue}]}]. 用fields对象=假成功只留日期auto_fill("只有日期无内容")
文本: text_value:{items:[{text,type:"text"}]} (type必须text非plain)
日期: string_value:"毫秒戳"; auto_fill=true列强填当前时间→历史日期先建内容再update
查list_records返回同构
🚨**调用通道(2026-08-31重建)**: mcporter.cmd 已在本机消失(仅剩~/.mcporter/mcporter.json)，tdoc_helper.py 与 `tencentdocs.py tdoc_init`(报no_token) 均失效。
  现唯一通道 = **`tdoc_mcp.py`(Claw根目录)**：读环境变量 `CODEBUDDY_MCP_CONFIG` 里 tencent-docs 的 url+Bearer+context，直连 `http://127.0.0.1:49451/<hash>/mcp` 走 JSON-RPC tools/call，自动解 SSE/裸JSON，3次重试。共219个工具。
  接口: `from tdoc_mcp import call, ok, get_field, find_record_id`；`call(tool,args)`/`ok(resp)` 与旧 tdoc_helper 同签名，**改 import 一行即可迁移**。
  ✅**tdoc_helper.py 已于2026-09-04改为垫片**：内部优先 import tdoc_mcp，旧 mcporter 逻辑仅兜底 → 历史脚本零改动恢复可用。
  ⚠️三个核心脚本 `tdoc_mcp.py`/`tdoc_helper.py`/`sync_subscription_0g5JQL.py` 曾**未纳入 git**（2026-09-04 起已补入版本库，避免整条链路因文件丢失报废）
🚨**日期解析必用 get_field()**：list_records 返回 `field_values` 列表，按 `r['fields']` 解析会全判 MISSING → 重复 add_records(2026-08-20~25曾6天双记录)。已验证 get_field 下 bwHrDx 67条 / GxaSD5 61条日期全解析成功

### 腾讯文档 DTnNsSXVoc21TbkhF
bwHrDx(成交)/0g5JQL(认购)/GxaSD5(回顾,TS=UTC午夜)
bwHrDx字段带单位后缀(如"一手房成交面积（㎡）")；共12字段含"新楼盘公示条数""单选"
🚨**GxaSD5字段名是「楼市回顾内容」**(不是「楼市回顾」)；回读用错会取到None误判写入失败。取值前先 `smartsheet.list_fields` 列名
同步脚本(均须Python311+传日期参数): sync_2350_bwHrDx.py(23:50只写一手房4字段,不碰二手) / sync_07am_bwHrDx.py / sync_07am_GxaSD5.py / **sync_subscription_0g5JQL.py**

### 认购公示同步 0g5JQL(2026-09-01重建)
`sync_subscription_0g5JQL.py`(Python311): --date/--name(可多次)/--dry-run; 三级去重(项目名+认购开始 → 项目名+套数+均价 → 套数+均价); 写入前字段自检(缺字段拒绝写防半截记录); 写后回读校验
10字段: 数据日期(发现日)/认购开始日期/认购结束日期(均string_value上海午夜戳) / 项目名称·所在区·开发企业·认购比(text) / 套数（套）·上市面积（㎡）·备案均价（元/㎡）(number)
🚨**字段映射(踩过坑)**: 本地JSON用「套数/上市面积/备案均价/入围比」无单位后缀,表字段带后缀且"入围比"→"认购比"。映射错=静默丢4个字段(曾产生半截记录rCXkev已删)
日期口径: 数据日期=发现日 ≠ 认购开始日期(历史58/73条两者不同)
🚨**2026-09-04根治: 同步已焊进抓取脚本**。`scrape_subscription_data.js` 在发现新增楼盘后自动调 `Python311 sync_subscription_0g5JQL.py --date <今天>`（--no-sync 可关），不再依赖自动化任务"记得"同步这一步。同步失败只告警不改退出码；重复执行幂等（三级去重 → NO_CHANGE）
🚨**tdoc_helper.py 已改为垫片**: 优先走 tdoc_mcp.py，mcporter 逻辑仅兜底，call/ok 签名不变 → 旧脚本自动恢复可用
⚠️核查顺序: 任务报"腾讯文档同步失败"时，先 `git log --oneline -3` + 跑一次 `--dry-run` 复核是否其实已同步，别急着重跑抓取（09-04 白造一次 updateTime 冲突）
⚠️遗留待办: 14条历史真缺失待主人决定是否补录; 5条字段缺失待修(rNCLMh/r7oFEA/reZxet/rwbVgb/reDrHb)

## 工作日志(强约定)
腾讯文档 smartsheet DTkZDSWpxbWVUa1NN sheet NxtEWi（主人工作日志唯一落点）
字段: 日期毫秒戳(上海00:00)+工作内容text多行序号
🚨 固化脚本 `work_log_sync.py <YYYY-MM-DD> "条目1" "条目2"...`：先查重→同天续号→写后回读校验
⚠️ **最大坑：内容去重**。脚本"同天续号"逻辑在当天已有**完全相同**内容时会再追加一份→产生重复。正确流程：
  - 当天无记录 → 直接新建(ADD)
  - 当天已有记录 → **先比对内容**：本次条目已全包含→跳过不写；仅含新增条目→只续号追加差异项；内容冲突→提示主人确认
  - 绝不直接对"已存在的当天"原样再跑一次脚本
  ✅ **已在脚本内固化去重(2026-09-01)**：`work_log_sync.py` 新增 `strip_no()` 去序号比对 → 全重复打印 `SKIP_DUP(N)`+`NO_CHANGE` 不写；部分重复只追加差异项。实测同参数重跑幂等
  🚨 import 已改为 `from tdoc_mcp import call, ok`（旧 tdoc_helper 通道已失效）
  ⚠️ 中文条目须用 Python subprocess 列表传参驱动（Git Bash 直传会吞引号/乱码），勿在 bash 里裸传中文
🚨 主人工作日志只记腾讯文档，**不再写本地 `.workbuddy/memory/*.md`**（那些是助手日志，非主人工作日志）
实况: 2026-08-27(4条,rVPmjP) 曾误追加成8条已回退; 2026-08-28(3条,rL0x8I) 新建正常; **2026-08-31(7条,rbdyin) 新建正常**
🚨 **17:30提醒通道(2026-09-01 00:02主人最终拍板)**: **工作日志提醒回到"当前对话"输出**，不发微信。
  经过: 08-31 22:05 因"对话里看不到"改 push_to_wechat=true 并补发微信; 09-01 00:02 主人改口"以后工作日志提醒发在这个对话里" → **以对话输出为准**。
  ⚠️ 自动化 1782772611455 的 prompt 目前仍是"首步强制发微信"状态，**待 automation_update 工具恢复后改回对话输出**（2026-09-01 00:02 尝试时 automation_update 工具在本上下文不可用，且规则禁止直接改 sqlite/配置文件）

## 看板(dashboard)约定(2026-09-04确认)
🚨 **Pages 部署的是仓库根目录** → 主看板 = 根目录 `index.html`；`docs/index.html` 与 `dashboard/index.html` 是 8/16 的**旧副本**(缺时区修复)，改看板要三份一起改才一致
认购表 fetch `data/subscription_data.json`（根目录那份，已被 .gitignore 的 `!data/subscription_data.json` 例外放行，能推）
⚠️ `docs/data/` 整目录被 .gitignore 忽略(仅 `!docs/data/fangdi_data.json` 例外) → docs 版看板的认购数据文件**不存在**(404)，但因 Pages 走根目录所以不影响主看板
认购过滤窗口已改为 **过去10天 ~ 未来14天**(2026-09-04修复)：旧逻辑 `startDate <= today` 只显示已开始的，把"刚公示、明天才开认购"的新盘全漏掉（9/5 开盘的 3 个新盘被误杀），而代码里"即将开始"状态分支因此永不触发
验证改动：改完 push 后等 ~75s，curl 线上 html grep 新变量名确认 Pages 已部署

## 微信日报格式
📊上海房地产市场日报/📅数据日期/🏗️一手房(✅当日签约X套/X㎡,📐套均,🏢可售)/🏘️二手(✅当日签约,📐套均,📋挂牌)/📰楼市回顾(不清洗)/📈看板URL/📋表格URL
纯数据发梦比鱿鱼丝+沈胄磊; 异常只发梦比鱿鱼丝

## 截图偏好(2026-08-30固化,主人确认)
🚨 **通道**: 截图只走对话框 present_files 发主人,**不发微信**(含文件助手/本人"梦比鱿鱼丝")。
✅ **能成的方法**: 截 WorkBuddy 界面 = Python ctypes 找 WorkBuddy 窗口句柄 + `screenshot_hwnd.py <hwnd> <out>`(PrintWindow 按窗口抓) → present_files 在对话发。主人20:42实测"现在可以了"。
❌ **不行的**: 纯桌面/全屏图(desktop_full.png 含任务栏)在对话通道必 previewed:[]（连发3次全失败,客户端环境限制）；WorkBuddy 是无边框窗口 SW_MAXIMIZE 不生效、带不上任务栏。
⚠️ present_files 偶发 previewed:[]（随机性环境限制,非操作问题）→ 重试即可,同一图有时能出有时不能。
脚本: screenshot_hwnd.py / screenshot_desktop.py / crop_wb.py / crop_wechat.py 均在 Claw 根目录,须 Python311(pywin32/GDI)。

## 环境坑
微信/pywin32须Python311(托管3.13.12无pywin32)
mcporter传中文JSON用Python subprocess列表传参,禁Node execFileSync(吞引号)
🚨 **微信发送"假DONE"坑(2026-08-30实测)**: wechat_sender.send_to_wechat 原逻辑无论搜索是否命中正确联系人/粘贴是否成功最后都return True,只确认按键走完≠对方收到。07:00任务记"沈胄磊DONE"但对方未收到,手动重发后才到。
  **已加固**: ① activate_wechat()失败改为return False不再盲发; ②粘贴消息后等待0.2s→0.6s让大文本稳定落框。改动在~/.workbuddy/skills/arcwechat/scripts/wechat_sender.py
  ⚠️ 仍无法读聊天框文本做真送达校验,键盘模拟方案本质无回执。建议: 重要推送后让主人抽查确认; 或改文件发送(但长文本日报体验差)
tencentdocs.py: .../tencent-docs-plugin/1.0.0/skills/tencent-docs/; 用法 tdoc_call tencent-docs <tool> '<JSON>'
腾讯文档票据间歇性: 调用前tdoc_init探READY

## GitHub SSH
git@github.com:SebastianHUA/fangdi-monitor.git (2026-08-14起,HTTPS443 reset+旧PAT失效)
rebase冲突: fangdi_data.json取--ours(远端权威); index.html取--theirs(本地修复)
⚠️脏工作区做rebase一律`git pull --rebase --autostash`,禁手动git stash。2026-08-26实测:主任务stash后忘pop,08-25整条记录(一手+二手+回顾)遗留stash@{0},json未落盘、提交只含md、看板缺数据。恢复=stash pop+重生成日报比MD5验证

## 腾讯文档智能表 DTnNsSXVoc21TbkhF 坑
list_records返回`field_values`列表(非`fields`字典),解析错会把全部日期判成MISSING(误报)
日期字段两表格式不同: bwHrDx=text_value「YYYY-MM-DD」文本; GxaSD5=string_value UTC午夜毫秒戳。匹配错→查不到已有行→add_records重复新增
⚠️2026-08-20~25 bwHrDx曾连续6天双记录(23:50仅一手房残缺条+07:00完整条),即"面积/套均显示0"元凶。已用 dedup_tdoc.py 清理(严格子集校验+删前备份data/tdoc_backup_before_dedup.json,默认dry-run,--apply才删)
GxaSD5 08-15/08-19各2条且回顾内容不同,未定夺,勿擅自删

## 土地市场监测(2026-09-01重写)
抓取: `land_monitor_curl.py 3`(技能目录,Python311+bs4,参数=页数) → Claw根目录 land_monitor_results.csv
XLSX: `gen_land_xlsx.py`(标黄关键词 住宅/居住/普通商品房/商品房)
同步: **`land_tdoc_sync.py`(Claw根目录,Python311,--dry-run 预演)** ← 记忆里旧的 update_sheet.py 其实不存在
腾讯 NHsPBsupJrkx/000001 = 传统电子表格(非smartsheet),用 sheet.* 工具,通道一律走 tdoc_mcp.py
🚨 **sheet.get_cell_data 参数是 start_row/end_row/start_col/end_col(0-based),不是 range**; 传range被静默忽略只返回A1→极易误判"表是空的"。return_csv=true 拿 csv_data; 单次≤300行需分页
表结构: 第1行表头,数据第2行起**越往下越旧**(1062行,覆盖到2024-08); 16列序与CSV完全一致(A=公告标题…P=四至范围)
去重键 = 发布日期+公告类型+地块公告号+地块名称; 同地块多阶段(预告→出让公告→出让结果)各占一行是正常,别当重复删
⚠️ 旧版异名坑: 07-28「拟出让预告」在表内是「出让预告」(公告号空),脚本已内置排除
公告17:00后才上网→**必须全量比对补录**(只看"今天"会漏); set_range_value偶no_token→重试3次
推送口径: 任务原文=今日有新公告且涉宅; **但当天无新公告却发现历史批次从未入库且涉宅时也推送**(09-01先例),消息须标注"补录"
