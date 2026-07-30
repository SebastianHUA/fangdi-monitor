#!/usr/bin/env node
/**
 * 生成完整的每日房地产成交通报（固定模板版）
 *
 * 数据来源：data/fangdi_data.json（数组，每条含 date/newHouse/secondHand/marketReview）
 * 输出路径：data/fangdi_daily_report_YYYY-MM-DD.md（07:00 任务读取此路径发送微信）
 *
 * 用法：
 *   node generate_daily_report.js            # 默认取“昨天”为数据日期
 *   node generate_daily_report.js 2026-07-28 # 指定数据日期（用于补生成/校准）
 */

const fs = require('fs');
const path = require('path');

// 本地时间日期字符串 YYYY-MM-DD
function getDateString(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

// 千分位整数（无小数），如 44852 -> 44,852
function fmtInt(n) {
    return Math.round(n || 0).toLocaleString('en-US');
}

// 楼市回顾原文清洗：与官方展示模板保持一致（㎡、精简区域分隔符）
function normalizeMarketReview(raw) {
    if (!raw) return '';
    let s = raw;
    s = s.replace(/平方米/g, '㎡').replace(/万平方米/g, '万㎡');      // 单位统一
    s = s.replace(/，\s+/g, '，');                                    // 去掉全角逗号后的多余空格
    s = s.replace(/其中位于/g, '其中');                               // 去“位于”
    s = s.replace(/(郊环以外|外郊环间|中外环间|内中环间|内环以内)的(\d+)个/g, '$1$2个'); // 去“的”
    s = s.replace(/其中([^。]+)。/, (m, body) => '其中' + body.replace(/，/g, '、') + '。'); // 区域间“，”转“、”
    return s;
}

// 生成固定格式日报
function generateReportMarkdown(data, date) {
    const lines = [];
    const newHouse = data.newHouse || {};
    const secondHand = data.secondHand || {};
    const marketReview = normalizeMarketReview(data.marketReview);

    lines.push('📊 上海房地产市场日报');
    lines.push(`📅 ${date}`);
    lines.push('');

    const nhU = newHouse.todaySignUnits || 0;
    const nhA = newHouse.todaySignArea || 0;
    const nhAvail = (newHouse.availableUnits != null) ? newHouse.availableUnits : 0;
    lines.push(`🏗️ 一手房：当日签约 ${fmtInt(nhU)}套 / ${fmtInt(nhA)}㎡`);
    const nhAvg = (nhU > 0 && nhA > 0) ? (nhA / nhU).toFixed(2) : '0.00';
    lines.push(`　📐 套均 ${nhAvg}㎡ | 🏢 可售 ${fmtInt(nhAvail)}套`);
    lines.push('');

    const shC = secondHand.yesterdaySaleCount || 0;
    const shA = secondHand.yesterdaySaleArea || 0;
    const shList = (secondHand.listingCount != null) ? secondHand.listingCount : 0;
    lines.push(`🏘️ 二手房：当日签约 ${fmtInt(shC)}套 / ${fmtInt(shA)}㎡`);
    const shAvg = (shC > 0 && shA > 0) ? (shA / shC).toFixed(2) : '0.00';
    lines.push(`　📐 套均 ${shAvg}㎡ | 📋 挂牌 ${fmtInt(shList)}笔`);
    lines.push('');

    if (marketReview) {
        lines.push('📰 楼市回顾');
        lines.push(marketReview.trim());
        lines.push('');
    }

    lines.push('📈 看板：https://sebastianhua.github.io/fangdi-monitor/');
    lines.push('📋 表格：https://docs.qq.com/smartsheet/DTnNsSXVoc21TbkhF');

    return lines.join('\n');
}

// 主函数
function main() {
    console.log('[日报生成] 开始...');
    const args = process.argv.slice(2);
    // 支持两种写法：`node generate_daily_report.js 2026-07-30` 或 `--date=2026-07-30`
    let explicitDate = null;
    for (const a of args) {
        const m = /^--date=(\d{4}-\d{2}-\d{2})$/.exec(a);
        if (m) { explicitDate = m[1]; break; }
        if (/^\d{4}-\d{2}-\d{2}$/.test(a)) { explicitDate = a; break; }
    }

    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    const yesterdayStr = getDateString(yesterday);

    const dataDate = explicitDate || yesterdayStr;
    console.log(`[日报生成] 数据日期: ${dataDate}`);

    const dataFile = path.join(__dirname, 'data', 'fangdi_data.json');
    let all = null;
    try {
        all = JSON.parse(fs.readFileSync(dataFile, 'utf8'));
    } catch (e) {
        console.error(`[日报生成] ❌ 读取 ${dataFile} 失败: ${e.message}`);
        process.exit(1);
    }
    if (!Array.isArray(all)) {
        console.error('[日报生成] ❌ 数据不是数组');
        process.exit(1);
    }

    let record = all.find(r => r.date === dataDate);
    if (!record) {
        // 兜底：取最近一条“一手房+二手房”都有的记录
        record = all.find(r => r.newHouse && r.newHouse.todaySignUnits && r.secondHand && r.secondHand.yesterdaySaleCount);
        if (record) console.log(`[日报生成] ⚠️ 未找到 ${dataDate}，改用最近完整记录 ${record.date}`);
    }
    if (!record) {
        console.error('[日报生成] ❌ 未找到可用记录');
        process.exit(1);
    }

    // 若一手房缺失，尝试从楼市回顾回补（todaySignUnits / todaySignArea）
    if ((!record.newHouse || !record.newHouse.todaySignUnits) && record.marketReview) {
        const m = record.marketReview.match(/预\/出售各类商品房(\d+)套/);
        const a = record.marketReview.match(/面积([\d.]+)万平方米/);
        if (m) {
            record = Object.assign({}, record, {
                newHouse: {
                    todaySignUnits: parseInt(m[1]),
                    todaySignArea: a ? parseFloat(a[1]) * 10000 : 0,
                    availableUnits: record.newHouse ? record.newHouse.availableUnits : null
                }
            });
            console.log(`[日报生成] ✅ 从楼市回顾回补一手房: ${m[1]}套`);
        }
    }

    const report = generateReportMarkdown(record, dataDate);

    const outFile = path.join(__dirname, 'data', `fangdi_daily_report_${dataDate}.md`);
    fs.writeFileSync(outFile, report, 'utf8');
    console.log(`[日报生成] ✅ 日报已保存: ${outFile}`);

    console.log('\n========== 日报内容 ==========');
    console.log(report);
    console.log('========== 日报结束 ==========\n');
    return outFile;
}

if (require.main === module) {
    try {
        const out = main();
        console.log(`[日报生成] ✅ 完成！输出: ${out}`);
        process.exit(0);
    } catch (e) {
        console.error(`[日报生成] ❌ 错误: ${e.message}`);
        console.error(e.stack);
        process.exit(1);
    }
}

module.exports = { generateReportMarkdown, main, normalizeMarketReview };
