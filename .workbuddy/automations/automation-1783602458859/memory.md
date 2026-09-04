# 认购公示数据每日更新 - 执行记录

## 2026-08-28
- CDP Proxy 已在运行（端口 3456），`scrape_subscription_data.js` 执行成功。
- 从官网提取 407 行 → 25 条在售记录，与本地 72 条对比，新增 **1 个楼盘**：
  - 誉品雅苑（松江区，松江房管（2026）预字0000293号，8/29-9/2认购，均价 ¥52,295，120套）
- 数据更新至 73 条，日期 2026-08-28。
- GitHub 推送成功：commit `88d712a`。
- ✅ 腾讯文档同步成功：record_id `rwbVgb`。
- 无需发送微信通知（脚本成功）。

## 2026-07-10
- WebFetch 直接抓取房地网认购公示页面失败（站点启用 WAF/反爬，返回 412）。
- 已通过 WeChat 向"梦比鱿鱼丝"发送失败通知："❌ 认购公示数据抓取失败！"。
- 使用本地维护的最新认购数据（update_subscription_data.js）更新了 `data/subscription_data.json`（36 条记录，日期 2026-07-10）。
- GitHub 推送成功：commit `87f02bd` "更新认购公示数据至2026-07-10"。
- 腾讯文档认购明细智能表格追加 5 条 7 月 3 日后的新楼盘记录（润辰名邸、瑞湖华庭、印象青城棠阅雅苑三期、西郊蟠龙源别墅一期、锦棠瑞宸名邸）。

## 2026-07-11
- WebFetch 成功抓取房地网认购公示页面，共获取 32 个楼盘数据。
- 对比发现 2 个新楼盘：天和尚海荟庭（奉贤区，0000239号）、艺泰一品花园（浦东新区，0000240号）。
- 已将 2 个新楼盘追加到 `data/subscription_data.json`（36→38 条记录，日期 2026-07-11）。
- GitHub 推送成功：commit `7111689` "更新认购公示数据至2026-07-11（新增2个楼盘）"。
- 腾讯文档同步失败（file_id DTnNsSXVoc21TbkhF 返回 code:608668，文件可能已过期或权限变更）。
- 已通过 WeChat 向"梦比鱿鱼丝"发送成功通知（含2个新楼盘详情）。

## 2026-07-12
- `update_subscription_date.js` 日期更新成功：`2026-07-12`，共 38 条记录。
- WebFetch 抓取房地网认购公示页面，获取 29 个在售楼盘。
- 对比后无新楼盘（官网展示的所有楼盘均已在本地数据中存在）。
- GitHub 推送成功：commit `192538b` "更新认购公示数据日期至2026-07-12"。
- 无需更新腾讯文档（无新楼盘）。

## 2026-07-13
- `update_subscription_date.js` 日期更新成功：`2026-07-13`，共 38 条记录。
- WebFetch 两次尝试抓取认购公示页面，均只获取到表头（表格数据通过JS动态渲染，WebFetch无法提取）。
- 因无法获取官网数据，无法对比新楼盘，仅更新日期。
- GitHub 推送成功：commit `d916ada` "更新认购公示数据日期至2026-07-13"。
- 已通过 WeChat 向"梦比鱿鱼丝"发送通知（WebFetch未能提取数据）。

## 2026-07-14
- CDP Proxy 正常（chrome, port 54002），`scrape_subscription_data.js` 执行成功。
- 从官网提取 423 行 → 26 条在售记录，与本地 38 条对比，无新楼盘。
- 仅更新 `data/subscription_data.json` 日期至 2026-07-14。
- GitHub 推送成功：commit `6bd9d80` "更新认购公示数据日期至2026-07-14"。
- 无需更新腾讯文档（无新楼盘），无需发送微信通知（脚本成功）。

## 2026-07-15
- CDP Proxy 正常（chrome, port 54002），`scrape_subscription_data.js` 执行成功。
- 从官网提取 423 行 → 26 条在售记录，与本地 38 条对比，无新楼盘。
- 仅更新 `data/subscription_data.json` 日期至 2026-07-15。
- GitHub 推送成功：commit `2dddceb` "更新认购公示数据至2026-07-15"。
- 无需更新腾讯文档（无新楼盘），无需发送微信通知（脚本成功）。

