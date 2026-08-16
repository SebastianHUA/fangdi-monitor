# 项目记忆

## fangdi-monitor 系统

**架构**：独立仓库 `SebastianHUA/fangdi-monitor`，GitHub Pages https://sebastianhua.github.io/fangdi-monitor/

**脚本**：
- 抓取：`fangdi_cdp_proxy_scraper.js`（`--mode=newhouse|secondhand --date=YYYY-MM-DD`），23:50 一手房与 07:00 二手房共用
- CDP Proxy：`Claw/cdp_proxy.js`（⚠️不在 fangdi-monitor 目录），端口 3456
- 日报：`generate_daily_report.js --date=YYYY-MM-DD`（读 `data/fangdi_data.json` 数组 → 输出 `data/fangdi_daily_report_日期.md`）
- 认购：`scrape_subscription_data.js`、`update_subscription_date.js`
- 腾讯文档调用封装：`fangdi-monitor/tdoc_helper.py`（`call(tool, args)`，Python subprocess 包 mcporter，规避中文 JSON 传参坑）

**数据来源**：一手房=首页当日（午夜重置，仅当日可采）；二手房=昨日（可补采）；楼市回顾=首页。

### CDP / 抓取排障（按顺序）
1. `curl localhost:3456/` — 代理是否活（⚠️ 无 `/health` 端点，404 属正常）
2. `curl "localhost:3456/new?url=..."` — 若返回 `ECONNREFUSED 127.0.0.1:9222` 说明**带调试端口的 Chrome 已退出**（其他 chrome.exe 不算）
   - 拉起：`"/c/Program Files/Google/Chrome/Application/chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\temp\chrome-debug" --no-first-run --no-default-browser-check about:blank &`
   - ❌ 不要用 `Claw/启动Chrome远程调试.bat`（会 taskkill 主人所有 Chrome）
   - ⚠️ 必须**有头模式**，`--headless=new` 下 fangdi.com.cn 返回空文档
3. `curl 127.0.0.1:9222/json/version` — UA 含 HeadlessChrome 说明模式错
4. 新 profile 首访必被反爬（HTTP 412）→ 建 tab 后执行一次 `location.reload()` 让挑战 cookie 落地
5. 等 15~20s 后 eval `document.body.innerText` 搜"今日签约"，确认官网**是否已发数**；已发数→重试脚本；未发数→才考虑回补

**CDP 调用约定**：`/new` 只从 **query 参数** `url` 取地址（不解析 POST body）；响应字段名是 **`targetId`**；eval 用 `POST /eval?target=<targetId>`，**表达式作为 body 原文**（纯字符串）；关 tab `GET /close?target=<targetId>`。

**渲染时序**：`readyState=complete`（约8s）时"今日签约"仍为空，需再等 7~12s；偶发 0/null 多为时序问题，重试即可。

**🚨 过午夜绝不可跑 newhouse**：首页 00:00 归零，脚本不校验日期会写入全零记录（需人工清理 3 处文件）。任务延迟到 00:00 后 → 直接放弃，次日 07:00 用楼市回顾回补。

**楼市回顾时延**：07:00 首页显示的是**前一天**数据。23:50 一手房任务失败时，可用其"预/出售N套/N万㎡"回补 newHouse 的 todaySignUnits/todaySignArea，availableUnits 沿用前一日。先例：7-20、7-22、7-29、8-07。

### 自动化任务
- **23:50 一手房**：存本地 + 腾讯文档，❌不推 GitHub
- **07:00 二手房+楼市回顾**：存本地 + 腾讯文档（bwHrDx + GxaSD5，**GxaSD5 必须同步，不可跳过**）+ ✅推 GitHub，日报发梦比鱿鱼丝 + 沈胄磊
- **07:15 认购数据**、**17:00 土地市场监控**

### 数据字段（严格匹配）
- `newHouse`: `todaySignUnits` / `todaySignArea` / `availableUnits`
- `secondHand`: `yesterdaySaleCount` / `yesterdaySaleArea` / `listingCount`
- 顶层可选 `marketReview`（字符串）；面积统一㎡；`fangdi_data.json` 必为数组

