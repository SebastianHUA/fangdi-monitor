// 认购公示数据抓取脚本 - 使用CDP Proxy
// 从 https://www.fangdi.com.cn/new_house/new_house_jjswlpgs.html 抓取认购公示数据
// 依赖：CDP Proxy 运行在 localhost:3456
// 用法：node scrape_subscription_data.js

const http = require('http');
const fs = require('fs');
const path = require('path');

const CDP_PROXY = 'http://127.0.0.1:3456';
const SUBSCRIPTION_URL = 'https://www.fangdi.com.cn/new_house/new_house_jjswlpgs.html';
const DATA_FILE = path.join(__dirname, 'data', 'subscription_data.json');

// 标准字段名（16个字段）
const FIELD_NAMES = [
    '项目名称', '所在区', '预售许可证号', '开发企业', '项目地址',
    '户型', '产品类型', '上市面积', '套数', '备案均价',
    '入围比', '认购地址', '认购开始时间', '认购结束时间',
    '认购联系电话', '区局监督电话'
];

let targetId = null;

// ========== CDP Proxy API 工具函数 ==========

function apiCall(endpoint, method = 'GET', body = null) {
    return new Promise((resolve, reject) => {
        const url = `${CDP_PROXY}${endpoint}`;
        const options = {
            method: method,
            headers: body ? { 'Content-Type': 'application/json' } : {}
        };
        const req = http.request(url, options, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                try { resolve(JSON.parse(data)); } catch (e) { resolve(data); }
            });
        });
        req.on('error', reject);
        req.setTimeout(30000, () => req.destroy(new Error('Request timeout')));
        if (body) { req.write(typeof body === 'string' ? body : JSON.stringify(body)); }
        req.end();
    });
}

async function createTab(url) {
    console.log(`  [CDP] 创建新tab: ${url}`);
    const result = await apiCall('/new', 'POST', url);
    targetId = result.targetId;
    console.log(`  ✅ Tab已创建: ${targetId}`);
    await wait(12000); // 等待页面加载+JS渲染
    return targetId;
}

// 等待页面包含特定文本
async function waitForContent(keyword, maxRetries = 5, intervalMs = 5000) {
    for (let i = 0; i < maxRetries; i++) {
        const text = await evalJS('document.body.innerText');
        const pageText = typeof text === 'string' ? text : (text && text.value ? text.value : '');
        if (pageText.includes(keyword)) {
            console.log(`  ✅ 页面内容已就绪（第${i + 1}次检查找到"${keyword}"）`);
            return true;
        }
        console.log(`  ⏳ 等待页面加载...（第${i + 1}次检查未找到"${keyword}"）`);
        await wait(intervalMs);
    }
    return false;
}

async function evalJS(expression) {
    const result = await apiCall(`/eval?target=${targetId}`, 'POST', expression);
    if (result && result.value !== undefined) { return result.value; }
    return result;
}

function wait(ms) { return new Promise(r => setTimeout(r, ms)); }

async function closeTab() {
    if (targetId) {
        try { await apiCall(`/close?target=${targetId}`); } catch (e) {}
        targetId = null;
    }
}

// ========== 主逻辑 ==========