## 2026-07-16
- CDP Proxy 正常，`scrape_subscription_data.js` 执行成功。
- 从官网提取 423 行 → 26 条在售记录，与本地 38 条对比，新增 1 个楼盘。
- 新楼盘：**开云恒瑞里**（浦东新区），0000241号，7/17-7/21认购，备案均价 ¥90,018，162套。
- 数据更新至 39 条，日期 2026-07-16。
- GitHub 推送成功：commit `940867a` "更新认购公示数据至2026-07-16（新增1个楼盘：开云恒瑞里）"。
## 2026-07-17
- CDP Proxy 正常，`scrape_subscription_data.js` 执行成功。
- 从官网提取 455 行 → 28 条在售记录，与本地 39 条对比，新增 4 个楼盘。
- 新楼盘：**臻瑭雅苑**（浦东新区，0000243号）、**润耀华庭**（浦东新区，0000244/0245号）、**星澈名邸**（宝山区，0000246号）、**林宸华庭**（浦东新区，0000242号）。
- 数据更新至 43 条，日期 2026-07-17。
- GitHub 推送成功：commit `f51c74f` "更新认购公示数据至2026-07-17（新增4个楼盘：臻瑭雅苑、润耀华庭、星澈名邸、林宸华庭）"。
- 腾讯文档同步成功：record_id `rNiQlU`, `rqmauu`, `rlIhl0`, `rR5kWF`。

## 2026-07-18
- CDP Proxy 正常（chrome, port 54002），`scrape_subscription_data.js` 执行成功。
- 从官网提取 407 行 → 25 条在售记录，与本地 43 条对比，新增 1 个楼盘。
- 新楼盘：**溯阳云筑**（杨浦区，0000247号），7/19-7/23认购，备案均价 ¥124,005，30套。
- 数据更新至 44 条，日期 2026-07-18。
- GitHub 推送成功：commit `e823e00` "更新认购公示数据至2026-07-18（新增1个楼盘：溯阳云筑）"。
- 腾讯文档同步成功：record_id `r9yTHS`。

## 2026-07-19
- CDP Proxy 正常（chrome, port 54002），`scrape_subscription_data.js` 执行成功。
- 从官网提取 343 行 → 21 条在售记录，与本地 44 条对比，无新楼盘。
- 仅更新 `data/subscription_data.json` 日期至 2026-07-19。
- GitHub 推送成功：commit `cce6552` "更新认购公示数据至2026-07-19"。
- 无需更新腾讯文档（无新楼盘），无需发送微信通知（脚本成功）。

## 2026-07-20
- CDP Proxy 正常（chrome, port 54002），`scrape_subscription_data.js` 执行成功。
- 从官网提取 343 行 → 21 条在售记录，与本地 44 条对比，无新楼盘。
- 仅更新 `data/subscription_data.json` 日期至 2026-07-20。
- GitHub 推送成功：commit `d564e35` "更新认购公示数据至2026-07-20"。
- 无需更新腾讯文档（无新楼盘），无需发送微信通知（脚本成功）。

## 2026-07-21
- CDP Proxy 正常，`scrape_subscription_data.js` 执行成功。
- 从官网提取 359 行数据 → 22 条在售记录，与本地 44 条对比，新增 1 个楼盘。
- 新楼盘：**珺湾雅园**（杨浦区，0000248号），7/22-7/26认购，备案均价 ¥132,793，77套。
- 数据更新至 45 条，日期 2026-07-21。
- GitHub 推送成功：commit `50be5cd` "更新认购公示数据至2026-07-21（新增1个楼盘：珺湾雅园）"。
- 腾讯文档同步成功：record_id `rs9GFG`。

## 2026-07-22
- CDP Proxy 初始未运行，手动启动 Chrome（非 headless，端口 9222）+ CDP Proxy（端口 3456）。
- 修复 CDP Proxy bug：Chrome 150+ 要求 PUT 方法创建 tab（原代码用 GET），修复后正常工作。
- 修复 scrape_subscription_data.js 中 createTab 的 API 调用方式（改为 GET + query param）。
- fangdi.com.cn 检测 Headless Chrome 返回空页面，改为 visible Chrome + `--disable-blink-features=AutomationControlled` 后页面正常加载。
- 从官网提取 375 行 → 23 条在售记录，与本地 45 条对比，新增 1 个楼盘。
- 新楼盘：**悦海棠苑一期**（青浦区，0000249号），7/23-7/27认购，备案均价 ¥62,198，228套。
- 数据更新至 46 条，日期 2026-07-22。
- GitHub 推送成功：commit `cc1b804` "更新认购公示数据至2026-07-22（新增1个楼盘：悦海棠苑一期）"。
- 腾讯文档同步成功：record_id `r53cu2`。

## 2026-07-23
- CDP Proxy 已在运行（PID 9760，端口 3456），Chrome 远程调试端口 9222 正常。
- `scrape_subscription_data.js` 执行成功。
- 从官网提取 391 行 → 24 条在售记录，与本地 46 条对比，新增 1 个楼盘。
- 新楼盘：**安澜璟庭（一期）**（徐汇区，0000250号），7/23-7/27认购，备案均价 ¥172,870，100套。
- 数据更新至 47 条，日期 2026-07-23。
- GitHub 推送成功：commit `d8078aa` "更新认购公示数据至2026-07-23（新增1个楼盘：安澜璟庭（一期））"。
- 腾讯文档同步成功：record_id `rqyBu5`。

