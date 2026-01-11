# -*- coding: utf-8 -*-
"""
地理位置辅助函数
- 规范化省份名称（统一转换为地图所需的标准格式）
- 处理各级地理位置的显示和存储格式转换

说明：
- 数据库存储简短名称（如"山东"、"北京"）便于AC自动机匹配
- API返回时统一转换为地图标准格式（ECharts中国地图需要的格式）
"""

# 完整的省级行政单位映射：简短名称 -> 地图标准名称
# 确保与 /frontend/public/big_screen_assets/js/china.json 中的名称一致
PROVINCE_MAP = {
    # 普通省份（+省字）
    '河北': '河北省',
    '山西': '山西省',
    '辽宁': '辽宁省',
    '吉林': '吉林省',
    '黑龙江': '黑龙江省',
    '江苏': '江苏省',
    '浙江': '浙江省',
    '安徽': '安徽省',
    '福建': '福建省',
    '江西': '江西省',
    '山东': '山东省',
    '河南': '河南省',
    '湖北': '湖北省',
    '湖南': '湖南省',
    '广东': '广东省',
    '云南': '云南省',
    '贵州': '贵州省',
    '四川': '四川省',
    '陕西': '陕西省',
    '甘肃': '甘肃省',
    '青海': '青海省',
    '台湾': '台湾省',

    # 直辖市（+市字）
    '北京': '北京市',
    '天津': '天津市',
    '上海': '上海市',
    '重庆': '重庆市',

    # 自治区（特殊格式）
    '内蒙古': '内蒙古自治区',
    '广西': '广西壮族自治区',
    '宁夏': '宁夏回族自治区',
    '新疆': '新疆维吾尔自治区',
    '西藏': '西藏自治区',

    # 特别行政区（特殊格式）
    '香港': '香港特别行政区',
    '澳门': '澳门特别行政区',

    # 已经是标准格式的备选名称（用于容错）
    '河北省': '河北省',
    '山西省': '山西省',
    '辽宁省': '辽宁省',
    '吉林省': '吉林省',
    '黑龙江省': '黑龙江省',
    '江苏省': '江苏省',
    '浙江省': '浙江省',
    '安徽省': '安徽省',
    '福建省': '福建省',
    '江西省': '江西省',
    '山东省': '山东省',
    '河南省': '河南省',
    '湖北省': '湖北省',
    '湖南省': '湖南省',
    '广东省': '广东省',
    '云南省': '云南省',
    '贵州省': '贵州省',
    '四川省': '四川省',
    '陕西省': '陕西省',
    '甘肃省': '甘肃省',
    '青海省': '青海省',
    '台湾省': '台湾省',
    '北京市': '北京市',
    '天津市': '天津市',
    '上海市': '上海市',
    '重庆市': '重庆市',
    '内蒙古自治区': '内蒙古自治区',
    '广西壮族自治区': '广西壮族自治区',
    '宁夏回族自治区': '宁夏回族自治区',
    '新疆维吾尔自治区': '新疆维吾尔自治区',
    '西藏自治区': '西藏自治区',
    '香港特别行政区': '香港特别行政区',
    '澳门特别行政区': '澳门特别行政区',
}


def normalize_province_name(province: str) -> str:
    """
    规范化省份名称为地图标准格式

    用途：
    - 数据库存储简短名称（便于文本匹配和AC自动机）
    - API返回时统一转换为地图标准格式（符合ECharts中国地图期望）

    Args:
        province: 省份名称（可以是简短形式或标准形式）

    Returns:
        str: 地图标准格式的省份名称，如果不在映射表中则返回原值

    Examples:
        >>> normalize_province_name('山东')
        '山东省'
        >>> normalize_province_name('山东省')
        '山东省'
        >>> normalize_province_name('北京')
        '北京市'
        >>> normalize_province_name('宁夏')
        '宁夏回族自治区'
        >>> normalize_province_name('香港')
        '香港特别行政区'
        >>> normalize_province_name(None)
        None
    """
    if not province or not isinstance(province, str):
        return province

    province = province.strip()
    if not province:
        return province

    # 查表转换
    if province in PROVINCE_MAP:
        return PROVINCE_MAP[province]

    # 未在映射表中，保持原值（可能是输入错误，但不破坏数据）
    return province


def normalize_provinces_list(provinces_list: list) -> list:
    """
    批量规范化省份列表（用于API返回数据）

    Args:
        provinces_list: 省份字典列表，每个字典包含 'name' 和 'value' 字段

    Returns:
        list: 规范化后的省份列表

    Example:
        >>> normalize_provinces_list([
        ...     {'name': '山东', 'value': 100},
        ...     {'name': '北京', 'value': 50}
        ... ])
        [
            {'name': '山东省', 'value': 100},
            {'name': '北京市', 'value': 50}
        ]
    """
    if not provinces_list:
        return []

    result = []
    for item in provinces_list:
        if isinstance(item, dict) and 'name' in item:
            normalized_item = item.copy()
            normalized_item['name'] = normalize_province_name(item['name'])
            result.append(normalized_item)
        else:
            result.append(item)

    return result


def normalize_cities_with_provinces(cities_list: list) -> list:
    """
    批量规范化城市列表（规范化其所属省份字段）

    用于处理 all_cities 和 shandong_cities 的返回数据

    Args:
        cities_list: 城市字典列表，包含 'name'、'value' 和 'province' 字段

    Returns:
        list: 规范化后的城市列表

    Example:
        >>> normalize_cities_with_provinces([
        ...     {'name': '青岛', 'value': 200, 'province': '山东'},
        ...     {'name': '成都', 'value': 150, 'province': '四川'}
        ... ])
        [
            {'name': '青岛', 'value': 200, 'province': '山东省'},
            {'name': '成都', 'value': 150, 'province': '四川省'}
        ]
    """
    if not cities_list:
        return []

    result = []
    for item in cities_list:
        if isinstance(item, dict):
            normalized_item = item.copy()
            # 规范化所属省份（核心字段）
            if 'province' in normalized_item:
                normalized_item['province'] = normalize_province_name(normalized_item['province'])
            result.append(normalized_item)
        else:
            result.append(item)

    return result


def get_all_provinces() -> dict:
    """
    获取所有省级行政单位的完整映射表

    Returns:
        dict: 简短名称 -> 地图标准名称的映射
    """
    return PROVINCE_MAP.copy()


def get_map_standard_name(short_name: str) -> str:
    """
    获取某个地区的地图标准名称（别名）

    Args:
        short_name: 简短名称（如"山东"）

    Returns:
        str: 地图标准名称（如"山东省"），如果不存在则返回 None
    """
    return PROVINCE_MAP.get(short_name)