### 腾讯文档（smartsheet `DTnNsSXVoc21TbkhF`）
- 每日成交 `bwHrDx`、认购明细 `0g5JQL`、楼市回顾 `GxaSD5`
- 字段：number→`number_value`，text→`text_value{items:[{text,type}]}`，日期→毫秒时间戳字符串（GxaSD5 沿用 **UTC 午夜**约定）
- bwHrDx 字段标题带单位后缀，如"一手房成交面积（㎡）"、"二手房套均面积（㎡/套）"，简称会报 field not found

### 看板
- 只显示最近"部分完整"数据（新房或二手>0）；`getDataDate()` 与 `updateDashboard()` 逻辑须一致
- 根目录 / dashboard / docs 三处 `index.html` + `chart.umd.min.js` 须一致；Chart.js 本地加载不依赖 CDN

## 认购公示系统
URL `new_house/new_house_jjswlpgs.html`，本地 `data/subscription_data.json`。表格 JS 动态渲染，必须用 CDP Proxy（WebFetch 只能拿表头）。页面可能重定向到首页，脚本会自动重新导航。

## 土地市场监测
脚本 `land_monitor_curl.py` / `parse_detail_optimized.py` / `update_sheet.py`；腾讯文档 `NHsPBsupJrkx`。
- ⚠️ `NHsPBsupJrkx` 是**传统电子表格**（worksheet），不是 smartsheet：smartsheet API 报 6086003；须用 `sheet.insert_dimension` + `sheet.set_range_value` + `sheet.get_cell_data`；sheet_id=`000001`，表头第0行，数据第1行起（最新在前）
- 2026-07-28 API 改版：公告列表从 JSON 改 HTML，新公告用 `href="URL"`（旧版 `onclick="jump(UUID)"`）
- ⚠️ **公告发布延迟**：部分公告 17:00 后才上网，只筛当天日期会漏录 → 须按公告号与文档已有记录**全量比对**补录
- ⚠️ **详情抓取限制**：`_hand` 后缀不是可靠判据，普通 uuid 的出让公告也可能是 JS 加密反爬页，agent-browser 会挂起数分钟（须及时 kill）→ 只录标题+日期+类型
- ⚠️ `set_range_value` 偶发 `ERROR:no_token` 属瞬时票据抖动 → 带 sleep 重试 2-4 次；insert 成功而 set 失败会留空行，重试须沿用同一 row index
- tencentdocs.py 路径（2026-08-10 更新，旧 `AppData/.../resources/builtin-plugins/...` 已失效报 Errno 2）：`C:/Users/huaxi/.workbuddy/plugins/cache/workbuddy-builtin/tencent-docs-plugin/1.0.0/skills/tencent-docs/tencentdocs.py`；再失效就 `find` 搜 `tencentdocs.py` 重新定位。用法 `tdoc_call sheet-mcp <tool> '<JSON>'`（工具名**无** `sheet.` 前缀）
- ⚠️ 脚本 `land_monitor_curl.py` 依赖 bs4，须用 `C:\Users\huaxi\AppData\Local\Programs\Python\Python311\python.exe` 运行（托管 3.13.12 无 bs4）

## 微信日报格式（强制，2026-08-01 起）
```
📊 上海房地产市场日报
📅 数据日期：YYYY-MM-DD

🏗️ 一手房成交情况

✅ 当日签约：X套 / X㎡
📐 套均面积：X㎡/套
🏢 可售住宅：X套

🏘️ 二手房成交情况

✅ 当日签约：X套 / X㎡
📐 套均面积：X㎡/套
📋 挂牌套数：X套

📰 楼市回顾

（marketReview 原始文本）

📈 数据看板：
https://sebastianhua.github.io/fangdi-monitor/

📋 数据表格：
https://docs.qq.com/smartsheet/DTnNsSXVoc21TbkhF
```
- 一手&二手统一"当日签约"；千分位；面积带㎡；套均 2 位小数；可售/挂牌单位均为"套"
- 章节标题独立成行，数据行 ✅ 前缀分行；看板/表格标题与 URL 分行
- 楼市回顾**不清洗**，保留官网原始措辞
- ⚠️ 日报文件**仅含标准数据**，任何特殊说明/异常解释/回补备注一律单独发梦比鱿鱼丝