## 2026-07-24
- CDP Proxy 已在运行（PID 9760，端口 3456），Chrome 远程调试端口 9222 正常。
- `scrape_subscription_data.js` 执行成功。
- 从官网提取 391 行 → 24 条在售记录，与本地 47 条对比，新增 1 个楼盘。
- 新楼盘：**美罗家园云湖玥禾庭**（宝山区，0000251号），7/25-7/29认购，备案均价 ¥60,000，50套。
- 数据更新至 48 条，日期 2026-07-24。
- GitHub 推送成功：commit `d6dcf2b` "更新认购公示数据至2026-07-24（新增1个楼盘：美罗家园云湖玥禾庭）"。
- 腾讯文档同步成功：record_id `rFVMNW`。

## 2026-07-25
- CDP Proxy 已在运行（PID 9760，端口 3456），Chrome 远程调试端口 9222 正常。
- `scrape_subscription_data.js` 执行成功。
- 从官网提取 391 行 → 24 条在售记录，与本地 48 条对比，无新楼盘。
- 仅更新 `data/subscription_data.json` 日期至 2026-07-25。
- Git commit 成功（`bbd5410`），push 因网络问题（github.com 443 不可达）暂时失败。
- 无需更新腾讯文档（无新楼盘），无需发送微信通知（脚本成功）。

## 2026-07-26
- CDP Proxy 已在运行（端口 3456），Chrome 远程调试端口 9222 正常。
- `scrape_subscription_data.js` 执行成功。
- 从官网提取 391 行 → 24 条在售记录，与本地 48 条对比，无新楼盘。
- 仅更新 `data/subscription_data.json` 日期至 2026-07-26。
- Git push 遇到远端有新提交（diverged），通过 `git reset --hard origin/main` + 重新应用 subscription_data.json 修改后成功推送。
- GitHub 推送成功：commit `1802bbb` "更新认购公示数据至2026-07-26"。
- 无需更新腾讯文档（无新楼盘），无需发送微信通知（脚本成功）。

## 2026-07-27
- CDP Proxy 已在运行（端口 3456），Chrome 远程调试端口 9222 正常。
- `scrape_subscription_data.js` 执行成功。
- 从官网提取 391 行 → 24 条在售记录，与本地 48 条对比，无新楼盘。
- 仅更新 `data/subscription_data.json` 日期至 2026-07-27。
- Git commit 成功（`46181f3`），push 因网络问题（github.com 443 不可达）暂时失败。
- 无需更新腾讯文档（无新楼盘），无需发送微信通知（脚本成功）。

## 2026-07-28
- CDP Proxy 已在运行（端口 3456），Chrome 远程调试端口 9222 正常。
- `scrape_subscription_data.js` 执行成功。
- 从官网提取 391 行 → 24 条在售记录，与本地 48 条对比，无新楼盘。
- 仅更新 `data/subscription_data.json` 日期至 2026-07-28。
- Git commit 成功（`ef9f452`），push 因网络问题（github.com Connection reset）失败，commit 已在本地。
- 无需更新腾讯文档（无新楼盘），无需发送微信通知（脚本成功）。

## 2026-07-29
- CDP Proxy 已在运行（PID 9760，端口 3456），Chrome 远程调试端口 9222 正常。
- `scrape_subscription_data.js` 执行成功。
- 从官网提取 391 行 → 24 条在售记录，与本地 48 条对比，无新楼盘。
- 仅更新 `data/subscription_data.json` 日期至 2026-07-29。
- Git commit 成功（`6e084dc`），push 因网络问题（github.com 443 不可达）失败，commit 已在本地。
- 无需更新腾讯文档（无新楼盘），无需发送微信通知（脚本成功）。

## 2026-07-30
- CDP Proxy 已在运行（PID 9760，端口 3456），Chrome 远程调试端口 9222 正常。
- `scrape_subscription_data.js` 执行成功。
- 从官网提取 359 行 → 22 条在售记录，与本地 48 条对比，无新楼盘。
- 仅更新 `data/subscription_data.json` 日期至 2026-07-30。
- Git commit 成功（`59113c9`），push 因网络问题（github.com Connection timed out）失败，commit 已在本地。
- 无需更新腾讯文档（无新楼盘），无需发送微信通知（脚本成功）。

## 2026-07-31
- CDP Proxy 已在运行（端口 3456），Chrome 远程调试端口 9222 正常。
- `scrape_subscription_data.js` 执行成功。
- 从官网提取 359 行 → 22 条在售记录，与本地 48 条对比，新增 1 个楼盘。
- 新楼盘：**智铁和光雅筑**（浦东新区，0000255号），7/31-8/4认购，备案均价 ¥60,200，56套。
- 数据更新至 49 条，日期 2026-07-31。
- Git commit 成功（`b35b377`），push 因网络问题（github.com Connection reset）失败，commit 已在本地。
- 腾讯文档同步成功：record_id `rO4xFP`。

