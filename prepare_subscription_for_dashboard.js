// 添加认购楼盘数据到看板
// 功能：从 output/认购公示明细_*.csv 读取数据，添加到看板显示

const fs = require('fs');

// 读取最新的认购公示数据
const csvFile = 'output/认购公示明细_2026-06-28.csv';

if (!fs.existsSync(csvFile)) {
    console.log('[认购] 未找到认购公示数据文件');
    process.exit(0);
}

const csvContent = fs.readFileSync(csvFile, 'utf8');
const lines = csvContent.split('\n').filter(line => line.trim());

console.log(`[认购] 读取到 ${lines.length - 1} 条认购楼盘数据`);

// 解析CSV（简单解析，不考虑引号内的逗号）
const records = [];
for (let i = 1; i < lines.length; i++) {
    const fields = lines[i].split(',');
    if (fields.length >= 10) {
        records.push({
            date: fields[0],
            district: fields[1],
            projectName: fields[2],
            company: fields[3],
            subscribeStart: fields[4],
            subscribeEnd: fields[5],
            subscribeRatio: fields[6],
            units: parseInt(fields[7]),
            area: parseFloat(fields[8]),
            avgPrice: parseFloat(fields[9])
        });
    }
}

console.log(`[认购] 解析到 ${records.length} 条有效记录`);

// 按认购结束日期排序，取最近7天
const now = new Date();
const recentRecords = records.filter(r => {
    const endDate = new Date(r.subscribeEnd);
    const diffDays = (now - endDate) / (1000 * 60 * 60 * 24);
    return diffDays <= 7; // 最近7天
}).sort((a, b) => a.subscribeEnd > b.subscribeEnd ? 1 : -1);

console.log(`[认购] 最近7天有 ${recentRecords.length} 条认购楼盘`);

// 生成HTML表格行
const htmlRows = recentRecords.map(r => `
                <tr>
                    <td>${r.projectName}</td>
                    <td>${r.district}</td>
                    <td>${r.subscribeStart}</td>
                    <td>${r.subscribeEnd}</td>
                    <td>${r.units}</td>
                    <td>${r.avgPrice}</td>
                </tr>
`).join('');

console.log('\n[认购] HTML表格行:');
console.log(htmlRows);

// 保存到JSON供看板使用
const outputData = {
    date: new Date().toISOString().split('T')[0],
    recentSubscriptions: recentRecords
};

fs.writeFileSync('data/subscription_data.json', JSON.stringify(outputData, null, 2), 'utf8');
console.log(`\n[认购] ✅ 认购数据已保存: data/subscription_data.json`);
