# 上海房地产抓取环境自愈脚本
# 作用：确保 Chrome 调试实例(9222) 与 CDP Proxy 存活，必要时自动拉起并做反爬预热
# 用法：powershell -ExecutionPolicy Bypass -File C:\Users\huaxi\WorkBuddy\Claw\ensure_scrape_env.ps1
#      可选参数 -ProxyPort 3456（默认 3456，测试时可用其他端口）
# 退出码：0 = 环境就绪；1 = Chrome 拉起失败；2 = CDP Proxy 拉起失败
# 说明：必须用 Start-Process 分离式拉起（Git Bash 下的 start "" 不可用，cmd start 经 bash 转义会失效）

param(
    [int]$ProxyPort = 3456
)

$ErrorActionPreference = "Continue"
$ChromePath = "C:\Program Files\Google\Chrome\Application\chrome.exe"
$UserDataDir = "C:\temp\chrome-debug"
$ProxyScript = "C:\Users\huaxi\WorkBuddy\Claw\cdp_proxy.js"
$chromeJustStarted = $false

function Test-Chrome {
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:9222/json/version" -TimeoutSec 3 -UseBasicParsing
        if ($r.StatusCode -eq 200) { return $r.Content }
    } catch { }
    return $null
}

function Test-Proxy {
    param([int]$Port)
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/" -TimeoutSec 3 -UseBasicParsing
        # CDP Proxy 根路径返回 200 即存活；它没有 /health 端点，不要用 /health 判断
        if ($r.StatusCode -eq 200) { return $true }
    } catch { }
    return $false
}

# ========== 第1步：确保 Chrome 调试实例(9222) 存活 ==========
$ver = Test-Chrome
if ($ver -ne $null) {
    Write-Output "[OK] Chrome 9222 本来就活着"
    if ($ver -match "HeadlessChrome") {
        Write-Output "[WARN] 当前是 Headless 模式！fangdi.com.cn 在 headless 下返回空文档，建议手工重启为有头模式"
    }
} else {
    Write-Output "[..] Chrome 9222 已死，正在用有头模式拉起"
    $ok = $false
    for ($i = 1; $i -le 3; $i++) {
        # 有头模式：不加 --headless；不使用 taskkill，避免杀掉主人正在用的浏览器窗口
        Start-Process -FilePath $ChromePath -ArgumentList `
            "--remote-debugging-port=9222", `
            "--user-data-dir=$UserDataDir", `
            "--no-first-run", `
            "--no-default-browser-check", `
            "about:blank"
        Start-Sleep -Seconds 8
        if ((Test-Chrome) -ne $null) { $ok = $true; break }
        Write-Output "[..] 第 $i 次拉起未成功，重试"
    }
    if (-not $ok) {
        Write-Output "[FAIL] Chrome 9222 拉起失败（重试3次）"
        exit 1
    }
    Write-Output "[OK] Chrome 9222 已拉起"
    $chromeJustStarted = $true
}

# ========== 第2步：确保 CDP Proxy 存活 ==========
if (Test-Proxy -Port $ProxyPort) {
    Write-Output "[OK] CDP Proxy $ProxyPort 本来就活着"
} else {
    Write-Output "[..] CDP Proxy $ProxyPort 已死，正在拉起"
    $ok = $false
    for ($i = 1; $i -le 3; $i++) {
        Start-Process -FilePath "node" -ArgumentList $ProxyScript, "$ProxyPort" -WindowStyle Hidden
        Start-Sleep -Seconds 3
        if (Test-Proxy -Port $ProxyPort) { $ok = $true; break }
        Write-Output "[..] 第 $i 次拉起未成功，重试"
    }
    if (-not $ok) {
        Write-Output "[FAIL] CDP Proxy $ProxyPort 拉起失败（重试3次）"
        exit 2
    }
    Write-Output "[OK] CDP Proxy $ProxyPort 已拉起"
}

# ========== 第3步：反爬预热（仅当刚拉起 Chrome 才需要）==========
# 新 profile / 冷启动首访 fangdi 会被反爬(HTTP 412)，需 reload 让挑战 cookie 落地
if ($chromeJustStarted) {
    Write-Output "[..] Chrome 刚拉起，执行反爬预热"
    try {
        $resp = Invoke-WebRequest -Uri "http://127.0.0.1:$ProxyPort/new?url=https://www.fangdi.com.cn/index.html" -Method POST -TimeoutSec 40 -UseBasicParsing
        $tid = (ConvertFrom-Json $resp.Content).targetId
        if ($tid) {
            Invoke-WebRequest -Uri "http://127.0.0.1:$ProxyPort/eval?target=$tid" -Method POST -Body "location.reload()" -TimeoutSec 20 -UseBasicParsing | Out-Null
            Start-Sleep -Seconds 15
            Invoke-WebRequest -Uri "http://127.0.0.1:$ProxyPort/close?target=$tid" -TimeoutSec 10 -UseBasicParsing | Out-Null
            Write-Output "[OK] 反爬预热完成（cookie 已落地）"
        } else {
            Write-Output "[WARN] 预热未取到 targetId，抓取脚本可能首次失败，将由脚本自身重试"
        }
    } catch {
        Write-Output "[WARN] 预热异常: $($_.Exception.Message)"
    }
} else {
    Write-Output "[OK] Chrome 本来就活着，cookie 已 warm，跳过预热"
}

Write-Output "[READY] 抓取环境就绪"
exit 0