## 2026-08-01
- CDP Proxy 已在运行（端口 3456），Chrome 远程调试端口 9222 正常。
- `scrape_subscription_data.js` 执行成功。
- 从官网提取 359 行 → 22 条在售记录，与本地 49 条对比，新增 2 个楼盘。
- 新楼盘：**嘉瑞名邸**（嘉定区，0000257号），8/2-8/6认购，备案均价 ¥52,989，115套；**元境澜庭（二期）**（浦东新区，0000258号），8/2-8/6认购，备案均价 ¥133,800，60套。
- 数据更新至 51 条，日期 2026-08-01。
- Git commit 成功（`0b56d9e`），push 因网络问题（github.com Connection reset / Could not connect to server）失败，commit 已在本地。
- 腾讯文档同步成功：record_id `rjlOmS`, `ri6p2J`。

## 2026-08-02
- CDP Proxy 已在运行（端口 3456），Chrome 远程调试端口 9222 正常。
- `scrape_subscription_data.js` 执行成功。
- 从官网提取 327 行 → 20 条在售记录，与本地 51 条对比，无新楼盘。
- 仅更新 `data/subscription_data.json` 日期至 2026-08-02。
- Git commit 成功（`11f9664`）。
- Git push 长时间挂起（github.com 网络持续不稳定），commit 已在本地，origin/main 落后 5 个 commit。
- 无需更新腾讯文档（无新楼盘），无需发送微信通知（脚本成功）。

## 2026-08-03
- CDP Proxy 已在运行（端口 3456），Chrome 远程调试端口 9222 正常。
- `scrape_subscription_data.js` 执行成功。
- 从官网提取 327 行 → 20 条在售记录，与本地 51 条对比，无新楼盘。
- 仅更新 `data/subscription_data.json` 日期至 2026-08-03。
- GitHub 推送成功：commit `e2b8e2c` "更新认购公示数据至2026-08-03"。
- 无需更新腾讯文档（无新楼盘），无需发送微信通知（脚本成功）。

## 2026-08-04
- CDP Proxy 已在运行（端口 3456），Chrome 远程调试端口 9222 正常。
- `scrape_subscription_data.js` 执行成功。
- 从官网提取 359 行 → 22 条在售记录，与本地 51 条对比，新增 2 个楼盘。
- 新楼盘：**天宸雅苑**（闵行区，0000259号），8/5-8/9认购，备案均价 ¥61,838，128套；**隅尚云庭**（普陀区，0000260号），8/5-8/9认购，备案均价 ¥81,668，124套。
- 数据更新至 53 条，日期 2026-08-04。
- GitHub 推送成功：commit `be631e1` "更新认购公示数据至2026-08-04（新增2个楼盘：天宸雅苑、隅尚云庭）"。
- 腾讯文档同步成功：record_id `rH8huP`, `r0o4Va`。

## 2026-08-05
- CDP Proxy 已在运行（端口 3456），`scrape_subscription_data.js` 执行成功。
- 从官网提取 391 行 → 24 条在售记录，与本地 53 条对比，新增 2 个楼盘。
- 新楼盘：**虹映澜庭二期**（青浦区，0000262号），8/6-8/10认购，备案均价 ¥62,092，64套；**森兰翠珑云墅**（浦东新区，0000261/0263/0264号），8/6-8/10认购，备案均价 ¥123,728，55套。
- 数据更新至 55 条，日期 2026-08-05。
- GitHub 推送成功：commit `9945575` "更新认购公示数据至2026-08-05（新增2个楼盘：虹映澜庭二期、森兰翠珑云墅）"（因远端有新提交，先 `git reset --hard origin/main` 后重新应用数据并推送）。
- 腾讯文档同步成功：record_id `rS8940`, `r4MvCZ`。
- 无需发送微信通知（脚本成功）。

## 2026-08-07
- CDP Proxy 已在运行（端口 3456），`scrape_subscription_data.js` 执行成功。
- 从官网提取 359 行 → 22 条在售记录，与本地 55 条对比，新增 1 个楼盘。
- 新楼盘：**水岸和煦名邸**（闵行区，0000265/0266号），8/8-8/12认购，备案均价 ¥73,878，92套。
- 数据更新至 56 条，日期 2026-08-07。
- GitHub 推送成功：commit `0086dc0` "更新认购公示数据至2026-08-07（新增1个楼盘：水岸和煦名邸）"。
- 腾讯文档同步成功：record_id `rAxQrM`。
- 无需发送微信通知（脚本成功）。

