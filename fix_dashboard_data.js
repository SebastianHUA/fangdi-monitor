// 修复并重建 fangdi_data.json（看板数据文件）
// 功能：
// 1. 从原始数据提取正确的一手房成交数据（从 marketReview 补全）
// 2. 统一面积单位为 ㎡
// 3. 保留所有字段（挂牌套数、可售套数等）

const fs = require('fs');
const path = require('path');

// 读取所有历史数据文件
const files = fs.readdirSync('.').filter(f => 
    f.startsWith('fangdi_data_') && 
    f.endsWith('.json') && 
    !f.includes('mcp') &&
    f !== 'fangdi_data.json' &&
    !f.includes('merged')
);

console.log(`[修复] 找到 ${files.length} 个原始数据文件`);

const allData = [];

for (let file of files) {
    try {
        const data = JSON.parse(fs.readFileSync(file, 'utf8'));
        
        // 跳过无效数据
        if (!data.date) {
            console.log(`  ⚠️ 跳过: ${file} (缺少日期)`);
            continue;
        }
        
        // 从 marketReview 提取一手房数据（如果需要补全）
        let todaySaleCount = data.newHouse ? data.newHouse.todaySignUnits : null;
        let todaySaleArea = data.newHouse ? data.newHouse.todaySignArea : null;
        
        if ((!todaySaleCount || todaySaleCount === 0) && data.marketReview) {
            const match = data.marketReview.match(/预\/出售各类商品房(\d+)套/);
            if (match) {
                todaySaleCount = parseInt(match[1]);
                console.log(`  [补全] ${data.date} 一手房成交套数: ${todaySaleCount} (从 marketReview)`);
            }
        }
        
        if ((!todaySaleArea || todaySaleArea === 0) && data.marketReview) {
            const match = data.marketReview.match(/面积([\d.]+)万平方米/);
            if (match) {
                todaySaleArea = parseFloat(match[1]) * 10000; // 万㎡ → ㎡
                console.log(`  [补全] ${data.date} 一手房成交面积: ${todaySaleArea} ㎡ (从 marketReview)`);
            }
        }
        
        // 构建看板数据格式（统一面积单位为 ㎡）
        const transformed = {
            date: data.date,
            newHouse: {
                todaySaleCount: todaySaleCount,
                todaySaleArea: todaySaleArea, // ㎡
                availableUnits: data.newHouse ? data.newHouse.availableUnits : null,
                availableArea: data.newHouse ? data.newHouse.availableArea : null, // 万㎡
                newOpenCount: data.newHouse ? data.newHouse.newOpenUnits : null
            },
            secondHand: {
                yesterdaySaleCount: data.secondHand ? data.secondHand.yesterdaySaleCount : null,
                yesterdaySaleArea: data.secondHand ? data.secondHand.yesterdaySaleArea : null, // ㎡
                listingCount: data.secondHand ? data.secondHand.listingCount : null,
                listingArea: data.secondHand ? data.secondHand.listingArea : null // 万㎡
            },
            marketReview: data.marketReview || null
        };
        
        // 如果有 homePage 数据，补充
        if (data.homePage) {
            if (!transformed.newHouse.availableUnits && data.homePage.newHouseAvailableUnits) {
                transformed.newHouse.availableUnits = data.homePage.newHouseAvailableUnits;
            }
            if (!transformed.secondHand.listingCount && data.homePage.secondHandListingCount) {
                transformed.secondHand.listingCount = data.homePage.secondHandListingCount;
            }
        }
        
        allData.push(transformed);
        console.log(`  ✅ 转换: ${file} (${data.date})`);
    } catch (e) {
        console.log(`  ⚠️ 跳过: ${file} (${e.message})`);
    }
}

// 按日期排序
allData.sort((a, b) => a.date > b.date ? 1 : -1);

console.log(`[修复] 共转换 ${allData.length} 条有效记录`);

// 确保 data 目录存在
const dataDir = 'data';
if (!fs.existsSync(dataDir)) {
    fs.mkdirSync(dataDir);
    console.log('[修复] 创建 data/ 目录');
}

// 确保 docs/data 目录存在
const docsDataDir = path.join('docs', 'data');
if (!fs.existsSync(docsDataDir)) {
    fs.mkdirSync(docsDataDir, { recursive: true });
    console.log('[修复] 创建 docs/data/ 目录');
}

// 保存为看板数据文件
const outputFile1 = path.join(dataDir, 'fangdi_data.json');
const outputFile2 = path.join(docsDataDir, 'fangdi_data.json');

fs.writeFileSync(outputFile1, JSON.stringify(allData, null, 2), 'utf8');
console.log(`[修复] ✅ 数据已保存到: ${outputFile1}`);

fs.writeFileSync(outputFile2, JSON.stringify(allData, null, 2), 'utf8');
console.log(`[修复] ✅ 数据已保存到: ${outputFile2}`);

// 显示最新数据
if (allData.length > 0) {
    const latest = allData[allData.length - 1];
    console.log('\n[修复] 最新数据:');
    console.log(`  日期: ${latest.date}`);
    console.log(`  一手房成交: ${latest.newHouse.todaySaleCount} 套`);
    console.log(`  一手房面积: ${latest.newHouse.todaySaleArea} ㎡`);
    console.log(`  一手房可售: ${latest.newHouse.availableUnits} 套`);
    console.log(`  二手房成交: ${latest.secondHand.yesterdaySaleCount} 套`);
    console.log(`  二手房面积: ${latest.secondHand.yesterdaySaleArea} ㎡`);
    console.log(`  二手房挂牌: ${latest.secondHand.listingCount} 套`);
}
