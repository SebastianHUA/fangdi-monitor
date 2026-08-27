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
23:50一手房(本地+腾讯,不推GitHub); 07:00二手+回顾(本地+腾讯bwHrDx+GxaSD5+GitHub,发梦比鱿鱼丝+沈胄磊); 07:15认购; 17:00土地
fangdi_data.json必为数组按日期降序; 取最新用date精确匹配,禁取"最后一条"
⚠️禁止手动改fangdi_data.json(例外:①自动化失败且能从腾讯文档取正确值;②23:50一手房失败用回顾回补)

### 腾讯文档smartsheet通用约定
🚨add/update_records必用field_values数组: records:[{field_values:[{field,tvalue}]}]. 用fields对象=假成功只留日期auto_fill("只有日期无内容")
文本: text_value:{items:[{text,type:"text"}]} (type必须text非plain)
日期: string_value:"毫秒戳"; auto_fill=true列强填当前时间→历史日期先建内容再update
查list_records返回同构

### 腾讯文档 DTnNsSXVoc21TbkhF
bwHrDx(成交)/0g5JQL(认购)/GxaSD5(回顾,TS=UTC午夜)
bwHrDx字段带单位后缀(如"一手房成交面积（㎡）")

## 工作日志(强约定)
腾讯文档 smartsheet DTkZDSWpxbWVUa1NN sheet NxtEWi
字段: 日期毫秒戳(上海00:00)+工作内容text多行序号
先查后追加,同天不替换; 更新附链接
.workbuddy/memory/*.md是助手日志,非主人工作日志

## 微信日报格式
📊上海房地产市场日报/📅数据日期/🏗️一手房(✅当日签约X套/X㎡,📐套均,🏢可售)/🏘️二手(✅当日签约,📐套均,📋挂牌)/📰楼市回顾(不清洗)/📈看板URL/📋表格URL
纯数据发梦比鱿鱼丝+沈胄磊; 异常只发梦比鱿鱼丝

## 环境坑
微信/pywin32须Python311(托管3.13.12无pywin32)
mcporter传中文JSON用Python subprocess列表传参,禁Node execFileSync(吞引号)
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

## 土地市场监测
脚本 land_monitor_curl.py(需bs4,Python311)/update_sheet.py; 腾讯 NHsPBsupJrkx 是传统电子表格(非smartsheet),用sheet.insert_dimension+set_range_value
公告17:00后才上网→全量比对补录; set_range_value偶no_token→sleep重试
