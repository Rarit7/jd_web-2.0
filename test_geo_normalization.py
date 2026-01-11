#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
地理位置规范化测试脚本
验证省份名称转换是否正确匹配地图标准格式
"""

import sys
sys.path.insert(0, '/home/ls/workspace/sdjd/jd_web-2.0')

from jd.helpers.geo_helper import normalize_province_name, normalize_provinces_list, normalize_cities_with_provinces


def test_single_province_normalization():
    """测试单个省份的规范化"""
    print("=" * 60)
    print("测试1: 单个省份规范化")
    print("=" * 60)

    test_cases = [
        # 普通省份
        ('山东', '山东省'),
        ('广东', '广东省'),
        ('江苏', '江苏省'),
        ('四川', '四川省'),
        # 直辖市
        ('北京', '北京市'),
        ('上海', '上海市'),
        ('天津', '天津市'),
        ('重庆', '重庆市'),
        # 自治区
        ('宁夏', '宁夏回族自治区'),
        ('广西', '广西壮族自治区'),
        ('内蒙古', '内蒙古自治区'),
        ('新疆', '新疆维吾尔自治区'),
        ('西藏', '西藏自治区'),
        # 特别行政区
        ('香港', '香港特别行政区'),
        ('澳门', '澳门特别行政区'),
        # 已经是标准格式
        ('山东省', '山东省'),
        ('北京市', '北京市'),
        ('宁夏回族自治区', '宁夏回族自治区'),
    ]

    passed = 0
    failed = 0

    for input_name, expected in test_cases:
        result = normalize_province_name(input_name)
        status = "✓" if result == expected else "✗"
        if result == expected:
            passed += 1
        else:
            failed += 1
        print(f"{status} '{input_name}' -> '{result}' (期望: '{expected}')")

    print(f"\n结果: {passed} 个通过, {failed} 个失败")
    return failed == 0


def test_provinces_list_normalization():
    """测试省份列表的规范化"""
    print("\n" + "=" * 60)
    print("测试2: 省份列表规范化")
    print("=" * 60)

    provinces_data = [
        {'name': '山东', 'value': 239},
        {'name': '江苏', 'value': 200},
        {'name': '北京', 'value': 150},
        {'name': '宁夏', 'value': 100},
        {'name': '香港', 'value': 50},
    ]

    result = normalize_provinces_list(provinces_data)

    print("输入数据:")
    for item in provinces_data:
        print(f"  {item}")

    print("\n规范化后:")
    for item in result:
        print(f"  {item}")

    expected_names = ['山东省', '江苏省', '北京市', '宁夏回族自治区', '香港特别行政区']
    actual_names = [item['name'] for item in result]

    if actual_names == expected_names:
        print("\n✓ 列表规范化正确")
        return True
    else:
        print(f"\n✗ 列表规范化失败")
        print(f"期望: {expected_names}")
        print(f"实际: {actual_names}")
        return False


def test_cities_with_provinces_normalization():
    """测试包含省份信息的城市列表规范化"""
    print("\n" + "=" * 60)
    print("测试3: 城市列表及其省份规范化")
    print("=" * 60)

    cities_data = [
        {'name': '青岛', 'value': 200, 'province': '山东'},
        {'name': '上海', 'value': 180, 'province': '上海'},
        {'name': '成都', 'value': 150, 'province': '四川'},
        {'name': '南京', 'value': 120, 'province': '江苏'},
        {'name': '香港', 'value': 100, 'province': '香港'},
    ]

    result = normalize_cities_with_provinces(cities_data)

    print("输入数据:")
    for item in cities_data:
        print(f"  {item}")

    print("\n规范化后:")
    for item in result:
        print(f"  {item}")

    expected_provinces = ['山东省', '上海市', '四川省', '江苏省', '香港特别行政区']
    actual_provinces = [item['province'] for item in result]

    if actual_provinces == expected_provinces:
        print("\n✓ 城市列表规范化正确")
        return True
    else:
        print(f"\n✗ 城市列表规范化失败")
        print(f"期望: {expected_provinces}")
        print(f"实际: {actual_provinces}")
        return False


def main():
    """运行所有测试"""
    print("\n")
    print("=" * 60)
    print("地理位置规范化测试")
    print("=" * 60)
    print("用途: 验证数据库短名称到地图标准格式的转换")
    print()

    results = [
        test_single_province_normalization(),
        test_provinces_list_normalization(),
        test_cities_with_provinces_normalization(),
    ]

    print("\n" + "=" * 60)
    if all(results):
        print("✓ 所有测试通过!")
        print("=" * 60)
        return 0
    else:
        print("✗ 有测试失败!")
        print("=" * 60)
        return 1


if __name__ == '__main__':
    exit(main())
