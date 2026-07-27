# fangdi-monitor 项目记忆

## 关键配置
- CDP Proxy 路径：`C:\Users\huaxi\WorkBuddy\Claw\cdp_proxy.js`（端口 3456）
- Chrome 远程调试端口：9222
- 腾讯文档 file_id: DTnNsSXVoc21TbkhF, sheet_id: 0g5JQL

## 重要发现
- fangdi.com.cn 检测 Headless Chrome，返回空页面。必须使用 visible Chrome + `--disable-blink-features=AutomationControlled`
- Chrome 150+ 要求 PUT 方法调用 `/json/new` API（不能用 GET）
- 认购公示页面直接打开会被重定向到首页，需要从首页导航才能正常加载
- 腾讯文档字段名与本地数据字段名不完全一致（如"套数（套）"vs"套数"等）

## 自动化任务
- 认购公示数据每日更新（07:15 执行），automation ID: 1783602458859
