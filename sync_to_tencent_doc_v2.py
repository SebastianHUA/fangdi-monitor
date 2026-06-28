#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同步房地产成交数据到腾讯文档智能表格（V2版本）
使用正确的MCP格式（field_values）
"""

import json
import sys
from datetime import datetime, timedelta

def load_json_data(json_file):
    """加载JSON数据"""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print("加载JSON文件失败: " + str(e))
        return None

def prepare_daily_records(data):
    """
    准备每日成交数据记录（MCP格式）
    每个日期生成一条记录，包含一手房和二手房所有字段
    """
    records = []
    
    date_str = data.get('date', '')
    if not date_str:
        print("警告: 数据中缺少日期字段")
        return records
    
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    
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
        "field_values": [
            {"field": "日期", "text_value": {"items": [{"text": date_str, "type": "text"}]}},
            {"field": "一手房成交套数", "number_value": new_house.get('todaySignUnits', 0) or 0},
            {"field": "一手房成交面积（㎡）", "number_value": new_house.get('todaySignArea', 0) or 0},
            {"field": "一手房套均面积（㎡/套）", "number_value": new_house_avg},
            {"field": "一手房可售套数", "number_value": new_house.get('availableUnits', 0) or 0},
            {"field": "二手房成交套数", "number_value": second_hand.get('yesterdaySaleCount', 0) or 0},
            {"field": "二手房成交面积（㎡）", "number_value": second_hand.get('yesterdaySaleArea', 0) or 0},
            {"field": "二手房套均面积（㎡/套）", "number_value": second_hand_avg},
            {"field": "二手房挂牌套数", "number_value": second_hand.get('listingCount', 0) or 0}
        ]
    }
    
    records.append(record)
    print("准备合并记录: " + date_str + " (一手房+" + "二手房)")
    
    return records

def prepare_subscription_records(data):
    """
    准备认购公示明细记录（MCP格式）
    日期字段使用毫秒级unix时间戳
    """
    records = []
    
    new_house = data.get('newHouse', {})
    projects = new_house.get('subscriptions', [])
    
    if not projects:
        return records
    
    # 数据日期（转换为时间戳）
    date_str = data.get('date', '')
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    data_date_ms = int(date_obj.timestamp() * 1000)
    
    for project in projects:
        # 认购开始日期（转换为时间戳）
        start_date_ms = 0
        if project.get('startDate'):
            try:
                start_date_obj = datetime.strptime(project['startDate'], '%Y-%m-%d')
                start_date_ms = int(start_date_obj.timestamp() * 1000)
            except:
                pass
        
        # 认购结束日期（转换为时间戳）
        end_date_ms = 0
        if project.get('endDate'):
            try:
                end_date_obj = datetime.strptime(project['endDate'], '%Y-%m-%d')
                end_date_ms = int(end_date_obj.timestamp() * 1000)
            except:
                pass
        
        record = {
            "field_values": [
                {"field": "数据日期", "string_value": str(data_date_ms)},
                {"field": "所在区", "string_value": project.get('region', '')},
                {"field": "项目名称", "string_value": project.get('name', '')},
                {"field": "开发企业", "string_value": project.get('developer', '')},
                {"field": "认购开始日期", "string_value": str(start_date_ms)},
                {"field": "认购结束日期", "string_value": str(end_date_ms)},
                {"field": "认购比", "string_value": project.get('ratio', '')},
                {"field": "套数（套）", "number_value": int(project.get('units', 0))},
                {"field": "上市面积（㎡）", "number_value": float(project.get('area', 0))},
                {"field": "备案均价（元/㎡）", "number_value": float(project.get('avgPrice', 0))}
            ]
        }
        records.append(record)
    
    print("准备 " + str(len(records)) + " 条认购公示明细记录")
    return records

def main():
    if len(sys.argv) < 2:
        print("用法: python sync_to_tencent_doc_v2.py <json_file>")
        print("示例: python sync_to_tencent_doc_v2.py data/fangdi_2026-06-28.json")
        sys.exit(1)
    
    json_file = sys.argv[1]
    
    # 加载JSON数据
    print("[1/3] 加载数据文件: " + json_file)
    data = load_json_data(json_file)
    if not data:
        sys.exit(1)
    
    # 准备每日成交数据记录
    print("[2/3] 准备每日成交数据...")
    daily_records = prepare_daily_records(data)
    
    if daily_records:
        # 保存到文件
        output_file = json_file.replace('.json', '_daily_mcp.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(daily_records, f, ensure_ascii=False, indent=2)
        print("√ 每日成交数据已保存: " + output_file)
    else:
        print("警告: 没有每日成交数据需要同步")
    
    # 准备认购公示明细记录
    print("\n[3/3] 准备认购公示明细数据...")
    subscription_records = prepare_subscription_records(data)
    
    if subscription_records:
        # 保存到文件
        subscription_output_file = json_file.replace('.json', '_subscription_mcp.json')
        with open(subscription_output_file, 'w', encoding='utf-8') as f:
            json.dump(subscription_records, f, ensure_ascii=False, indent=2)
        print("√ 认购公示明细已保存: " + subscription_output_file)
    else:
        print("警告: 没有认购公示数据需要同步")
    
    # 输出下一步指导
    print("\n=== 下一步：使用MCP工具将数据写入腾讯文档 ===")
    print("\n1. 同步每日成交数据:")
    print("   file_id: DTnNsSXVoc21TbkhF")
    print("   sheet_id: bwHrDx")
    print("   records: 从 " + json_file.replace('.json', '_daily_mcp.json') + " 读取")
    print("\n2. 同步认购公示明细:")
    print("   file_id: DTnNsSXVoc21TbkhF")
    print("   sheet_id: 0g5JQL")
    print("   records: 从 " + json_file.replace('.json', '_subscription_mcp.json') + " 读取")

if __name__ == "__main__":
    main()
