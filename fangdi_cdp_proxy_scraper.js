// 上海房地产数据监测 - CDP Proxy 抓取脚本（最终版 v2.1）
// 功能：通过CDP Proxy抓取一手房/二手房成交数据 + 可售/挂牌数据
// 依赖：无（使用curl调用CDP Proxy API）
// 用法：node fangdi_cdp_proxy_scraper.js [--mode=newhouse|secondhand|all]

const https = require('https');
const http = require('http');
const fs = require('fs');

// ========== 配置 ==========
const CDP_PROXY = 'http://127.0.0.1:3456';
let targetId = null;

// 测试模式（不保存数据）
let TEST_MODE = false;

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

if (args.includes('--test')) {
    TEST_MODE = true;
    console.log(`[配置] ⚠️ 测试模式已启用 - 不保存数据`);
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
    // 【修复】CDP Proxy 的 /new 仅从 query 参数读取 url，不解析 body；
    // 必须用 /new?url=... 形式，否则 tab 停在 about:blank 导致抓取全 0
    const result = await apiCall(`/new?url=${encodeURIComponent(url)}`, 'POST');
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
    const signUnitsMatch = text.match(/签约套数[：:]\s*(\d+)/) || text.match(/一手房[成交签约]{2}套数[：:]\s*(\d+)/);
    if (signUnitsMatch) {
        result.todaySignUnits = parseInt(signUnitsMatch[1]);
        console.log(`  ✅ 一手房签约套数: ${result.todaySignUnits} 套`);
    } else {
        console.log(`  ⚠️ 未找到一手房签约套数，原始文本前500字符: ${text.substring(0, 500)}`);
    }
    
    // 提取一手房当日签约面积（㎡）
    const signAreaMatch = text.match(/签约面积[：:]\s*([\d.]+)/) || text.match(/一手房[成交签约]{2}面积[：:]\s*([\d.]+)/);
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

// 2. 抓取一手房成交数据（从交易统计页面）
async function fetchNewHouseData() {
    console.log('\n[2/2] 抓取一手房成交数据（trade页面）...');
    
    await createTab('https://www.fangdi.com.cn/trade/trade.html');
    
    // 提取页面文本
    const textResult = await evalJS('document.body.innerText');
    
    let text = '';
    if (typeof textResult === 'object' && textResult.value !== undefined) {
        text = String(textResult.value);
    } else if (typeof textResult === 'string') {
        text = textResult;
    } else {
        console.log(`  ⚠️ eval返回格式异常:`, textResult);
        await closeTab();
        return null;
    }
    
    const result = {
        date: new Date().toISOString().split('T')[0],
        todaySignUnits: null,
        todaySignArea: null,
        availableUnits: null,
        availableArea: null,
        cumSaleUnits: null,
        cumSaleArea: null,
        newOpenUnits: null
    };
    
    // 提取今日成交套数
    const todayMatch = text.match(/今日共预[\/]出售各类商品房(\d+)套/);
    if (todayMatch) {
        result.todaySignUnits = parseInt(todayMatch[1]);
        console.log(`  ✅ 今日成交套数: ${result.todaySignUnits} 套`);
    }
    
    // 提取今日成交面积（万㎡ -> ㎡）
    const todayAreaMatch = text.match(/成交面积[\s\S]{0,50}?([\d.]+)万/);
    if (todayAreaMatch) {
        result.todaySignArea = Math.round(parseFloat(todayAreaMatch[1]) * 10000);
        console.log(`  ✅ 今日成交面积: ${result.todaySignArea} ㎡`);
    }
    
    // 提取今年累计成交套数
    const cumMatch = text.match(/今年累计成交[\s\S]{0,200}?(\d+)套/);
    if (cumMatch) {
        result.cumSaleUnits = parseInt(cumMatch[1]);
        console.log(`  ✅ 今年累计: ${result.cumSaleUnits} 套`);
    }
    
    // 提取今年累计成交面积（万㎡ -> ㎡）
    const cumAreaMatch = text.match(/累计成交面积[\s\S]{0,100}?([\d.]+)万/);
    if (cumAreaMatch) {
        result.cumSaleArea = Math.round(parseFloat(cumAreaMatch[1]) * 10000);
        console.log(`  ✅ 累计面积: ${result.cumSaleArea} ㎡`);
    }
    
    // 提取新开房源
    const newOpenMatch = text.match(/今日新开房源共计(\d+)个开盘单元/);
    if (newOpenMatch) {
        result.newOpenUnits = parseInt(newOpenMatch[1]);
        console.log(`  ✅ 新开房源: ${result.newOpenUnits} 个单元`);
    }
    
    // 提取可售套数（从页面文本）
    const availableMatch = text.match(/可售[住宅套数]*[：:]\s*([\d,]+)/) || text.match(/可售[\s\S]{0,50}?([\d,]+)套/);
    if (availableMatch) {
        result.availableUnits = parseInt(availableMatch[1].replace(/,/g, ''));
        console.log(`  ✅ 可售套数: ${result.availableUnits} 套`);
    }
    
    // 🆕 提取楼市回顾（从首页，比 trade.html 更稳定）
    try {
        const reviewIndex = text.indexOf('楼市回顾');
        if (reviewIndex > -1) {
            console.log(`  [调试] 首页找到"楼市回顾"，位置: ${reviewIndex}`);
            const afterTitle = text.indexOf('\n', reviewIndex);
            if (afterTitle > -1) {
                let reviewContent = text.substring(afterTitle).trim();
                const lines = reviewContent.split('\n');
                let resultLines = [];
                
                for (let i = 0; i < Math.min(lines.length, 10); i++) {
                    const line = lines[i].trim();
                    if (!line || line.includes('今日楼市') || line.includes('昨日楼市')) continue;
                    if (line.includes('17:00')) break;
                    resultLines.push(line);
                    if (resultLines.length >= 5) break;
                }
                
                if (resultLines.length > 0) {
                    result.marketReview = resultLines.join('\n');
                    console.log(`  ✅ 楼市回顾（首页）: ${result.marketReview.substring(0, 80)}...`);
                } else {
                    console.log(`  ⚠️ 首页未找到楼市回顾内容`);
                }
            }
        } else {
            console.log(`  ⚠️ 首页未找到"楼市回顾"区块`);
        }
    } catch (e) {
        console.log(`  ⚠️ 提取楼市回顾异常: ${e.message}`);
    }
    
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
    
    // 提取昨日成交套数 - 多种匹配模式
    const yesterdayPatterns = [
        /昨日成交[\s\S]{0,100}?(\d+)套/,
        /昨日[\s\S]{0,50}?(\d+)套/,
        /成交套数[：:][\s\S]{0,20}?(\d+)/
    ];
    for (const pattern of yesterdayPatterns) {
        const match = text.match(pattern);
        if (match) {
            result.yesterdaySaleCount = parseInt(match[1]);
            console.log(`  ✅ 匹配到昨日成交套数: ${result.yesterdaySaleCount} (模式: ${pattern})`);
            break;
        }
    }
    
    // 提取昨日成交面积 - 多种匹配模式（支持万㎡和㎡）
    const yesterdayAreaPatterns = [
        /昨日成交面积[\s\S]{0,100}?([\d.]+)万/,  // 万㎡格式
        /昨日成交面积[\s\S]{0,100}?([\d.]+)㎡/,   // 直接㎡格式
        /成交面积[：:][\s\S]{0,50}?([\d.]+)万/,
        /成交面积[：:][\s\S]{0,50}?([\d.]+)㎡/,
        /昨日[\s\S]{0,100}?([\d.]+)万㎡/,
        /昨日[\s\S]{0,100}?([\d.]+)㎡/
    ];
    for (const pattern of yesterdayAreaPatterns) {
        const match = text.match(pattern);
        if (match) {
            const value = parseFloat(match[1]);
            // 判断是万㎡还是㎡
            if (pattern.source.includes('万')) {
                result.yesterdaySaleArea = Math.round(value * 10000);
            } else {
                result.yesterdaySaleArea = Math.round(value);
            }
            console.log(`  ✅ 匹配到昨日成交面积: ${result.yesterdaySaleArea} ㎡ (原始: ${value}, 模式: ${pattern})`);
            break;
        }
    }
    
    // 提取今年累计成交套数 - 多种匹配模式
    const cumPatterns = [
        /今年累计成交[\s\S]{0,200}?(\d+)套/,
        /累计成交[\s\S]{0,200}?(\d+)套/,
        /今年[\s\S]{0,100}?(\d+)套/
    ];
    for (const pattern of cumPatterns) {
        const match = text.match(pattern);
        if (match) {
            result.cumSaleCount = parseInt(match[1]);
            console.log(`  ✅ 匹配到累计成交套数: ${result.cumSaleCount} (模式: ${pattern})`);
            break;
        }
    }
    
    // 提取今年累计成交面积 - 多种匹配模式
    const cumAreaPatterns = [
        /累计成交面积[\s\S]{0,200}?([\d.]+)万/,
        /累计面积[\s\S]{0,200}?([\d.]+)万/,
        /成交面积[\s\S]{0,200}?([\d.]+)万/,
        /累计[\s\S]{0,100}?([\d.]+)万㎡/
    ];
    for (const pattern of cumAreaPatterns) {
        const match = text.match(pattern);
        if (match) {
            result.cumSaleArea = Math.round(parseFloat(match[1]) * 10000);
            console.log(`  ✅ 匹配到累计成交面积: ${result.cumSaleArea} ㎡ (原始: ${match[1]}万㎡)`);
            break;
        }
    }
    
    // 调试：如果未提取到面积，输出页面文本前500字符
    if (!result.yesterdaySaleArea) {
        console.log(`  ⚠️ 未提取到昨日成交面积，页面文本前500字符:`);
        console.log(text.substring(0, 500));
    }
    
    console.log(`  ✅ 昨日成交: ${result.yesterdaySaleCount || '未提取'} 套`);
    console.log(`  ✅ 昨日成交面积: ${result.yesterdaySaleArea || '未提取'} ㎡`);
    
    await closeTab();
    
    return result;
}

// ========== 新增：抓取楼市回顾 ==========
async function fetchMarketReview() {
    console.log('\n======= 抓取楼市回顾 =======\n');
    
    const result = {
        date: new Date().toISOString().split('T')[0],
        marketReview: null
    };
    
    try {
        // 1. 打开交易统计页面
        console.log(`  [调试] 正在打开交易统计页面...`);
        await createTab('https://www.fangdi.com.cn/trade/trade.html');
        
        // 2. 等待页面加载（增加到5秒，确保动态内容渲染完毕）
        await wait(5000);
        
        // 3. 提取楼市回顾（带重试）
        console.log(`  [调试] 正在提取楼市回顾...`);
        
        for (let attempt = 0; attempt < 3; attempt++) {
            if (attempt > 0) {
                console.log(`  [重试] 第${attempt + 1}次尝试...`);
                await wait(3000); // 额外等待3秒
            }
            
            const pageText = await evalJS('document.body.innerText');
            
            if (!pageText || typeof pageText !== 'string') {
                console.log(`  ⚠️ 第${attempt + 1}次：页面文本提取失败`);
                continue;
            }
            
            // 方法1：精确匹配"楼市回顾"
            let reviewIndex = pageText.indexOf('楼市回顾');
            
            // 方法2：如果indexOf失败，尝试正则匹配（兼容可能的编码问题）
            if (reviewIndex === -1) {
                const regexMatch = pageText.match(/今日新开房源共计(\d+)个开盘单元/);
                if (regexMatch) {
                    // 从匹配位置往前找，提取完整内容
                    const matchPos = pageText.indexOf('今日新开房源共计');
                    // 尝试提取从"今日楼市"开始到"17:00"之间的内容
                    const todayReviewIdx = pageText.indexOf('今日楼市');
                    if (todayReviewIdx > -1 && todayReviewIdx < matchPos) {
                        reviewIndex = todayReviewIdx;
                        console.log(`  [备用] 通过"今日楼市"定位，位置: ${reviewIndex}`);
                    }
                }
            }
            
            if (reviewIndex > -1) {
                console.log(`  [调试] 找到楼市回顾内容，位置: ${reviewIndex}`);
                
                let reviewContent = pageText.substring(reviewIndex).trim();
                
                console.log(`  [调试] 楼市回顾原始文本（前300字符）: ${reviewContent.substring(0, 300)}`);
                
                // 按行分割，提取楼市回顾的行
                const lines = reviewContent.split('\n');
                let resultLines = [];
                
                for (let i = 0; i < Math.min(lines.length, 10); i++) {
                    const line = lines[i].trim();
                    
                    // 跳过空行和标题行
                    if (!line || line === '楼市回顾' || line.includes('今日楼市') || line.includes('昨日楼市')) {
                        continue;
                    }
                    
                    // 如果遇到"17:00"提示，停止提取
                    if (line.includes('17:00')) {
                        break;
                    }
                    
                    resultLines.push(line);
                    
                    // 最多取5行
                    if (resultLines.length >= 5) break;
                }
                
                console.log(`  [调试] 提取的行数: ${resultLines.length}`);
                
                if (resultLines.length > 0) {
                    result.marketReview = resultLines.join('\n');
                    console.log(`  ✅ 楼市回顾: ${result.marketReview}`);
                    break; // 成功提取，退出重试循环
                } else {
                    console.log(`  ⚠️ 第${attempt + 1}次：未找到楼市回顾内容行`);
                }
            } else {
                console.log(`  ⚠️ 第${attempt + 1}次：未找到"楼市回顾"区块`);
                console.log(`  [调试] 页面文本长度: ${pageText.length}, 前200字符: ${pageText.substring(0, 200)}`);
            }
        }
        
        if (!result.marketReview) {
            console.log(`  ❌ 3次尝试均失败，无法提取楼市回顾`);
        }
        
        await closeTab();
        
    } catch (e) {
        console.log(`  ❌ 抓取楼市回顾失败: ${e.message}`);
        try { await closeTab(); } catch (_) {}
    }
    
    return result;
}

// ========== 主函数 ==========
async function main() {
    console.log('======= 上海房地产数据监测系统 =======\n');
    
    // 支持 --date 参数（格式：--date=2026-07-03）
    let date = new Date().toISOString().split('T')[0];
    const dateArg = args.find(arg => arg.startsWith('--date='));
    if (dateArg) {
        date = dateArg.split('=')[1];
        console.log(`[配置] 使用指定日期: ${date}`);
    }
    
    const result = {
        date: date,
        newHouse: null,
        secondHand: null,
        homePage: null,
        marketReview: null  // 新增：楼市回顾
    };
    
    try {
        console.log(`\n======= 开始抓取 [模式: ${mode}] =======\n`);
        
        // 所有模式都需要首页数据
        result.homePage = await fetchHomePageData();
        
        // 🆕 从首页提取楼市回顾（所有模式都可用，比 trade.html 更稳定）
        if (result.homePage && result.homePage.marketReview) {
            result.marketReview = result.homePage.marketReview;
            console.log(`\n  ✅ 楼市回顾已从首页提取`);
        }
        
        if (mode === 'newhouse' || mode === 'all') {
            // 【修复】优先使用首页数据（更准确，因为trade页面是动态渲染）
            if (result.homePage) {
                result.newHouse = {
                    date: result.homePage.date,
                    todaySignUnits: result.homePage.todaySignUnits,
                    todaySignArea: result.homePage.todaySignArea,
                    availableUnits: result.homePage.newHouseAvailableUnits,
                    availableArea: result.homePage.newHouseAvailableArea,
                    cumSaleUnits: null,
                    cumSaleArea: null,
                    newOpenUnits: null
                };
                console.log(`\n  ✅ 一手房数据已从首页提取`);
                console.log(`  ✅ 成交套数: ${result.newHouse.todaySignUnits} 套`);
                console.log(`  ✅ 成交面积: ${result.newHouse.todaySignArea} ㎡`);
            }
            
            // 如果首页没有获取到，尝试从trade页面获取（备用）
            if (!result.newHouse) {
                const newHouseData = await fetchNewHouseData();
                if (newHouseData) {
                    result.newHouse = newHouseData;
                    console.log(`\n  ✅ 一手房数据已从trade页面提取（备用）`);
                    console.log(`  ✅ 成交套数: ${result.newHouse.todaySignUnits} 套`);
                    console.log(`  ✅ 成交面积: ${result.newHouse.todaySignArea} ㎡`);
                }
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
        
        // 抓取楼市回顾（所有模式都运行，但先检查首页是否已有）
        if (!result.marketReview) {
            const reviewData = await fetchMarketReview();
            if (reviewData && reviewData.marketReview) {
                result.marketReview = reviewData.marketReview;
            }
        } else {
            console.log(`  ℹ️ 楼市回顾已从首页获取，跳过 trade.html`);
        }
        
        // 转换数据格式为看板期望的嵌套格式
        // 【修复】只添加实际抓取到的数据，避免覆盖其他字段
        const formattedResult = {
            date: result.date
        };
        
        // 只有在抓取了一手房数据时才添加 newHouse 字段
        if (result.newHouse && (result.newHouse.todaySignUnits !== undefined || result.newHouse.availableUnits !== undefined)) {
            formattedResult.newHouse = {
                todaySignUnits: result.newHouse?.todaySignUnits ?? result.newHouse?.saleCount ?? 0,
                todaySignArea: result.newHouse?.todaySignArea ?? result.newHouse?.saleArea ?? 0,
                availableUnits: result.newHouse?.availableUnits ?? result.newHouse?.newHouseAvailableUnits ?? 0
            };
        }
        
        // 只有在抓取了二手房数据时才添加 secondHand 字段
        if (result.secondHand && (result.secondHand.yesterdaySaleCount !== undefined || result.secondHand.listingCount !== undefined)) {
            formattedResult.secondHand = {
                yesterdaySaleCount: result.secondHand?.yesterdaySaleCount ?? result.secondHand?.saleCount ?? 0,
                yesterdaySaleArea: result.secondHand?.yesterdaySaleArea ?? result.secondHand?.saleArea ?? 0,
                listingCount: result.secondHand?.listingCount ?? result.secondHand?.secondHandListingCount ?? 0
            };
        }
        
        // 🆕 楼市回顾始终保存（如果有的话）
        if (result.marketReview) {
            formattedResult.marketReview = result.marketReview;
        }
        
        // 生成日报（测试模式和正常模式都生成）
        const report = generateReport(result);
        
        // 保存数据（数组格式，保留历史数据）
        if (!TEST_MODE) {
            console.log("======== 保存数据 =========");
            
            // 生成数组格式的数据文件（保留历史数据）
            const dataFile = "data/fangdi_data.json";
            let allData = [];
            
            // 读取现有数据
            if (fs.existsSync(dataFile)) {
                try {
                    const existingData = JSON.parse(fs.readFileSync(dataFile, "utf8"));
                    // 兼容处理：如果现有数据是单个对象，转为数组
                    if (Array.isArray(existingData)) {
                        allData = existingData;
                    } else {
                        allData = [existingData];
                    }
                } catch (e) {
                    console.log("⚠️ 读取现有数据失败，创建新数组");
                    allData = [];
                }
            }
            
            // 检查是否已存在该日期的数据（避免重复）
            const existingIndex = allData.findIndex(d => d.date === result.date);
            if (existingIndex >= 0) {
                // 【修复】合并数据，而不是整体替换
                allData[existingIndex] = {
                    ...allData[existingIndex],  // 保留现有数据
                    ...formattedResult           // 用新数据覆盖
                };
                console.log(`✅ 更新现有数据: ${result.date}`);
            } else {
                // 追加新数据
                allData.push(formattedResult);
                console.log(`✅ 追加新数据: ${result.date}`);
            }
            
            // 按日期降序排序（最新的在前）
            allData.sort((a, b) => b.date > a.date ? 1 : -1);
            
            // 保存到文件
            fs.writeFileSync(dataFile, JSON.stringify(allData, null, 2), "utf8");
            console.log(`✅ 数据已保存: ${dataFile} (共 ${allData.length} 条记录)`);
            
            // 同时保存带日期的文件（用于备份）
            const jsonFile = `data/fangdi_data_${date}.json`;
            fs.writeFileSync(jsonFile, JSON.stringify(formattedResult, null, 2), "utf8");
            console.log(`✅ 备份已保存: ${jsonFile}`);
            
            // 保存日报
            const reportFile = `data/fangdi_daily_report_${date}.md`;
            fs.writeFileSync(reportFile, report, 'utf8');
            console.log(`✅ 日报已保存: ${reportFile}`);
        } else {
            console.log("\n⚠️ 测试模式 - 不保存数据");
            console.log("模拟保存:");
            console.log(`  - 数据文件: data/fangdi_data.json`);
            console.log(`  - 备份文件: data/fangdi_data_${date}.json`);
            console.log(`  - 日报文件: data/fangdi_daily_report_${date}.md`);
        }
        
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