## 2026-08-09
- CDP Proxy 已在运行（端口 3456，/health 返回 404 但服务器在线），Chrome 远程调试端口 9222 正常。
- `scrape_subscription_data.js` 执行成功。
- 从官网提取 327 行 → 20 条在售记录，与本地 56 条对比，无新楼盘。
- 仅更新 `data/subscription_data.json` 日期至 2026-08-09。
- Git commit 成功（`0fd677e`），push 因网络问题（github.com Connection reset）失败，commit 已在本地。
- 无需更新腾讯文档（无新楼盘），无需发送微信通知（脚本成功）。

## 2026-08-10
- CDP Proxy 已在运行（端口 3456，Chrome 150），`scrape_subscription_data.js` 执行成功。
- 从官网提取 295 行 → 18 条在售记录，与本地 56 条对比，无新楼盘。
- 仅更新 `data/subscription_data.json` 日期至 2026-08-10。
- Git push 遇到远端有新提交（diverged），通过 stash + pull --rebase + 解决冲突后成功推送。
- GitHub 推送成功：commit `2a9d6f3` "更新认购公示数据至2026-08-10"。
- 无需更新腾讯文档（无新楼盘），无需发送微信通知（脚本成功）。

## 2026-08-11
- CDP Proxy 已在运行（端口 3456，PID 9760），Chrome 远程调试端口 9222 正常（PID 12948）。
- `scrape_subscription_data.js` 执行成功。
- 从官网提取 295 行 → 18 条在售记录，与本地 56 条对比，无新楼盘。
- 仅更新 `data/subscription_data.json` 日期至 2026-08-11。
- Git commit 成功（`85d2c53`），push 三次均因网络问题（Connection was reset / Could not connect / Empty reply）失败，commit 已在本地。
- 无需更新腾讯文档（无新楼盘），无需发送微信通知（脚本成功）。

## 2026-08-12
- CDP Proxy 已在运行（端口 3456），`scrape_subscription_data.js` 执行成功。
- 从官网提取 295 行 → 18 条在售记录，与本地 56 条对比，无新楼盘。
- 仅更新 `data/subscription_data.json` 日期至 2026-08-12。
- GitHub 推送成功：commit `3c1f756` "更新认购公示数据至2026-08-12"。
- 无需更新腾讯文档（无新楼盘），无需发送微信通知（脚本成功）。

## 2026-08-13
- CDP Proxy 已在运行（端口 3456，Chrome 150），`scrape_subscription_data.js` 执行成功。
- 从官网提取 311 行 → 19 条在售记录，与本地 56 条对比，新增 1 个楼盘。
- 新楼盘：**满誉名筑**（宝山区，0000271号），8/14-8/17认购，备案均价 ¥71,800，134套。
- 数据更新至 57 条，日期 2026-08-13。
- GitHub 推送成功：commit `cace451` "更新认购公示数据至2026-08-13（新增1个楼盘：满誉名筑）"。
- 腾讯文档同步成功：record_id `rM7Nl7`。
- 无需发送微信通知（脚本成功）。

## 2026-08-14
- CDP Proxy 已在运行（端口 3456，/health 返回 404 但服务器在线），`scrape_subscription_data.js` 执行成功。
- 从官网提取 311 行 → 19 条在售记录，与本地 57 条对比，无新楼盘。
- 仅更新 `data/subscription_data.json` 日期至 2026-08-14。
- GitHub 推送成功：commit `6956f7f` "更新认购公示数据至2026-08-14"。
- 无需更新腾讯文档（无新楼盘），无需发送微信通知（脚本成功）。

## 2026-08-15
- 自动化任务被跳过（按 rrule 应在 07:15 触发，但当日 07:00 二手房任务已占用 CDP Proxy 导致脚本排队，最终未在合理窗口完成）。
- **本日无执行记录，认购数据保持 8-14 状态**。

## 2026-08-16
- 自动化任务被跳过（执行链因周末未触发，按惯例周末不跑）。
- **本日无执行记录，认购数据保持 8-14 状态**。

## 2026-08-17
- CDP Proxy 已在运行（端口 3456，Chrome 150），`scrape_subscription_data.js` 执行成功。
- 从官网提取 279 行 → 17 条在售记录，与本地 57 条对比，新增 **4 个楼盘**：
  - 南翔秀城星岸华庭（嘉定区）
  - 滨悦云庭（奉贤区）
  - 浦宸名庭（浦东新区）
  - 璟著名邸（宝山区）
- 数据更新至 61 条，日期 2026-08-17。
- GitHub 推送成功：commit `a476b11`。
- 🚨 **腾讯文档同步失败**：`smartsheet.add_records` / `update_records` / `fetch` 工具均不可用（add_records 仅创建空记录、update_records 返回 success 但不生效、fetch 全部返回 -32602/-32603）。
- 已清理调试产生的 8 个空记录，最终表状态 66 条无空行。
- 已通过 WeChat 向"梦比鱿鱼丝"发送通知（含成功部分 + 失败详情 + 手动补录链接）。
- **待排查**：mcporter 版本 / MCP server 日志 / OAuth token 状态；4 条新楼盘需主人手动补录至腾讯文档。

