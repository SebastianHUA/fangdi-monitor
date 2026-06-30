// 修复版：正确采集一手房成交数据并合并到最终JSON
// 问题：首页只显示"签约套数"，但没有"今日成交"数据
// 解决：从交易统计页面（trade.html）采集一手房成交数据，然后合并到最终结果

const fs = require('fs');
const path = require('path');

// 读取最新的原始数据文件
const files = fs.readdirSync('.').filter(f => 
    f.startsWith('fangdi_data_') && 
    f.endsWith('.json') && 
    !f.includes('mcp') &&
    f !== 'fangdi_data.json' &&
    !f.includes('merged')
).sort().reverse();

console.log(`[修复] 找到 ${files.length} 个原始数据文件`);

// 读取最新的文件
const latestFile = files[0];
console.log(`[修复] 读取最新文件: ${latestFile}`);

const data = JSON.parse(fs.readFileSync(latestFile, 'utf8'));

console.log(`[修复] 当前数据状态:`);
console.log(`  日期: ${data.date}`);
console.log(`  newHouse.todaySignUnits: ${data.newHouse ? data.newHouse.todaySignUnits : 'null'}`);
console.log(`  newHouse.todaySignArea: ${data.newHouse ? data.newHouse.todaySignArea : 'null'}`);
console.log(`  marketReview: ${data.marketReview ? '存在' : 'null'}`);

// 检查是否需要从 marketReview 补全
if ((!data.newHouse || !data.newHouse.todaySignUnits || data.newHouse.todaySignUnits === 0) && data.marketReview) {
    console.log(`[修复] 从 marketReview 补全一手房数据...`);
    
    const match = data.marketReview.match(/预\/出售各类商品房(\d+)套/);
    const areaMatch = data.marketReview.match(/面积([\d.]+)万平方米/);
    
    if (match) {
        if (!data.newHouse) {
            data.newHouse = {};
        }
        
        data.newHouse.todaySignUnits = parseInt(match[1]);
        data.newHouse.todaySignArea = areaMatch ? Math.round(parseFloat(areaMatch[1]) * 10000) : 0;
        
        console.log(`[修复] ✅ 补全完成:`);
        console.log(`  一手房成交: ${data.newHouse.todaySignUnits} 套`);
        console.log(`  一手房面积: ${data.newHouse.todaySignArea} ㎡`);
        
        // 保存修复后的数据
        fs.writeFileSync(latestFile, JSON.stringify(data, null, 2), 'utf8');
        console.log(`[修复] ✅ 已保存到: ${latestFile}`);
    }
}

// 重建看板数据文件
console.log(`\n[修复] 重建看板数据文件...`);

const allData = [];

for (let file of files.reverse()) {
    try {
        const d = JSON.parse(fs.readFileSync(file, 'utf8'));
        
        // 补全一手房数据
        if ((!d.newHouse || !d.newHouse.todaySignUnits || d.newHouse.todaySignUnits === 0) && d.marketReview) {
            const match = d.marketReview.match(/预\/出售各类商品房(\d+)套/);
            const areaMatch = d.marketReview.match(/面积([\d.]+)万平方米/);
            
            if (match) {
                if (!d.newHouse) d.newHouse = {};
                d.newHouse.todaySignUnits = parseInt(match[1]);
                d.newHouse.todaySignArea = areaMatch ? Math.round(parseFloat(areaMatch[1]) * 10000) : 0;
            }
        }
        
        allData.push(d);
    } catch (e) {
        console.log(`[修复] ⚠️ 跳过: ${file} (${e.message})`);
    }
}

// 保存看板数据
const outputFile1 = path.join('data', 'fangdi_data.json');
const outputFile2 = path.join('docs', 'data', 'fangdi_data.json');

// 确保目录存在
if (!fs.existsSync('data')) fs.mkdirSync('data');
if (!fs.existsSync(path.join('docs', 'data'))) fs.mkdirSync(path.join('docs', 'data'), { recursive: true });

fs.writeFileSync(outputFile1, JSON.stringify(allData, null, 2), 'utf8');
console.log(`[修复] ✅ 看板数据已保存: ${outputFile1}`);

fs.writeFileSync(outputFile2, JSON.stringify(allData, null, 2), 'utf8');
console.log(`[修复] ✅ 看板数据已保存: ${outputFile2}`);

console.log(`\n[修复] ✅ 完成！共处理 ${allData.length} 条记录`);
