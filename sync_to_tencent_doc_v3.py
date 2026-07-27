#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同步房地产成交数据到腾讯文档智能表格（V3版本）
- 直接调用MCP API
- 添加重试机制
- 返回成功/失败状态
"""

import json
import sys
import time
from datetime import datetime, timedelta

def load_json_data(json_file):
    """加载JSON数据"""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print("加载JSON文件失败: " + str(e))
        return None

def prepare_daily_record(data):
    """
    准备每日成交数据记录（MCP格式）
    每个日期生成一条记录，包含一手房和二手房所有字段
    """
    date_str = data.get('date', '')
    if not date_str:
        print("警告: 数据中缺少日期字段")
        return None
    
    # 一手房数据
    new_house = data.get('newHouse', {})
    # 二手房数据
    second_hand = data.get('secondHand', {})
    
    # 计算一手房套均面积（㎡/套）
    new_house_avg = 0
    today_sign_units = new_house.get('todaySignUnits') or 0
    today_sign_area = new_house.get('todaySignArea') or 0
    if today_sign_units > 0:
        new_house_avg = round(today_sign_area / today_sign_units, 2)
    
    # 计算二手房套均面积（㎡/套）
    second_hand_avg = 0
    yesterday_sale_count = second_hand.get('yesterdaySaleCount') or 0
    yesterday_sale_area = second_hand.get('yesterdaySaleArea') or 0
    if yesterday_sale_count > 0:
        second_hand_avg = round(yesterday_sale_area / yesterday_sale_count, 2)
    
    # 生成一条合并记录（一手房+二手房）
    record = {
        "date": date_str,
        "newHouse": {
            "units": new_house.get('todaySignUnits', 0) or 0,
            "area": new_house.get('todaySignArea', 0) or 0,
            "avg": new_house_avg,
            "available": new_house.get('availableUnits', 0) or 0
        },
        "secondHand": {
            "units": second_hand.get('yesterdaySaleCount', 0) or 0,
            "area": second_hand.get('yesterdaySaleArea', 0) or 0,
            "avg": second_hand_avg,
            "listing": second_hand.get('listingCount', 0) or 0
        }
    }
    
    print("准备合并记录: " + date_str + " (一手房+" + str(record["newHouse"]["units"]) + "套 / 二手房+" + str(record["secondHand"]["units"]) + "套)")
    
    return record

def sync_to_tencent_doc(record, max_retries=2):
    """
    同步数据到腾讯文档（通过MCP工具）
    由于Python脚本无法直接调用MCP工具，这个函数会输出MCP工具的调用参数
    然后由外部（如自动化任务中的AI）来执行MCP工具调用
    """
    print("\n=== 腾讯文档同步参数 ===")
    print("请使用以下参数调用 mcp__tencent-docs__smartsheet.update_records:")
    print(json.dumps(record, ensure_ascii=False, indent=2))
    print("\n注意：本脚本无法直接调用MCP工具，需要外部执行")
    print("建议：在自动化任务中，让AI直接调用MCP工具")
    
    # 返回失败，提示需要外部调用
    return False, "需要外部调用MCP工具"

def main():
    if len(sys.argv) < 2:
        print("用法: python sync_to_tencent_doc_v3.py <json_file>")
        print("示例: python sync_to_tencent_doc_v3.py data/fangdi_data.json")
        sys.exit(1)
    
    json_file = sys.argv[1]
    
    # 加载JSON数据
    print("[1/2] 加载数据文件: " + json_file)
    data = load_json_data(json_file)
    if not data:
        sys.exit(1)
    
    # 如果数据是数组，取第一条（最新数据）
    if isinstance(data, list):
        data = data[0]
    
    # 准备记录
    print("\n[2/2] 准备腾讯文档同步数据...")
    record = prepare_daily_record(data)
    
    if not record:
        print("错误: 无法准备记录")
        sys.exit(1)
    
    # 同步到腾讯文档（实际上只是输出参数）
    success, message = sync_to_tencent_doc(record)
    
    if success:
        print("\n✅ 腾讯文档同步成功！")
        sys.exit(0)
    else:
        print("\n❌ 腾讯文档同步失败: " + message)
        sys.exit(1)

if __name__ == "__main__":
    main()