## 环境与工具坑
- 🚨 **微信发送必须用 Python311**（2026-08-09）：PATH 中 `python` = WorkBuddy 托管 3.13.12，**无 pywin32** → `ModuleNotFoundError: win32gui`。正确解释器：`C:\Users\huaxi\AppData\Local\Programs\Python\Python311\python.exe`
- ⚠️ Git Bash 的 `/tmp` ≠ Windows Python 的 `C:\tmp`，临时脚本要写进工作区目录
- ⚠️ **mcporter 传中文/换行 JSON**：只能用 Python `subprocess.run([...,'mcporter.cmd','call','tencent-docs','smartsheet.xxx','--args',json.dumps(args,ensure_ascii=False)],encoding='utf-8')` 列表传参；Node `execFileSync(shell:true)` 吞引号、`--args "$(cat /tmp/x.json)"` 读不到文件
- ⚠️ `data/fangdi_data_YYYY-MM-DD.json` 备份被 .gitignore 忽略，git add 会报错 → 只 add `data/fangdi_data.json` + 日报 md

## GitHub 推送
- ✅ **2026-08-14 起改用 SSH 通道（关键）**：HTTPS(443) 长期 `Connection reset` + 内嵌 PAT(`ghp_BcTS`) 已失效 → 改用 SSH。`git remote set-url origin "git@github.com:SebastianHUA/fangdi-monitor.git"`。SSH key 已生成 `~/.ssh/id_ed25519`（公钥 `ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIKvQULeoIvpFZMG/fRrGhagSbSUBX640Kwbh0MRv7UZY workbuddy-claw`，已加 GitHub 账户）。22 端口通、`ssh -T git@github.com` 认证成功。
- 正常流程：`git stash -u` → `git pull origin main --rebase` → `git stash pop` → add/commit/push
- 💡 **报错语义**：`! [rejected] (fetch first)` = 认证+网络正常只是落后远端 → 正常 pull rebase 即可；只有 `Connection reset` / 443 超时才考虑 REST 兜底
- ⚠️ **rebase 冲突 `data/fangdi_data.json`**：远端 `origin/main` 的该文件是**权威完整版（48条 6-27~8-13）**，本地旧 commit 多为截断/早期数据 → 一律 `git checkout --ours` 取远端完整版，勿取本地旧 commit
- ⚠️ **rebase 冲突 `index.html`（看板修复）**：本地 commit 的 canvas `height:320px` 修复 + `./chart.umd.min.js` 本地引用是**要上线**的 → `git checkout --theirs` 保留本地修复版
- ⚠️ **rebase 冲突取向**：`git checkout --theirs` 在 rebase 中指**正在应用的本地 commit**（与 merge 相反）；`--ours` 指已合并的 HEAD/远端。解完校验 JSON 可解析、index.html 含 height:320px
- 🚨 **未跟踪文件挡 rebase**：`.workbuddy/memory/*`、`*.bak` 等会被 checkout 覆盖 → 先 `mv` 到 `/c/temp/` 再 rebase，完再移回（记忆文件必须保留）

## 通用规范
- ❌ 禁止手动改 `fangdi_data.json`（例外：①自动化失败且能从腾讯文档取正确值；②23:50 一手房失败时用楼市回顾回补）
- ⭐ **默认工作日志（强约定，2026-08-12 主人明确指定）**：以后只要说"工作日志"，一律指腾讯文档 smartsheet `DTkZDSWpxbWVUa1NN` sheet `NxtEWi`（链接 https://docs.qq.com/smartsheet/DTkZDSWpxbWVUa1NN）。字段=日期毫秒时间戳(上海00:00) + 工作内容 text 多行序号列表；先查后追加（同天追加不替换，不覆盖原有）；更新后附该链接。
  - ⚠️ 区分：`.workbuddy/memory/YYYY-MM-DD.md` 是助手自身执行日志，不是主人的工作日志；主人说"记录我的工作/记到工作日志"一律写腾讯文档这个表。
- 微信通知：纯数据日报发梦比鱿鱼丝 + 沈胄磊；异常/特殊说明**只发梦比鱿鱼丝**
- Trade 页面数据可能为 0 → 优先用首页数据
- 月度/年度视图 = 累计值（❌不除以天数）

## 已知永久缺口
- **2026-08-06 二手房数据**：08-07 当日 07:00 任务未运行，页面只展示昨日数据，已无法补采
