/**
 * DashboardScreen页面工具函数和常量
 * 只提取纯工具函数和常量数据，不涉及响应式状态
 */

/**
 * 山东省城市坐标数据
 */
export const geoCoordMap = {
  '济南': [117, 36.65],
  '青岛': [120.33, 36.07],
  '淄博': [118.05, 36.78],
  '枣庄': [117.57, 34.86],
  '东营': [118.49, 37.46],
  '烟台': [121.39, 37.52],
  '潍坊': [119.1, 36.62],
  '济宁': [116.59, 35.38],
  '泰安': [117.13, 36.18],
  '威海': [122.1, 37.5],
  '日照': [119.46, 35.42],
  '临沂': [118.35, 35.05],
  '德州': [116.29, 37.45],
  '聊城': [115.97, 36.45],
  '滨州': [118.03, 37.36],
  '菏泽': [115.480656, 35.23375]
} as const

/**
 * 城市名拼音映射（包含带"市"字的版本）
 */
export const cityPinyinMap = {
  // 不带市字的版本
  '济南': 'jinan',
  '青岛': 'qingdao',
  '淄博': 'zibo',
  '枣庄': 'zaozhuang',
  '东营': 'dongying',
  '烟台': 'yantai',
  '潍坊': 'weifang',
  '济宁': 'jining',
  '泰安': 'taian',
  '威海': 'weihai',
  '日照': 'rizhao',
  '临沂': 'linyi',
  '德州': 'dezhou',
  '聊城': 'liaocheng',
  '滨州': 'binzhou',
  '菏泽': 'heze',
  // 带市字的版本
  '济南市': 'jinan',
  '青岛市': 'qingdao',
  '淄博市': 'zibo',
  '枣庄市': 'zaozhuang',
  '东营市': 'dongying',
  '烟台市': 'yantai',
  '潍坊市': 'weifang',
  '济宁市': 'jining',
  '泰安市': 'taian',
  '威海市': 'weihai',
  '日照市': 'rizhao',
  '临沂市': 'linyi',
  '德州市': 'dezhou',
  '聊城市': 'liaocheng',
  '滨州市': 'binzhou',
  '菏泽市': 'heze'
} as const

/**
 * 转换地图数据格式，将城市名和数值转换为地图坐标格式
 * @param data 原始数据数组，每项包含name和value
 * @returns 转换后的数据数组，包含name和value（坐标+数值）
 */
export const convertData = (data: any[]) => {
  const res = []
  for (let i = 0; i < data.length; i++) {
    const geoCoord = geoCoordMap[data[i].name as keyof typeof geoCoordMap]
    if (geoCoord) {
      res.push({
        name: data[i].name,
        value: geoCoord.concat(data[i].value)
      })
    }
  }
  return res
}

/**
 * 获取城市地图中心点坐标
 * @param cityPinyin 城市拼音
 * @returns 中心点坐标 [经度, 纬度]
 */
export const getCityCenter = (cityPinyin: string): [number, number] => {
  const cityNames = Object.keys(cityPinyinMap)
  const cityName = cityNames.find(name =>
    cityPinyinMap[name as keyof typeof cityPinyinMap] === cityPinyin
  )

  if (cityName) {
    const cleanCityName = cityName.replace('市', '')
    const coord = geoCoordMap[cleanCityName as keyof typeof geoCoordMap] || geoCoordMap[cityName as keyof typeof geoCoordMap]
    if (coord) {
      // 城市地图轻微调整位置
      return [coord[0], coord[1] - 0.1]
    }
  }

  // 默认中心点（山东省中心）
  return [118.5, 37.0]
}
