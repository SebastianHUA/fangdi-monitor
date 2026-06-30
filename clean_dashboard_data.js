// 清理并重建看板数据文件
// 问题：
// 1. 第一条记录格式错误（包含"提取时间"等字段）
// 2. 06-27 数据全是 null
// 3. 06-28/29 的 newHouse.todaySaleCount 显示为 undefined（实际有数据）

const fs = require('fs');

// 读取原始数据文件
const files = ['fangdi_data_2026-06-28.json', 'fangdi_data_2026-06-29.json'];

const allData = [];

for (let file of files) {
    if (!fs.existsSync(file)) {
        console.log(`[清理] 文件不存在: ${file}`);
        continue;
    }
    
    const data = JSON.parse(fs.readFileSync(file, 'utf8'));
    
    // 补全一手房数据（从marketReview）
    if ((!data.newHouse || !data.newHouse.todaySignUnits || data.newHouse.todaySignUnits === 0) && data.marketReview) {
        const match = data.marketReview.match(/预\/出售各类商品房(\d+)套/);
        const areaMatch = data.marketReview.match(/面积([\d.]+)万平方米/);
        
        if (match) {
            if (!data.newHouse) data.newHouse = {};
            data.newHouse.todaySignUnits = parseInt(match[1]);
            data.newHouse.todaySignArea = areaMatch ? Math.round(parseFloat(areaMatch[1]) * 10000) : 0;
            console.log(`[清理] ${data.date} 补全一手房数据: ${data.newHouse.todaySignUnits}套`);
        }
    }
    
    allData.push(data);
}

// 按日期排序
allData.sort((a, b) => a.date > b.date ? 1 : -1);

console.log(`[清理] 共 ${allData.length} 条有效记录`);

// 保存
const outputFile1 = 'data/fangdi_data.json';
const outputFile2 = 'docs/data/fangdi_data.json';

fs.writeFileSync(outputFile1, JSON.stringify(allData, null, 2), 'utf8');
console.log(`[清理] ✅ 已保存: ${outputFile1}`);

fs.writeFileSync(outputFile2, JSON.stringify(allData, null, 2), 'utf8');
console.log(`[清理] ✅ 已保存: ${outputFile2}`);

// 显示数据
allData.forEach(d => {
    console.log(`\n日期: ${d.date}`);
    console.log(`  一手房: ${d.newHouse?.todaySignUnits}套, ${d.newHouse?.todaySignArea}㎡`);
    console.log(`  二手房: ${d.secondHand?.yesterdaySaleCount}套, ${d.secondHand?.yesterdaySaleArea}㎡`);
});
