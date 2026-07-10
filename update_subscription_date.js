// 仅更新认购数据的date字段（避免UTC偏移导致日期错误）
const fs = require('fs');
const path = require('path');

const filePath = path.join(__dirname, 'data', 'subscription_data.json');
const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));

const now = new Date();
const dateStr = now.getFullYear() + '-' +
    String(now.getMonth() + 1).padStart(2, '0') + '-' +
    String(now.getDate()).padStart(2, '0');

data.date = dateStr;
data.updateTime = now.toISOString();

fs.writeFileSync(filePath, JSON.stringify(data, null, 2), 'utf8');
console.log(`✅ 认购数据日期已更新: ${dateStr}`);
console.log(`  楼盘总数: ${data.recentSubscriptions.length}`);