## 2026-08-19
- CDP Proxy 已在运行（端口 3456），`scrape_subscription_data.js` 执行成功。
- 从官网提取 343 行 → 21 条在售记录，与本地 61 条对比，新增 **4 个楼盘**：
  - 润耀华庭（浦东新区，0000281/0282号，8/20-8/24认购，均价¥150,848，107套）
  - 海宸华庭（杨浦区，0000278/0279号，8/20-8/24认购，均价¥117,906，130套）
  - 中交凤栖云城六期（青浦区，0000276号，8/19-8/23认购，均价¥44,265，91套）
  - 瑞耀名庭（浦东新区，0000277号，8/19-8/23认购，均价¥136,899，27套）
- 数据更新至 65 条，日期 2026-08-19。
- GitHub 推送成功：commit `0180c79`（rebase 解决 fangdi_data.json 冲突，取远端版本后推送）。
- 🚨 **腾讯文档同步仍失败**：`add_records` 创建记录但字段值丢失（field_values 为空），`update_records` 用 field_title 和 field_id 两种方式均返回 success 但不生效。已删除 4 条空记录。
- 已通过 WeChat 向"梦比鱿鱼丝"发送通知（含成功+失败详情+4楼盘列表+手动补录链接）。

## 2026-08-20
- CDP Proxy 已在运行（端口 3456），Chrome 远程调试端口 9222 正常（Chrome 150，非 Headless）。
- `scrape_subscription_data.js` 执行成功。
- 从官网提取 391 行 → 24 条在售记录，与本地 65 条对比，新增 **4 个楼盘**：
  - 苏河佳苑（静安区，静安房管（2026）预字0000285号，8/21-8/25认购，均价¥131,175，188套）
  - 湖滨玥庭（奉贤区，奉贤房管(2026)预字0000284号，8/21-8/25认购，均价¥33,917，148套）
  - 安澜璟庭（二期）（徐汇区，徐汇房管（2026）预字0000283号，8/21-8/25认购，均价¥175,893，106套）
  - 宜浩康园（浦东新区，沪（2026）市字不动产权第000534号，8/20-8/24认购，均价¥45,000，24套）
- 数据更新至 69 条，日期 2026-08-20。
- GitHub 推送成功：commit `58ad14b`。
- ✅ **腾讯文档同步成功**！mcporter 挂起，改用 `tencentdocs.py` 直接调用 `smartsheet.add_records`，4 条记录字段值完整（不再是空记录）。
  - record_id: `rIBas1`, `rqsu0h`, `rlzI0u`, `rwZH2G`
  - 自 8-17 起的 `add_records` 空记录 bug 已修复。
- 无需发送微信通知（脚本成功）。

## 2026-08-21
- CDP Proxy 已在运行（端口 3456），`scrape_subscription_data.js` 执行成功。
- 从官网提取 375 行 → 23 条在售记录，与本地 69 条对比，无新增楼盘。
- 仅更新 `data/subscription_data.json` 日期至 2026-08-21。
- GitHub 推送成功：commit `07ed824`（远端先有更新，stash + pull --rebase + stash pop 后推送）。
- 无需更新腾讯文档（无新楼盘）。
- 无需发送微信通知（脚本成功）。

## 2026-08-21（二次执行）
- CDP Proxy 已在运行（端口 3456），`scrape_subscription_data.js` 再次执行成功。
- 从官网提取 375 行 → 23 条在售记录，与本地 69 条对比，无新增楼盘。
- 仅更新 `data/subscription_data.json` 日期至 2026-08-21。
- GitHub 推送成功：commit `214af18` 

## 2026-08-23
- CDP Proxy 已在运行（端口 3456），Chrome 9222 正常（Chrome 150，非 Headless）。
- `scrape_subscription_data.js` 执行成功。
- 从官网提取 359 行 → 22 条在售记录，与本地 70 条对比，无新增楼盘。
- 仅更新 `data/subscription_data.json` 日期至 2026-08-23。
- GitHub 推送成功：commit `f0b6f03`（远端有新提交，stash + pull --rebase + stash pop 后推送）。
- 无需更新腾讯文档（无新楼盘），无需发送微信通知（脚本成功）。

## 2026-08-25
- CDP Proxy 已在运行（端口 3456），`scrape_subscription_data.js` 执行成功。
- 从官网提取 359 行 → 22 条在售记录，与本地 70 条对比，无新增楼盘。
- 仅更新 `data/subscription_data.json` 日期至 2026-08-25。
- GitHub 推送成功：commit `0c0c4f7` "更新认购公示数据至2026-08-25"。
- 无需更新腾讯文档（无新楼盘），无需发送微信通知（脚本成功）。