async function main() {
    console.log('=== 认购公示数据抓取（CDP Proxy） ===');

    // 1. 检查CDP Proxy
    try {
        const health = await apiCall('/health');
        console.log(`  ✅ CDP Proxy: ${health.status}`);
    } catch (e) {
        console.error('  ❌ CDP Proxy未运行！请先启动: node cdp_proxy.js');
        process.exit(1);
    }

    // 2. 打开认购公示页面
    console.log('\n[1/4] 打开认购公示页面...');

    // 方案A：直接打开认购公示页面
    await createTab(SUBSCRIPTION_URL);

    // 检查是否被重定向到首页
    let currentUrl = await evalJS('window.location.href');
    let urlStr = typeof currentUrl === 'string' ? currentUrl : JSON.stringify(currentUrl);
    console.log(`  当前URL: ${urlStr}`);

    if (urlStr.includes('index.html') || !urlStr.includes('jjswlpgs')) {
        console.log('  ⚠️ 被重定向到首页，尝试在当前tab中导航...');
        // 在当前tab中用JS导航到认购公示页面
        await evalJS(`window.location.href = '${SUBSCRIPTION_URL}'`);
        await wait(12000);

        currentUrl = await evalJS('window.location.href');
        urlStr = typeof currentUrl === 'string' ? currentUrl : JSON.stringify(currentUrl);
        console.log(`  导航后URL: ${urlStr}`);
    }

    // 等待认购公示数据加载
    const contentReady = await waitForContent('区局监督电话', 6, 5000);
    if (!contentReady) {
        console.error('  ❌ 页面未加载认购公示数据');

        // 方案B：尝试通过首页点击导航
        console.log('\n  尝试方案B：通过首页导航...');
        await closeTab();
        await createTab('https://www.fangdi.com.cn/index.html');
        await wait(5000);

        // 点击"一手房"菜单下的"认购公示"链接
        await evalJS(`
            var links = document.querySelectorAll('a');
            for (var i = 0; i < links.length; i++) {
                if (links[i].href && links[i].href.includes('jjswlpgs')) {
                    links[i].click();
                    break;
                }
            }
        `);
        await wait(10000);

        const ready2 = await waitForContent('区局监督电话', 4, 5000);
        if (!ready2) {
            console.error('  ❌ 方案B也失败');
            const debugText = await evalJS('document.body.innerText');
            const text = typeof debugText === 'string' ? debugText : (debugText && debugText.value ? debugText.value : '');
            console.error('  页面文本前500字符:', text.substring(0, 500));
            await closeTab();
            process.exit(1);
        }
    }

    // 3. 提取页面文本
    console.log('\n[2/4] 提取页面数据...');
    const pageTextRaw = await evalJS('document.body.innerText');
    const pageText = typeof pageTextRaw === 'string' ? pageTextRaw :
        (pageTextRaw && pageTextRaw.value ? pageTextRaw.value : '');

    if (!pageText || pageText.length < 100) {
        console.error('  ❌ 页面文本为空或太短');
        await closeTab();
        process.exit(1);
    }

    // 4. 关闭tab
    await closeTab();

    // 5. 解析文本数据
    console.log('\n[3/4] 解析数据...');

    // 找到"项目名称"的位置（数据开始的标志）
    const startMarker = '区局监督电话';
    const markerIdx = pageText.indexOf(startMarker);
    if (markerIdx === -1) {
        console.error('  ❌ 未找到数据起始标记"区局监督电话"');
        console.error('  页面文本前300字符:', pageText.substring(0, 300));
        process.exit(1);
    }

    // 从标记后开始提取数据行
    const dataText = pageText.substring(markerIdx + startMarker.length).trim();
    const lines = dataText.split('\n').map(l => l.trim()).filter(l => l.length > 0);

    console.log(`  提取到 ${lines.length} 行数据`);

    // 每16行组成一条记录
    const FIELD_COUNT = FIELD_NAMES.length;
    const records = [];
    for (let i = 0; i + FIELD_COUNT <= lines.length; i += FIELD_COUNT) {
        const record = {};
        for (let j = 0; j < FIELD_COUNT; j++) {
            record[FIELD_NAMES[j]] = lines[i + j];
        }
        // 验证：认购开始时间应该是日期格式
        if (record['认购开始时间'] && /^\d{4}-\d{2}-\d{2}$/.test(record['认购开始时间'])) {
            // 转换数值字段
            record['上市面积'] = parseFloat(String(record['上市面积']).replace(/[^0-9.]/g, '')) || record['上市面积'];
            record['套数'] = parseInt(String(record['套数']).replace(/[^0-9]/g, '')) || record['套数'];
            record['备案均价'] = parseInt(String(record['备案均价']).replace(/[^0-9]/g, '')) || record['备案均价'];
            records.push(record);
        }
    }

    console.log(`  ✅ 解析成功: ${records.length} 条记录`);
    if (records.length > 0) {
        console.log(`  最新记录: ${records[0]['项目名称']} (${records[0]['所在区']}) - 认购开始: ${records[0]['认购开始时间']}`);
        console.log(`  最旧记录: ${records[records.length - 1]['项目名称']} - 认购开始: ${records[records.length - 1]['认购开始时间']}`);
    }

    if (records.length === 0) {
        console.error('  ❌ 未解析出有效记录');
        console.error('  前50行数据:', lines.slice(0, 50).join('\n'));
        process.exit(1);
    }

    // 6. 与现有数据对比
    console.log('\n[4/4] 与现有数据对比...');

    let existingData = { date: '', recentSubscriptions: [] };
    if (fs.existsSync(DATA_FILE)) {
        existingData = JSON.parse(fs.readFileSync(DATA_FILE, 'utf8'));
    }

    const existingPermits = new Set(
        existingData.recentSubscriptions.map(r => r['预售许可证号'])
    );

    const newProjects = records.filter(r => {
        const permit = r['预售许可证号'];
        return permit && !existingPermits.has(permit);
    });

    console.log(`  现有记录: ${existingData.recentSubscriptions.length} 条`);
    console.log(`  官网记录: ${records.length} 条`);
    console.log(`  新增楼盘: ${newProjects.length} 条`);

    if (newProjects.length > 0) {
        console.log('\n  📢 新增楼盘列表:');
        newProjects.forEach((p, i) => {
            console.log(`    ${i + 1}. ${p['项目名称']} (${p['所在区']}) - ${p['预售许可证号']} - 认购: ${p['认购开始时间']}`);
        });

        // 追加新楼盘
        existingData.recentSubscriptions = [...newProjects, ...existingData.recentSubscriptions];

        // 按认购开始时间降序排序
        existingData.recentSubscriptions.sort((a, b) => {
            const dateA = new Date(a['认购开始时间'] || '2000-01-01');
            const dateB = new Date(b['认购开始时间'] || '2000-01-01');
            return dateB - dateA;
        });
    }

    // 更新日期
    const now = new Date();
    const dateStr = now.getFullYear() + '-' +
        String(now.getMonth() + 1).padStart(2, '0') + '-' +
        String(now.getDate()).padStart(2, '0');
    existingData.date = dateStr;
    existingData.updateTime = now.toISOString();

    // 保存
    fs.writeFileSync(DATA_FILE, JSON.stringify(existingData, null, 2), 'utf8');
    console.log(`\n✅ 数据已保存: ${DATA_FILE}`);
    console.log(`  总计: ${existingData.recentSubscriptions.length} 条`);
    console.log(`  日期: ${dateStr}`);

    if (newProjects.length > 0) {
        console.log(`\n📢 发现 ${newProjects.length} 个新楼盘！`);
        // 输出JSON供自动化任务使用
        console.log('\n===NEW_PROJECTS_JSON===');
        console.log(JSON.stringify(newProjects, null, 2));
        console.log('===END_JSON===');
    } else {
        console.log('\n📋 无新增楼盘，仅更新日期。');
    }
}

main().catch(err => {
    console.error('❌ 执行失败:', err.message);
    closeTab().then(() => process.exit(1));
});
