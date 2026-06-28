#!/usr/bin/env node
/**
 * 生成完整的每日房地产成交通报
 * 合并一手房和二手房数据，生成Markdown日报
 * 
 * 使用方式：
 *   node generate_daily_report.js [json_file]
 * 
 * 参数：
 *   json_file: 可选，包含二手房数据的JSON文件（今天日期）
 *              如果不提供，则自动查找今天的JSON文件
 * 
 * 功能：
 *   1. 读取今天的JSON文件（包含二手房数据）
 *   2. 读取昨天的JSON文件（包含一手房数据）
 *   3. 合并数据
 *   4. 生成完整的Markdown日报
 *   5. 保存日报到文件
 *   6. 输出日报内容（用于微信推送）
 */

const fs = require('fs');
const path = require('path');

// 获取指定日期的字符串（YYYY-MM-DD，使用本地时间）
function getDateString(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

// 读取JSON文件
function readJSONFile(filePath) {
    try {
        if (!fs.existsSync(filePath)) {
            console.log(`  [警告] 文件不存在: ${filePath}`);
            return null;
        }
        const content = fs.readFileSync(filePath, 'utf8');
        return JSON.parse(content);
    } catch (e) {
        console.log(`  [错误] 读取文件失败: ${filePath}, ${e.message}`);
        return null;
    }
}

// 生成完整日报的Markdown内容
function generateReportMarkdown(data, date) {
    const lines = [];
    
    lines.push(`# 上海房地产市场日报_${date}`);
    lines.push(``);
    lines.push(`> 生成时间: ${new Date().toLocaleString('zh-CN', {timeZone: 'Asia/Shanghai'})}`);
    lines.push(``);
    
    // 一、一手房成交情况
    lines.push(`## 📈 一、一手房成交情况`);
    lines.push(``);
    
    const newHouse = data.newHouse || {};
    const homePage = data.homePage || {};
    
    if (newHouse && (newHouse.todaySignUnits || homePage.todaySignUnits)) {
        const signUnits = newHouse.todaySignUnits || homePage.todaySignUnits || 0;
        const signArea = newHouse.todaySignArea || homePage.todaySignArea || 0;
        const availableUnits = newHouse.availableUnits || homePage.newHouseAvailableUnits || 0;
        const availableArea = newHouse.availableArea || homePage.newHouseAvailableArea || 0;
        
        lines.push(`- **当日签约套数**: ${signUnits} 套`);
        lines.push(`- **当日签约面积**: ${signArea} ㎡`);
        
        if (signUnits > 0 && signArea > 0) {
            const avgArea = (signArea / signUnits).toFixed(2);
            lines.push(`- **套均面积**: ${avgArea} ㎡/套`);
        }
        
        lines.push(`- **可售住宅套数**: ${availableUnits} 套`);
        lines.push(`- **可售住宅面积**: ${availableArea} 万㎡`);
        
        if (newHouse.newOpenUnits) {
            lines.push(`- **新开房源**: ${newHouse.newOpenUnits} 套`);
        }
    } else {
        lines.push(`（无数据）`);
    }
    
    lines.push(``);
    
    // 二、二手房成交情况
    lines.push(`## 📉 二、二手房成交情况`);
    lines.push(``);
    
    const secondHand = data.secondHand || {};
    
    if (secondHand && secondHand.yesterdaySaleCount) {
        lines.push(`- **昨日成交套数**: ${secondHand.yesterdaySaleCount} 套`);
        lines.push(`- **昨日成交面积**: ${secondHand.yesterdaySaleArea} ㎡`);
        
        if (secondHand.yesterdaySaleCount > 0 && secondHand.yesterdaySaleArea > 0) {
            const avgArea = (secondHand.yesterdaySaleArea / secondHand.yesterdaySaleCount).toFixed(2);
            lines.push(`- **套均面积**: ${avgArea} ㎡/套`);
        }
    } else {
        lines.push(`（无数据）`);
    }
    
    lines.push(``);
    
    // 三、市场供应情况
    lines.push(`## 🏗️ 三、市场供应情况`);
    lines.push(``);
    
    if (homePage && homePage.newHouseAvailableUnits) {
        lines.push(`- **一手房可售套数**: ${homePage.newHouseAvailableUnits} 套`);
        lines.push(`- **一手房可售面积**: ${homePage.newHouseAvailableArea} 万㎡`);
    }
    
    if (homePage && homePage.secondHandListingCount) {
        lines.push(`- **二手房挂牌笔数**: ${homePage.secondHandListingCount} 笔`);
        lines.push(`- **二手房挂牌面积**: ${homePage.secondHandListingArea} 万㎡`);
    }
    
    lines.push(``);
    
    // 四、数据来源
    lines.push(`## 📋 四、数据来源`);
    lines.push(``);
    lines.push(`- **数据来源**: 上海网上房地产（www.fangdi.com.cn）`);
    lines.push(`- **一手房数据**: ${date} 23:55 抓取`);
    lines.push(`- **二手房数据**: ${getDateString(new Date())} 07:00 抓取`);
    lines.push(``);
    
    return lines.join('\n');
}

// 主函数
function main() {
    console.log('[日报生成] 开始...');
    
    // 解析命令行参数
    const args = process.argv.slice(2);
    const inputFile = args[0]; // 可选的JSON文件路径
    
    // 计算日期
    const today = new Date();
    const todayStr = getDateString(today);
    
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    const yesterdayStr = getDateString(yesterday);
    
    console.log(`[日报生成] 今天: ${todayStr}`);
    console.log(`[日报生成] 昨天: ${yesterdayStr}`);
    
    // 1. 读取二手房数据（今天的JSON文件）
    let secondHandFile;
    if (inputFile && fs.existsSync(inputFile)) {
        secondHandFile = inputFile;
    } else {
        secondHandFile = path.join(__dirname, `fangdi_data_${todayStr}.json`);
    }
    
    console.log(`[日报生成] 读取二手房数据: ${secondHandFile}`);
    const secondHandData = readJSONFile(secondHandFile);
    
    if (!secondHandData) {
        console.log(`[日报生成] ❌ 未找到二手房数据文件`);
        process.exit(1);
    }
    
    // 2. 读取一手房数据（昨天的JSON文件）
    const newHouseFile = path.join(__dirname, `fangdi_data_${yesterdayStr}.json`);
    console.log(`[日报生成] 读取一手房数据: ${newHouseFile}`);
    const newHouseData = readJSONFile(newHouseFile);
    
    if (!newHouseData) {
        console.log(`[日报生成] ⚠️ 未找到一手房数据文件，将只生成二手房报告`);
    }
    
    // 3. 合并数据
    const mergedData = {
        date: yesterdayStr,
        newHouse: newHouseData ? newHouseData.newHouse : null,
        secondHand: secondHandData.secondHand || null,
        homePage: secondHandData.homePage || (newHouseData ? newHouseData.homePage : null)
    };
    
    // 4. 如果一手房数据缺失，尝试从今天的数据文件中获取（homePage可能包含）
    if (!mergedData.newHouse && secondHandData.homePage) {
        mergedData.newHouse = {
            todaySignUnits: secondHandData.homePage.todaySignUnits,
            todaySignArea: secondHandData.homePage.todaySignArea,
            availableUnits: secondHandData.homePage.newHouseAvailableUnits,
            availableArea: secondHandData.homePage.newHouseAvailableArea
        };
    }
    
    // 5. 生成完整日报
    const report = generateReportMarkdown(mergedData, yesterdayStr);
    
    // 6. 保存日报
    const outputFile = path.join(__dirname, `上海房地产市场日报_${yesterdayStr}_完整版.md`);
    fs.writeFileSync(outputFile, report, 'utf8');
    console.log(`[日报生成] ✅ 日报已保存: ${outputFile}`);
    
    // 7. 输出日报内容（用于微信推送）
    console.log('\n========== 日报内容（用于微信推送）==========');
    console.log(report);
    console.log('========== 日报结束 ==========\n');
    
    // 8. 返回输出文件路径
    return outputFile;
}

// 执行
if (require.main === module) {
    try {
        const outputFile = main();
        console.log(`[日报生成] ✅ 完成！输出文件: ${outputFile}`);
        process.exit(0);
    } catch (e) {
        console.error(`[日报生成] ❌ 错误: ${e.message}`);
        console.error(e.stack);
        process.exit(1);
    }
}

module.exports = { generateReportMarkdown, main };