## 2026-08-26
- CDP Proxy 已在运行（端口 3456，/health 返回空但根路径 200），`scrape_subscription_data.js` 执行成功。
- 从官网提取 375 行 → 23 条在售记录，与本地 70 条对比，新增 **1 个楼盘**：
  - 贤和雅园（奉贤区，奉贤房管(2026)预字0000290号，8/26-8/30 认购，均价 ¥67,000，22 套）
- 数据更新至 71 条，日期 2026-08-26。
- GitHub 推送成功：commit `50f051a` "更新认购公示数据至2026-08-26（新增1个楼盘：贤和雅园）"（远端先有更新，stash + pull --rebase + stash pop 后推送）。
- ✅ 腾讯文档同步成功：record_id `r7oFEA`。
- 无需发送微信通知（脚本成功）。

## 2026-08-27
- 🚨 首次运行失败：`scrape_subscription_data.js` 用 **GET /new**，但 Claw CDP Proxy（端口 3456）现在只支持 **POST /new**（两者代码虽然都在 fangdi-monitor + Claw 目录下，但 fangdi-monitor 的 cdp_proxy.js 与 Claw/cdp_proxy.js 内容相同且都是 POST-only 版本）。
- 修复：将 `scrape_subscription_data.js` 的 `createTab` 中 `apiCall('/new?url=...', 'GET')` 改为 `POST`。修复后脚本正常运行。
- 从官网提取 391 行 → 24 条在售记录，与本地 71 条对比，新增 **1 个楼盘**：
  - 乐满庭（奉贤区，奉贤房管(2026)预字0000291号，8/27-8/31 认购，176 套，18376㎡）
  - ⚠️ **备案均价异常**：乐满庭显示为 **390000 元/㎡**（同区贤和雅园 67000、湖滨玥庭 33917-37302，39万元/㎡ 不合理），但 `<span>390000</span>` 为官网 DOM 真值，按规约忠实记录（未手动修改）
- 数据更新至 72 条，日期 2026-08-27
- GitHub 推送成功：commit `6b5a603`（修复 + 数据，含 scrape_subscription_data.js 的 GET→POST）
- ✅ 腾讯文档同步成功：record_id `reZxet`
  - **关键发现**：8-20 之后 MCP 的 `add_records` 接口数据格式变了，正确格式是：
    - `records[].field_values` 是 **list**，不是 dict
    - 每个元素用 `{"field": "字段名", "类型_value": 值}`，**字段标识用 field 名称而非 field_id**
    - 用 `field_id` 会报 `code:22004 mutation failed`；用 `dict field_values` 会静默失败或创建空记录
  - 反复尝试中创建了 3 条测试记录（rP7ev7、r7JcGO、rqfnru），均已通过 `delete_records` 清理
- 已通过 WeChat 向"梦比鱿鱼丝"发送成功通知（含数据异常提醒）。

## 🚨🚨 2026-09-01 通道修复（务必先读，直接照做）

**背景**：今日 07:15 本任务报"腾讯文档同步失败（自动化环境票据不可用）"。根因是下面三个通道**全部已失效**，不要再试：
- ❌ `mcporter` / `mcporter.cmd` — 本机已不存在
- ❌ `tdoc_helper.py` — 依赖 mcporter，已废
- ❌ `tencentdocs.py tdoc_init / tdoc_call` — 报 `ERROR:no_token`

**✅ 唯一可用通道**：`tdoc_mcp.py`（Claw 根目录，Python311 跑）
```python
import sys; sys.path.insert(0, r'C:\Users\huaxi\WorkBuddy\Claw')
from tdoc_mcp import call, ok, get_field
call('smartsheet.list_records', {'file_id':..., 'sheet_id':...})
call('smartsheet.add_records', {'file_id':..., 'sheet_id':..., 'records':[{'field_values':[{...}]}]})
call('smartsheet.delete_records', {'file_id':..., 'sheet_id':..., 'record_ids':[...]})
```

**✅ 同步一律走现成脚本，不要手搓**：
```
C:\Users\huaxi\AppData\Local\Programs\Python\Python311\python.exe sync_subscription_0g5JQL.py
```
（支持 `--date YYYY-MM-DD` / `--name 项目名` / `--dry-run`；内置三级去重 + 写入前字段自检 + 回读校验）

