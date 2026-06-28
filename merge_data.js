#!/usr/bin/env node
/**
 * 合并每日数据文件为历史数据文件
 * 读取 data/fangdi_YYYY-MM-DD.json，合并为 data/fangdi_data.json
 */

const fs = require('fs');
const path = require('path');

const DATA_DIR = path.join(__dirname, 'data');
const OUTPUT_FILE = path.join(DATA_DIR, 'fangdi_data.json');

function mergeData() {
    console.log('[数据合并] 开始合并每日数据文件...');
    
    // 读取所有每日数据文件
    const files = fs.readdirSync(DATA_DIR)
        .filter(f => f.startsWith('fangdi_') && f.endsWith('.json') && f !== 'fangdi_data.json')
        .sort(); // 按日期排序
    
    console.log(`[数据合并] 找到 ${files.length} 个数据文件`);
    
    const allData = [];
    
    for (const file of files) {
        const filePath = path.join(DATA_DIR, file);
        try {
            const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
            allData.push(data);
        } catch (e) {
            console.error(`[数据合并] 读取 ${file} 失败:`, e.message);
        }
    }
    
    // 按日期排序
    allData.sort((a, b) => a.date > b.date ? 1 : -1);
    
    // 写入合并文件
    fs.writeFileSync(OUTPUT_FILE, JSON.stringify(allData, null, 2));
    console.log(`[数据合并] ✅ 已合并 ${allData.length} 条数据到 ${OUTPUT_FILE}`);
    
    return allData;
}

// 执行
if (require.main === module) {
    mergeData();
}

module.exports = { mergeData };
