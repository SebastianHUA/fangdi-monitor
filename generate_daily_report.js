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

// 生成完整日报的Markdown内容（优化版：适合微信阅读）
function generateReportMarkdown(data, date) {
    const lines = [];
    
    // 标题
    lines.push(`📊 上海房地产市场日报`);
    lines.push(`📅 数据日期：${date}`);
    lines.push(``);
    
    // 一、一手房成交情况
    lines.push(`🏗️ 一手房成交情况`);
    lines.push(``);
    
    const newHouse = data.newHouse || {};
    const homePage = data.homePage || {};
    
    if (newHouse && (newHouse.todaySignUnits || homePage.todaySignUnits)) {
        const signUnits = newHouse.todaySignUnits || homePage.todaySignUnits || 0;
        const signArea = newHouse.todaySignArea || homePage.todaySignArea || 0;
        const availableUnits = newHouse.availableUnits || homePage.newHouseAvailableUnits || 0;
        
        lines.push(`✅ 当日签约：${signUnits}套 / ${signArea}㎡`);
        
        if (signUnits > 0 && signArea > 0) {
            const avgArea = (signArea / signUnits).toFixed(1);
            lines.push(`📐 套均面积：${avgArea}㎡/套`);
        }
        
        lines.push(`🏢 可售住宅：${availableUnits.toLocaleString()}套`);
    } else {
        lines.push(`（无数据）`);
    }
    
    lines.push(``);
    
    // 二、二手房成交情况
    lines.push(`🏘️ 二手房成交情况`);
    lines.push(``);
    
    const secondHand = data.secondHand || {};
    
    if (secondHand && secondHand.yesterdaySaleCount) {
        const saleCount = secondHand.yesterdaySaleCount || 0;
        const saleArea = secondHand.yesterdaySaleArea || 0;
        const listingCount = secondHand.listingCount || 0;
        
        lines.push(`✅ 当日签约：${saleCount}套 / ${saleArea}㎡`);
        
        if (saleCount > 0 && saleArea > 0) {
            const avgArea = (saleArea / saleCount).toFixed(1);
            lines.push(`📐 套均面积：${avgArea}㎡/套`);
        }
        
        lines.push(`📋 挂牌套数：${listingCount.toLocaleString()}套`);
    } else {
        lines.push(`（无数据）`);
    }
    
    lines.push(``);
    
    // 三、楼市回顾（新增）
    if (data.marketReview) {
        lines.push(`📰 楼市回顾`);
        lines.push(``);
        lines.push(data.marketReview);
        lines.push(``);
    }
    
    // 四、数据链接
    lines.push(`📈 数据看板：`);
    lines.push(`https://sebastianhua.github.io/fangdi-monitor/`);
    lines.push(``);
    lines.push(`📋 数据表格：`);
    lines.push(`https://docs.qq.com/smartsheet/DTnNsSXVoc21TbkhF`);
    
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
    
    // 3. 合并数据（优先使用当前数据文件中的一手房数据）
    let newHouse = null;
    
    // 尝试从当前数据文件获取
    if (secondHandData && secondHandData.newHouse && secondHandData.newHouse.todaySignUnits) {
        newHouse = secondHandData.newHouse;
    } else if (newHouseData && newHouseData.newHouse) {
        newHouse = newHouseData.newHouse;
    }
    
    // 如果一手房数据为0，尝试从 marketReview 提取
    if ((!newHouse || !newHouse.todaySignUnits || newHouse.todaySignUnits === 0) && secondHandData && secondHandData.marketReview) {
        const match = secondHandData.marketReview.match(/预\/出售各类商品房(\d+)套/);
        const areaMatch = secondHandData.marketReview.match(/面积([\d.]+)万平方米/);
        if (match) {
            newHouse = {
                todaySignUnits: parseInt(match[1]),
                todaySignArea: areaMatch ? parseFloat(areaMatch[1]) * 10000 : 0,
                availableUnits: newHouse ? newHouse.availableUnits : null,
                availableArea: newHouse ? newHouse.availableArea : null
            };
            console.log(`[日报生成] ✅ 从 marketReview 补全一手房数据: ${newHouse.todaySignUnits}套`);
        }
    }
    
    const mergedData = {
        date: yesterdayStr,
        newHouse: newHouse,
        secondHand: secondHandData.secondHand || null,
        homePage: secondHandData.homePage || (newHouseData ? newHouseData.homePage : null),
        marketReview: secondHandData.marketReview || null  // 新增：楼市回顾
    };
    
    // 调试信息
    if (secondHandData && secondHandData.newHouse && secondHandData.newHouse.todaySignUnits) {
        console.log(`[日报生成] ✅ 使用当前数据文件中的一手房数据: ${secondHandData.newHouse.todaySignUnits}套`);
    } else if (newHouseData && newHouseData.newHouse) {
        console.log(`[日报生成] ✅ 使用昨天数据文件中的一手房数据: ${newHouseData.newHouse.todaySignUnits}套`);
    } else {
        console.log(`[日报生成] ⚠️ 未找到一手房数据`);
    }
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
