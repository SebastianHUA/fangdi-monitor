// 上海房地产数据监测 - CDP Proxy 抓取脚本（最终版 v2.1）
// 功能：通过CDP Proxy抓取一手房/二手房成交数据 + 可售/挂牌数据
// 依赖：无（使用curl调用CDP Proxy API）
// 用法：node fangdi_cdp_proxy_scraper.js [--mode=newhouse|secondhand|all]

const https = require('https');
const http = require('http');
const fs = require('fs');

// ========== 配置 ==========
const CDP_PROXY = 'http://localhost:3456';
let targetId = null;

// 命令行参数解析
const args = process.argv.slice(2);
let mode = 'all';

if (args.includes('--mode=newhouse')) {
    mode = 'newhouse';
} else if (args.includes('--mode=secondhand')) {
    mode = 'secondhand';
} else if (args.includes('--mode=all')) {
    mode = 'all';
}

console.log(`[配置] 运行模式: ${mode}`);
console.log(`[配置] CDP Proxy: ${CDP_PROXY}`);

// ========== CDP Proxy API 工具函数 ==========

function apiCall(endpoint, method = 'GET', body = null) {
    return new Promise((resolve, reject) => {
        const url = `${CDP_PROXY}${endpoint}`;
        const options = {
            method: method,
            headers: body ? {'Content-Type': 'application/json'} : {}
        };
        
        const req = http.request(url, options, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                try {
                    resolve(JSON.parse(data));
                } catch (e) {
                    resolve(data);
                }
            });
        });
        
        req.on('error', reject);
        
        if (body) {
            req.write(typeof body === 'string' ? body : JSON.stringify(body));
        }
        
        req.end();
    });
}

async function createTab(url) {
    console.log(`  [CDP] 创建新tab: ${url}`);
    const result = await apiCall('/new', 'POST', url);
    targetId = result.targetId;
    console.log(`  ✅ Tab已创建: ${targetId}`);
    
    // 等待页面加载
    await wait(8000);
    
    return targetId;
}

async function evalJS(expression) {
    const result = await apiCall(`/eval?target=${targetId}`, 'POST', expression);
    // CDP Proxy返回格式: {value: '...'}
    if (result && result.value !== undefined) {
        return result.value;
    }
    return result;
}

function wait(ms) {
    return new Promise(r => setTimeout(r, ms));
}

async function closeTab() {
    if (targetId) {
        console.log(`  [CDP] 关闭tab: ${targetId}`);
        await apiCall(`/close?target=${targetId}`);
        targetId = null;
    }
}

// ========== 数据抓取函数 ==========

