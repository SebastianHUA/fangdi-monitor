// 上海房地产数据监测 - 完整版（参考fetch_fangdi_daily_monitor.js）
const WebSocket = require('ws');
const http = require('http');
const fs = require('fs');
const path = require('path');

const CDP_PORT = 9222;
let msgId = 1;

function getTabs() {
    return new Promise((resolve, reject) => {
        const req = http.get(`http://localhost:${CDP_PORT}/json`, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                try { resolve(JSON.parse(data).filter(t => t.type === 'page')); }
                catch (e) { reject(e); }
            });
        }).on('error', reject);
    });
}

function sendWS(ws, method, params = {}) {
    return new Promise((resolve) => {
        const id = msgId++;
        const handler = (data) => {
            const resp = JSON.parse(data);
            if (resp.id === id) { ws.off('message', handler); resolve(resp); }
        };
        ws.on('message', handler);
        ws.send(JSON.stringify({ id, method, params }));
    });
}

function evalJS(ws, expr, timeout = 15000) {
    return new Promise((resolve) => {
        const id = msgId++;
        const timer = setTimeout(() => { ws.off('message', h); resolve(null); }, timeout);
        const h = (data) => {
            const resp = JSON.parse(data);
            if (resp.id === id) {
                clearTimeout(timer);
                ws.off('message', h);
                if (resp.result && resp.result.result) resolve(resp.result.result.value);
                else resolve(null);
            }
        };
        ws.on('message', h);
        ws.send(JSON.stringify({
            id, method: 'Runtime.evaluate',
            params: { expression: expr, returnByValue: true, awaitPromise: true }
        }));
    });
}

function wait(ms) { return new Promise(r => setTimeout(r, ms)); }

// ========== 主抓取逻辑 ==========
async function main() {
    console.log('='.repeat(60));
    console.log('上海房地产数据监测系统');
    console.log('='.repeat(60));
    
    const date = new Date().toISOString().split('T')[0];
    console.log(`\n📅 日期: ${date}`);
    
    // 连接CDP
    console.log('\n[准备] 连接Chrome CDP...');
    let tabs;
    try { tabs = await getTabs(); }
    catch (e) {
        console.error('\n❌ 无法连接Chrome！');
        console.error('请先运行 "启动Chrome远程调试.bat"');
        process.exit(1);
    }
    
    if (tabs.length === 0) { console.error('\n❌ 没有可用标签页！'); process.exit(1); }
    console.log(`   ✅ 找到 ${tabs.length} 个标签页`);
    
    const ws = new WebSocket(tabs[0].webSocketDebuggerUrl);
    await new Promise((r, rej) => { ws.on('open', r); ws.on('error', rej); });
    console.log('   ✅ WebSocket已连接');
    
    await sendWS(ws, 'Page.enable');
    await sendWS(ws, 'Runtime.enable');
    
    try {
        const result = { date, newHouse: null, secondHand: null };
        
        // ========== 1. 一手房数据 ==========
        console.log('\n[1/2] 抓取一手房数据...');
        await sendWS(ws, 'Page.navigate', { url: 'https://www.fangdi.com.cn/trade/trade.html?t=' + Date.now() });
        await wait(5000);
        
        // 使用outerHTML提取（更可靠）
        const newHouseHtml = await evalJS(ws, 'document.documentElement.outerHTML', 10000);
        
        const newHouseData = {
            todaySaleCount: 0,
            todaySaleArea: 0,
            newOpenCount: 0
        };
        
        if (newHouseHtml) {
            const todayMatch = newHouseHtml.match(/今日共预\/出售各类商品房(\d+)套[\s\S]{0,300}?面积([\d.]+)万/);
            if (todayMatch) {
                newHouseData.todaySaleCount = parseInt(todayMatch[1]);
                newHouseData.todaySaleArea = parseFloat(todayMatch[2]);
            }
            
            const newOpenMatch = newHouseHtml.match(/今日新开房源共计(\d+)个/);
            if (newOpenMatch) newHouseData.newOpenCount = parseInt(newOpenMatch[1]);
        }
        
        result.newHouse = newHouseData;
        console.log(`   ✅ 今日成交: ${newHouseData.todaySaleCount} 套`);
        console.log(`   ✅ 今日面积: ${newHouseData.todaySaleArea} 万㎡`);
        
        // ========== 2. 二手房数据 ==========
        console.log('\n[2/2] 抓取二手房数据...');
        await sendWS(ws, 'Page.navigate', { url: 'https://www.fangdi.com.cn/old_house/old_house.html?t=' + Date.now() });
        await wait(5000);
        
        const secondHandData = await evalJS(ws, `
            (function() {
                const text = document.body.innerText;
                
                // 提取"昨日二手房成交套数"
                const taoShuMatch = text.match(/昨日二手房成交套数:\\s*(\\d+)/);
                const mianJiMatch = text.match(/昨日二手房成交面积:\\s*([\\d,.]+)/);
                
                return {
                    yesterdaySaleCount: taoShuMatch ? parseInt(taoShuMatch[1]) : 0,
                    yesterdaySaleArea: mianJiMatch ? parseFloat(mianJiMatch[1].replace(',', '')) : 0
                };
            })()
        `, 20000);
        
        result.secondHand = secondHandData;
        console.log(`   ✅ 昨日成交: ${secondHandData.yesterdaySaleCount} 套`);
        console.log(`   ✅ 昨日面积: ${secondHandData.yesterdaySaleArea} ㎡`);
        
        // ========== 3. 保存数据 ==========
        console.log('\n[保存] 保存数据...');
        const dataDir = path.join(__dirname, 'data');
        if (!fs.existsSync(dataDir)) fs.mkdirSync(dataDir, { recursive: true });
        
        const jsonPath = path.join(dataDir, `fangdi_${date}.json`);
        fs.writeFileSync(jsonPath, JSON.stringify(result, null, 2), 'utf8');
        console.log(`   ✅ 已保存: ${jsonPath}`);
        
        // ========== 4. 输出摘要 ==========
        console.log('\n' + '='.repeat(60));
        console.log('✅ 数据抓取完成！');
        console.log('='.repeat(60));
        console.log(`\n📊 数据摘要:`);
        console.log(`   一手房今日成交: ${result.newHouse.todaySaleCount} 套`);
        console.log(`   二手房昨日成交: ${result.secondHand.yesterdaySaleCount} 套`);
        console.log(`\n📄 JSON文件: ${jsonPath}`);
        
    } catch (e) {
        console.error('\n❌ 错误:', e.message);
        throw e;
    } finally { ws.close(); }
}

main().catch(e => { console.error('\n执行失败:', e); process.exit(1); });