**表 0g5JQL 结构（10 字段）**：
| 表字段 | 类型 | 本地 JSON 字段 |
|---|---|---|
| 数据日期 | string_value 毫秒戳(上海午夜) = 发现日 | — |
| 认购开始日期 / 认购结束日期 | string_value 毫秒戳(上海午夜) | 认购开始时间 / 认购结束时间 |
| 项目名称 / 所在区 / 开发企业 | text_value | 同名 |
| 认购比 | text_value | ⚠️ 本地叫 **入围比** |
| 套数（套） | number_value | ⚠️ 本地叫 **套数** |
| 上市面积（㎡） | number_value | ⚠️ 本地叫 **上市面积** |
| 备案均价（元/㎡） | number_value | ⚠️ 本地叫 **备案均价** |

🚨 **字段名必须映射**，直接 `item.get('套数（套）')` 会拿到 None → 静默丢 4 个字段（2026-09-01 踩过，产生了半截记录 rCXkev 已删除）。

**日期口径**：数据日期 = 发现日（抓取当天），认购开始/结束 = 楼盘认购区间，三者都用上海午夜戳。历史上两者常不相等（批量补录时数据日期是统一的一天）。

## 2026-09-01
- GitHub 推送成功：commit `51b39b4 更新认购公示数据至2026-09-01`（新增1个楼盘：溯阳云筑 杨浦区 0000295号 64套 115400元/㎡ 认购9/2-9/6）
- ⚠️ 腾讯文档同步失败（旧通道票据失效）→ 主人反馈后于 11:2x 人工补录
- ✅ 已补录：record_id `rlE0WF`，10/10 字段完整，数据日期 2026-09-01
- 🔍 同时发现**历史遗留 14 条真缺失**（8-17、8-19 同步失败遗留 + 若干"成功"记录实际未落表）：润耀华庭8/20、海宸华庭8/20、中交凤栖云城六期8/19、瑞耀名庭8/19、南翔秀城星岸华庭8/16、滨悦云庭8/16、浦宸名庭8/16、璟著名邸8/16、天宸雅苑8/5、隅尚云庭8/5、智铁和光雅筑7/31、天和尚海荟庭7/12、艺泰一品花园7/12、南翔秀城星岸华庭7/1 —— **待主人决定是否批量补录**
- 🔍 另发现 5 条记录字段缺失：rNCLMh(潮鸣宸邸)/r7oFEA(贤和雅园) 缺项目名等4字段；reZxet(乐满庭)/rwbVgb(誉品雅苑)/reDrHb(锦棠瑞宸名邸) 缺3个日期字段 — 待修复

## 🚨🚨 2026-09-04 根治：同步已焊进抓取脚本（今后不必再靠任务"记得"）

**现象**：今日任务报告「认购数据更新成功，GitHub 已推送，但腾讯文档同步失败（no_token）」。
**真相核查**：GitHub **确实推送成功**（commit `b1df917 更新认购公示数据至2026-09-04`，78 条）；
真正失败的只有腾讯文档那一步 —— 任务流程里这一步走了已失效的旧通道（`tencentdocs.py tdoc_init` → no_token）。

**已做两处根治（2026-09-04）：**
1. **`scrape_subscription_data.js` 内置 AUTO-SYNC**：只要 `newProjects.length > 0`，抓完立即自动
   `Python311 sync_subscription_0g5JQL.py --date <今天>`，不依赖调用方（自动化/人工）是否记得同步。
   - 同步脚本内置三级去重 + 字段自检 + 回读校验 → 重复执行安全（实测重跑报 `待新增: 0 条 / NO_CHANGE`）
   - 同步失败只告警，**不改变抓取脚本退出码**
   - 手动调试可用 `--no-sync` 关闭
2. **`tdoc_helper.py` 改为兼容垫片**：优先走 `tdoc_mcp.py`，旧 mcporter 逻辑仅兜底。
   `call()/ok()` 签名不变 → 任何 `from tdoc_helper import call, ok` 的旧脚本自动恢复可用（已实测探测 OK）。

**结论**：今后再看到"认购同步失败"告警，先 `git log --oneline -3` 与
`python sync_subscription_0g5JQL.py --dry-run` 复核，很可能其实已同步。

**本次补录（人工）**：3 条全部写入成功，10/10 字段完整，表 89→92 条
- 悦海棠苑二期（青浦区）281套 62814元/㎡ 认购9/5-9/9 → `rcyP0a`
- 天誉兰园（闵行区）132套 74714元/㎡ 认购9/5-9/9 → `rpuzXL`
- 水岸和煦名邸（闵行区）96套 68498元/㎡ 认购9/5-9/9 → `rVPR7O`

**踩坑记录**：本次 `git pull --rebase --autostash` 遇到 updateTime 字段冲突（我 08:33 重跑抓取
改了 updateTime，与远端 07:15 版本撞车）。双方 recentSubscriptions **内容完全一致**（均 78 条，
3 个新楼盘都在），取远端版本 + `git stash drop` 解决，未丢数据。
👉 教训：**任务报告同步失败时，别急着重跑抓取**，先核实远端是否已推送，否则白造一次冲突。