// 1. 抓取首页数据（当日签约、可售套数、挂牌套数）
async function fetchHomePageData() {
    console.log('\n[1/2] 抓取首页数据（当日签约/可售/挂牌）...');
    
    await createTab('https://www.fangdi.com.cn/index.html');
    
    // 提取页面文本（用于获取"签约套数"）
    const textResult = await evalJS('document.body.innerText');
    let text = '';
    if (typeof textResult === 'object' && textResult.value) {
        text = textResult.value;
    } else if (typeof textResult === 'string') {
        text = textResult;
    }
    
    // 提取HTML中的数据（用于获取"可售套数"和"挂牌套数"）
    const htmlData = await evalJS(`
        (function() {
            // 查找包含"全市"的span
            const citySpan = document.querySelector('.district.all_district');
            if (!citySpan || !citySpan.textContent.includes('全市')) {
                return {success: false, error: '未找到全市span'};
            }
            
            // 获取父元素
            const parent = citySpan.parentElement;
            
            // 查找所有包含<i>的span
            const spans = parent.querySelectorAll('span');
            
            const data = {};
            spans.forEach((span) => {
                const is = span.querySelectorAll('i');
                if (is.length >= 2) {
                    // 判断是哪个类型（一手房/普通住宅/二手房）
                    const text = span.previousElementSibling ? span.previousElementSibling.textContent : '';
                    
                    // 更简单的方法：按位置判断
                    // 第一个span是一手房，第二个是普通住宅，第三个是二手房
                }
            });
            
            // 更简单：直接按索引获取
            const allSpans = Array.from(parent.children);
            let houseSpan = null;
            let secondHandSpan = null;
            
            for (let child of allSpans) {
                const is = child.querySelectorAll('i');
                if (is.length >= 2) {
                    const prevText = child.previousElementSibling ? child.previousElementSibling.textContent : '';
                    if (prevText.includes('一手房') || !houseSpan) {
                        houseSpan = child;
                    }
                    if (prevText.includes('二手房') || !secondHandSpan) {
                        secondHandSpan = child;
                    }
                }
            }
            
            // 备用：直接获取第2、4个span（一手房和二手房）
            const dataSpans = Array.from(parent.querySelectorAll('span')).filter(s => s.querySelectorAll('i').length >= 2);
            
            if (dataSpans.length >= 3) {
                const houseIs = dataSpans[0].querySelectorAll('i');
                const secondHandIs = dataSpans[2].querySelectorAll('i');
                
                return {
                    success: true,
                    newHouseUnits: houseIs[0].textContent,
                    newHouseArea: houseIs[1].textContent,
                    secondHandCount: secondHandIs[0].textContent,
                    secondHandArea: secondHandIs[1].textContent
                };
            }
            
            return {success: false, error: '未找到数据span'};
        })()
    `);
    
    const result = {
        date: new Date().toISOString().split('T')[0],
        // 当日签约数据
        todaySignUnits: null,
        todaySignArea: null,
        // 可售数据
        newHouseAvailableUnits: null,
        newHouseAvailableArea: null,
        // 挂牌数据
        secondHandListingCount: null,
        secondHandListingArea: null
    };
    
    // 提取一手房当日签约套数
    const signUnitsMatch = text.match(/一手房签约套数：(\d+)套/);
    if (signUnitsMatch) {
        result.todaySignUnits = parseInt(signUnitsMatch[1]);
        console.log(`  ✅ 一手房签约套数: ${result.todaySignUnits} 套`);
    } else {
        console.log(`  ⚠️ 未找到一手房签约套数`);
    }
    
    // 提取一手房当日签约面积（㎡）
    const signAreaMatch = text.match(/一手房签约面积：([\d.]+)㎡/);
    if (signAreaMatch) {
        result.todaySignArea = Math.round(parseFloat(signAreaMatch[1]));
        console.log(`  ✅ 一手房签约面积: ${result.todaySignArea} ㎡`);
    } else {
        console.log(`  ⚠️ 未找到一手房签约面积`);
    }
    
    // 从HTML提取可售/挂牌数据
    if (htmlData && htmlData.success) {
        console.log(`  ✅ 从HTML提取到数据:`, htmlData);
        
        result.newHouseAvailableUnits = parseInt(htmlData.newHouseUnits);
        result.newHouseAvailableArea = parseFloat(htmlData.newHouseArea);
        result.secondHandListingCount = parseInt(htmlData.secondHandCount);
        result.secondHandListingArea = parseFloat(htmlData.secondHandArea);
        
        console.log(`  ✅ 一手房可售: ${result.newHouseAvailableUnits} 套`);
        console.log(`  ✅ 一手房可售面积: ${result.newHouseAvailableArea} 万㎡`);
        console.log(`  ✅ 二手房挂牌: ${result.secondHandListingCount} 笔`);
        console.log(`  ✅ 二手房挂牌面积: ${result.secondHandListingArea} 万㎡`);
    } else {
        console.log(`  ⚠️ 从HTML提取失败:`, htmlData ? htmlData.error : '未知错误');
    }
    
    await closeTab();
    
    return result;
}

// 2. 抓取一手房成交数据
async function fetchNewHouseData() {
    console.log('\n[2/2] 抓取一手房成交数据...');
    
    await createTab('https://www.fangdi.com.cn/trade/trade.html');
    
    const textResult = await evalJS('document.body.innerText');
    
    // 确保text是字符串
    let text = '';
    if (typeof textResult === 'object' && textResult.value) {
        text = textResult.value;
    } else if (typeof textResult === 'string') {
        text = textResult;
    } else {
        console.log(`  ⚠️ eval返回格式异常:`, textResult);
        await closeTab();
        return result;
    }
    
    const result = {
        date: new Date().toISOString().split('T')[0],
        todaySignUnits: null,
        todaySignArea: null,
        cumSaleUnits: null,
        cumSaleArea: null,
        newOpenUnits: null
    };
    
    // 提取今日成交套数
    const todayMatch = text.match(/今日共预[\/]出售各类商品房(\d+)套/);
    if (todayMatch) {
        result.todaySignUnits = parseInt(todayMatch[1]);
    }
    
    // 提取今日成交面积（万㎡ -> ㎡）
    const todayAreaMatch = text.match(/成交面积[\s\S]{0,50}?([\d.]+)万/);
    if (todayAreaMatch) {
        result.todaySignArea = Math.round(parseFloat(todayAreaMatch[1]) * 10000);
    }
    
    // 提取今年累计成交套数
    const cumMatch = text.match(/今年累计成交[\s\S]{0,200}?(\d+)套/);
    if (cumMatch) {
        result.cumSaleUnits = parseInt(cumMatch[1]);
    }
    
    // 提取今年累计成交面积（万㎡ -> ㎡）
    const cumAreaMatch = text.match(/累计成交面积[\s\S]{0,100}?([\d.]+)万/);
    if (cumAreaMatch) {
        result.cumSaleArea = Math.round(parseFloat(cumAreaMatch[1]) * 10000);
    }
    
    // 提取新开房源
    const newOpenMatch = text.match(/今日新开房源共计(\d+)个开盘单元/);
    if (newOpenMatch) {
        result.newOpenUnits = parseInt(newOpenMatch[1]);
    }
    
    console.log(`  ✅ 今日成交: ${result.todaySignUnits || '未提取'} 套`);
    console.log(`  ✅ 今日成交面积: ${result.todaySignArea || '未提取'} ㎡`);
    console.log(`  ✅ 今年累计: ${result.cumSaleUnits || '未提取'} 套`);
    console.log(`  ✅ 新开房源: ${result.newOpenUnits || '未提取'} 个单元`);
    
    await closeTab();
    
    return result;
}

// 3. 抓取二手房成交数据
async function fetchSecondHandData() {
    console.log('\n[2/2] 抓取二手房成交数据...');
    
    await createTab('https://www.fangdi.com.cn/old_house/old_house.html');
    
    const textResult = await evalJS('document.body.innerText');
    
    // 确保text是字符串
    let text = '';
    if (typeof textResult === 'object' && textResult.value) {
        text = textResult.value;
    } else if (typeof textResult === 'string') {
        text = textResult;
    } else {
        console.log(`  ⚠️ eval返回格式异常:`, textResult);
        await closeTab();
        return result;
    }
    
    const result = {
        date: new Date().toISOString().split('T')[0],
        yesterdaySaleCount: null,
        yesterdaySaleArea: null,
        cumSaleCount: null,
        cumSaleArea: null
    };
    
    // 提取昨日成交套数
    const yesterdayMatch = text.match(/昨日成交[\s\S]{0,50}?(\d+)套/);
    if (yesterdayMatch) {
        result.yesterdaySaleCount = parseInt(yesterdayMatch[1]);
    }
    
    // 提取昨日成交面积（万㎡ -> ㎡）
    const yesterdayAreaMatch = text.match(/昨日成交面积[\s\S]{0,50}?([\d.]+)万/);
    if (yesterdayAreaMatch) {
        result.yesterdaySaleArea = Math.round(parseFloat(yesterdayAreaMatch[1]) * 10000);
    }
    
    // 提取今年累计成交套数
    const cumMatch = text.match(/今年累计[\s\S]{0,200}?(\d+)套/);
    if (cumMatch) {
        result.cumSaleCount = parseInt(cumMatch[1]);
    }
    
    // 提取今年累计成交面积（万㎡ -> ㎡）
    const cumAreaMatch = text.match(/累计面积[\s\S]{0,100}?([\d.]+)万/);
    if (cumAreaMatch) {
        result.cumSaleArea = Math.round(parseFloat(cumAreaMatch[1]) * 10000);
    }
    
    console.log(`  ✅ 昨日成交: ${result.yesterdaySaleCount || '未提取'} 套`);
    console.log(`  ✅ 昨日成交面积: ${result.yesterdaySaleArea || '未提取'} ㎡`);
    
    await closeTab();
    
    return result;
}

// ========== 主函数 ==========
async function main() {
    console.log('======= 上海房地产数据监测系统 =======\n');
    
    const date = new Date().toISOString().split('T')[0];
    const result = {
        date: date,
        newHouse: null,
        secondHand: null,
        homePage: null
    };
    
    try {
        console.log(`\n======= 开始抓取 [模式: ${mode}] =======\n`);
        
        // 所有模式都需要首页数据
        result.homePage = await fetchHomePageData();
        
        if (mode === 'newhouse' || mode === 'all') {
            // 一手房数据从首页获取（当日签约数量）
            if (result.homePage) {
                result.newHouse = {
                    date: result.homePage.date,
                    todaySignUnits: result.homePage.todaySignUnits,
                    todaySignArea: result.homePage.todaySignArea,
                    availableUnits: result.homePage.newHouseAvailableUnits,
                    availableArea: result.homePage.newHouseAvailableArea,
                    // 以下数据暂时为空，如果需要可以从trade页面提取
                    cumSaleUnits: null,
                    cumSaleArea: null,
                    newOpenUnits: null
                };
                console.log(`\n  ✅ 一手房数据已从首页提取`);
                console.log(`  ✅ 签约套数: ${result.newHouse.todaySignUnits} 套`);
                console.log(`  ✅ 签约面积: ${result.newHouse.todaySignArea} ㎡`);
            }
        }
        
        if (mode === 'secondhand' || mode === 'all') {
            result.secondHand = await fetchSecondHandData();
            
            // 合并首页数据
            if (result.homePage) {
                result.secondHand.listingCount = result.homePage.secondHandListingCount;
                result.secondHand.listingArea = result.homePage.secondHandListingArea;
            }
            
            console.log(`\n  ✅ 二手房数据抓取完成`);
        }
        
        // 保存数据
        console.log('\n======= 保存数据 =======');
        
        const jsonFile = `fangdi_data_${date}.json`;
        fs.writeFileSync(jsonFile, JSON.stringify(result, null, 2), 'utf8');
        console.log(`✅ JSON 已保存: ${jsonFile}`);
        
        // 生成日报
        const report = generateReport(result);
        const reportFile = `fangdi_daily_report_${date}.md`;
        fs.writeFileSync(reportFile, report, 'utf8');
        console.log(`✅ 日报已保存: ${reportFile}`);
        
        console.log('\n======= ✅ 抓取完成 =======');
        console.log('\n📄 日报预览:');
        console.log(report.substring(0, 1000));
        
    } catch (e) {
        console.error('❌ 错误:', e.message);
        console.error(e.stack);
    } finally {
        // 确保关闭tab
        if (targetId) {
            await closeTab();
        }
    }
}

// ========== 生成日报 ==========
function generateReport(data) {
    const lines = [];
    lines.push(`# 上海房地产市场日报\n`);
    lines.push(`**日期**: ${data.date}\n`);
    lines.push(`**数据来源**: 上海网上房地产（www.fangdi.com.cn）\n`);
    lines.push(`**更新时间**: ${new Date().toLocaleString('zh-CN')}\n`);
    
    lines.push(`\n---\n`);
    
    if (data.newHouse) {
        lines.push(`\n## 一、一手房成交数据\n`);
        lines.push(`\n| 指标 | 数值 |`);
        lines.push(`|------|------|`);
        lines.push(`| 今日成交套数 | ${data.newHouse.todaySignUnits || '-'} 套 |`);
        lines.push(`| 今日成交面积 | ${data.newHouse.todaySignArea || '-'} ㎡ |`);
        lines.push(`| 今年累计成交 | ${data.newHouse.cumSaleUnits || '-'} 套 |`);
        lines.push(`| 今年累计成交面积 | ${data.newHouse.cumSaleArea || '-'} ㎡ |`);
        lines.push(`| 今日新开房源 | ${data.newHouse.newOpenUnits || '-'} 个单元 |`);
        lines.push(`| 可售套数 | ${data.newHouse.availableUnits || '-'} 套 |`);
        lines.push(`| 可售面积 | ${data.newHouse.availableArea || '-'} 万㎡ |`);
    }
    
    lines.push(`\n---\n`);
    
    if (data.secondHand) {
        lines.push(`\n## 二、二手房成交数据\n`);
        lines.push(`\n| 指标 | 数值 |`);
        lines.push(`|------|------|`);
        lines.push(`| 昨日成交套数 | ${data.secondHand.yesterdaySaleCount || '-'} 套 |`);
        lines.push(`| 昨日成交面积 | ${data.secondHand.yesterdaySaleArea || '-'} ㎡ |`);
        lines.push(`| 今年累计成交 | ${data.secondHand.cumSaleCount || '-'} 套 |`);
        lines.push(`| 今年累计成交面积 | ${data.secondHand.cumSaleArea || '-'} ㎡ |`);
        lines.push(`| 挂牌套数 | ${data.secondHand.listingCount || '-'} 笔 |`);
        lines.push(`| 挂牌面积 | ${data.secondHand.listingArea || '-'} 万㎡ |`);
    }
    
    lines.push(`\n---\n`);
    lines.push(`\n*本报告由 WorkBuddy 自动生成*\n`);
    
    return lines.join('\n');
}

// ========== 启动 ==========
main().catch(e => {
    console.error('❌ 未捕获错误:', e);
    process.exit(1);
});
