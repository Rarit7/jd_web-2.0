<template>
  <div class="big-screen" :class="layoutClasses">
    <!-- 加载动画 -->
    <div v-if="pageLoading" class="loading">
      <div class="loadbox">
        <div class="loading-spinner"></div>
        页面加载中...
      </div>
    </div>

    <!-- 主体内容 -->
    <div class="mainbox">
      <ul class="clearfix">
        <!-- 左侧面板 -->
        <li class="left-panel">
          <!-- 图表2: 地区分布 (上半部分) -->
          <div class="boxall chart-box half-chart">
            <div class="alltitle">{{ echart2Data.title }}</div>
            <div class="allnav" ref="echart2"></div>
            <div class="boxfoot"></div>
          </div>
          
          <!-- 词云图表 (下半部分) -->
          <div class="boxall chart-box half-chart">
            <div class="alltitle">{{ wordCloudData.title }}</div>
            <div class="allnav" ref="wordCloud"></div>
            <div class="boxfoot"></div>
          </div>
        </li>

        <!-- 中央面板 -->
        <li class="center-panel">
          <!-- 标题卡片 -->
          <div class="boxall title-card">
            <div class="main-title">电报黑词监控可视化大屏</div>
          </div>
          
          <!-- 地图 -->
          <div class="map">
            <div class="map4" ref="map1"></div>
            <!-- 地图导航提示 -->
            <div class="map-navigation-hint">
              <div v-if="currentMapLevel === 'china'" class="hint-text">
                点击山东省区域进入省级地图
              </div>
              <div v-else-if="currentMapLevel === 'shandong'" class="hint-text">
                点击城市进入城市地图 | 双击空白区域返回中国地图
              </div>
              <div v-else-if="currentMapLevel === 'city'" class="hint-text">
                {{ currentCity }}市地图 | 双击空白区域返回山东省地图
              </div>
            </div>
          </div>
          
        </li>

        <!-- 右侧面板 -->
        <li class="right-panel">
          <!-- 折线图 -->
          <div class="boxall chart-box medium">
            <div class="alltitle">{{ echart4Data.title }}</div>
            <div class="allnav" ref="echart4"></div>
            <div class="boxfoot"></div>
          </div>
          
          <!-- 柱状图 -->
          <div class="boxall chart-box">
            <div class="alltitle">{{ echart5Data.title }}</div>
            <div class="allnav" ref="echart5"></div>
            <div class="boxfoot"></div>
          </div>
          
          <!-- 多层饼图 -->
          <div class="boxall chart-box small">
            <div class="alltitle">{{ echart6Data.title }}</div>
            <div class="allnav" ref="echart6"></div>
            <div class="boxfoot"></div>
          </div>
        </li>
      </ul>
    </div>

    <!-- 背景装饰 -->
    <div class="back"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick, computed } from 'vue'
import echarts from '@/utils/echarts'
import 'echarts-wordcloud'
import { useAppStore } from '@/store/modules/app'
import { toUTC8 } from '@/utils/date'

const appStore = useAppStore()

// 布局相关计算属性
const layoutClasses = computed(() => ({
  hideSidebar: !appStore.sidebar.opened,
  mobile: appStore.device === 'mobile'
}))

const pageLoading = ref(true)
const currentTime = ref('')
const title = ref('TG_涉毒数据可视化大屏')

// 图表引用
const echart2 = ref()
const echart4 = ref()
const echart5 = ref()
const echart6 = ref()
const wordCloud = ref()
const map1 = ref()

// 地图状态管理
const currentMapLevel = ref('china') // 'china', 'shandong', 'city'
const currentCity = ref('') // 当前选中的城市
const mapHistory = ref(['china']) // 地图历史栈，用于返回上级
const loadedMaps = ref(new Set(['china'])) // 已加载的地图缓存

// 统计数据
const counterData = ref({
  name: '数据1',
  value: '1,111'
})

const counter2Data = ref({
  name: '数据2', 
  value: '2,222'
})


const echart2Data = ref({
  title: '地区分布',
  categories: ['济南', '青岛', '烟台', '潍坊', '临沂', '淄博', '威海'],
  series: [
    { name: '敏感词', data: [89, 95, 123, 108, 134, 87, 98] },
    { name: '违禁词', data: [35, 28, 42, 46, 39, 31, 33] },
    { name: '涉毒词汇', data: [23, 29, 25, 30, 26, 19, 19] }
  ]
})

// 词云数据
const wordCloudData = ref({
  title: '关键词云',
  data: [
    { name: '数据分析', value: 180 },
    { name: '机器学习', value: 165 },
    { name: '人工智能', value: 150 },
    { name: '大数据', value: 135 },
    { name: '云计算', value: 120 },
    { name: '深度学习', value: 110 },
    { name: '算法优化', value: 95 },
    { name: '数据挖掘', value: 88 },
    { name: '可视化', value: 82 },
    { name: '预测模型', value: 75 },
    { name: '统计分析', value: 68 },
    { name: '神经网络', value: 60 },
    { name: '自然语言', value: 55 },
    { name: '图像识别', value: 50 },
    { name: '智能推荐', value: 45 }
  ]
})


const echart4Data = ref({
  title: '月度趋势分析',
  data: [
    { name: '产量', value: [3, 4, 3, 4, 3, 4, 3, 6, 2, 4, 2, 4, 3, 4, 3, 4, 3, 4, 3, 6, 2, 4, 4] },
    { name: '销量', value: [5, 3, 5, 6, 1, 5, 3, 5, 6, 4, 6, 4, 8, 3, 5, 6, 1, 5, 3, 7, 2, 5, 8] }
  ],
  xAxis: ['01', '02', '03', '04', '05', '06', '07', '08', '09', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23', '24']
})

const echart5Data = ref({
  title: '城市排名TOP',
  data: [
    { name: '济南', value: 20 },
    { name: '青岛', value: 18 },
    { name: '烟台', value: 15 },
    { name: '潍坊', value: 13 },
    { name: '临沂', value: 9 },
    { name: '淄博', value: 8 },
    { name: '威海', value: 7 },
    { name: '泰安', value: 6 }
  ]
})

const echart6Data = ref({
  title: '重点城市占比',
  data: [
    { name: '济南', value: 235 },
    { name: '青岛', value: 198 },
    { name: '烟台', value: 167 },
    { name: '潍坊', value: 142 },
    { name: '临沂', value: 128 },
    { name: '淄博', value: 95 },
    { name: '威海', value: 87 },
    { name: '泰安', value: 76 }
  ]
})

const mapData = ref({
  symbolSize: 100,
  data: [
    { name: '济南', value: 239 },
    { name: '青岛', value: 231 },
    { name: '烟台', value: 203 },
    { name: '潍坊', value: 189 },
    { name: '临沂', value: 156 }
  ]
})

// 图表实例
let chart2: any = null
let chart4: any = null
let chart5: any = null
let chart6: any = null
let mapChart: any = null

// 时间更新函数
const updateTime = () => {
  const now = new Date()
  const utc8Time = new Date(now.toLocaleString('en-US', { timeZone: 'Asia/Shanghai' }))
  const y = utc8Time.getFullYear()
  const mt = utc8Time.getMonth() + 1
  const day = utc8Time.getDate()
  const h = utc8Time.getHours()
  const m = utc8Time.getMinutes()
  const s = utc8Time.getSeconds()
  currentTime.value = `${y}年${mt}月${day}日-${h}时${m}分${s}秒`
}

let timeTimer: NodeJS.Timeout | null = null

// 山东省城市坐标数据
const geoCoordMap = {
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
}

// 城市名拼音映射（包含带"市"字的版本）
const cityPinyinMap = {
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
}

const convertData = (data: any[]) => {
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

// 获取城市地图中心点
const getCityCenter = (cityPinyin: string) => {
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

// 懒加载地图数据
const loadMapData = async (mapType: string) => {
  console.log(`开始加载${mapType}地图数据...`)
  
  // 检查是否已经注册了地图
  if (echarts.getMap(mapType)) {
    console.log(`${mapType}地图数据已注册`)
    return true
  }
  
  // 如果缓存中有但ECharts中没有，清除缓存重新加载
  if (loadedMaps.value.has(mapType)) {
    console.log(`${mapType}地图缓存状态与ECharts不同步，清除缓存`)
    loadedMaps.value.delete(mapType)
  }
  
  try {
    let mapPath = ''
    if (mapType === 'china') {
      mapPath = '/big_screen_assets/js/china.json'
    } else if (mapType === 'shandong') {
      mapPath = '/big_screen_assets/js/shandong.json'
    } else {
      // 城市地图
      mapPath = `/big_screen_assets/js/shandongCities/${mapType}.json`
    }
    
    console.log(`请求地图文件: ${mapPath}`)
    
    const response = await fetch(mapPath)
    
    console.log(`${mapType}地图文件请求响应: ${response.status} ${response.statusText}`)
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    
    const geoJSON = await response.json()
    console.log(`${mapType}地图 GeoJSON 数据解析成功，类型:`, geoJSON.type, '特征数量:', geoJSON.features?.length || 0)
    
    // 验证GeoJSON结构
    if (!geoJSON || !geoJSON.type || geoJSON.type !== 'FeatureCollection') {
      throw new Error(`无效的GeoJSON数据格式: ${geoJSON?.type}`)
    }
    
    // 将 GeoJSON 数据注册到 ECharts
    console.log(`注册${mapType}地图到ECharts...`)
    echarts.registerMap(mapType, geoJSON)
    loadedMaps.value.add(mapType)
    
    // 立即验证注册是否成功
    const registeredMap = echarts.getMap(mapType)
    if (registeredMap) {
      console.log(`${mapType}地图数据注册成功，验证通过`)
      return true
    } else {
      console.error(`${mapType}地图数据注册失败，验证未通过，尝试重新注册...`)
      // 尝试重新注册一次
      try {
        echarts.registerMap(mapType, geoJSON)
        const secondCheck = echarts.getMap(mapType)
        if (secondCheck) {
          console.log(`${mapType}地图数据重新注册成功`)
          return true
        } else {
          console.error(`${mapType}地图数据重新注册仍然失败`)
          return false
        }
      } catch (retryError) {
        console.error(`${mapType}地图数据重新注册异常:`, retryError)
        return false
      }
    }
    
  } catch (error) {
    console.error(`${mapType}地图数据加载失败:`, error)
    return false
  }
}

// 更新地图
const updateMap = async (mapType: string, mapName?: string) => {
  if (!mapChart) {
    console.error('mapChart实例不存在')
    return
  }
  
  console.log(`开始更新地图: ${mapType}`)
  
  // 先加载地图数据
  const success = await loadMapData(mapType)
  if (!success) {
    console.error(`无法加载${mapType}地图数据`)
    return
  }
  
  // 再次验证地图是否已注册
  if (!echarts.getMap(mapType)) {
    console.error(`地图${mapType}仍未注册到ECharts`)
    return
  }
  
  console.log(`地图${mapType}已成功注册，开始设置选项`)
  
  const data = mapData.value.data
  let option: any
  
  if (mapType === 'china') {
    option = {
      tooltip: {
        trigger: 'item',
        formatter: function(params: any) {
          if (params.name === '山东' || params.name === '山东省') {
            return '点击进入山东省地图'
          }
          if (typeof (params.value)?.[2] == 'undefined') {
            return params.name + ' : ' + (params.value || 0)
          } else {
            return params.name + ' : ' + params.value[2]
          }
        }
      },
      geo: {
        map: 'china',
        label: {
          emphasis: {
            show: false
          }
        },
        roam: false,
        itemStyle: {
          normal: {
            areaColor: '#4c60ff',
            borderColor: '#002097'
          },
          emphasis: {
            areaColor: '#293fff'
          }
        }
      },
      series: [{
        name: '数据分布',
        type: 'scatter',
        coordinateSystem: 'geo',
        data: convertData(data),
        symbolSize: function(val: any) {
          return val[2] / mapData.value.symbolSize
        },
        label: {
          normal: {
            formatter: '{b}',
            position: 'right',
            show: false
          },
          emphasis: {
            show: true
          }
        },
        itemStyle: {
          normal: {
            color: '#ffeb7b'
          }
        }
      }]
    }
  } else if (mapType === 'shandong') {
    option = {
      tooltip: {
        trigger: 'item',
        formatter: function(params: any) {
          const cityName = params.name
          if (cityPinyinMap[cityName as keyof typeof cityPinyinMap]) {
            return `${cityName}: 点击进入城市地图`
          }
          if (typeof (params.value)?.[2] == 'undefined') {
            return params.name + ' : ' + (params.value || 0)
          } else {
            return params.name + ' : ' + params.value[2]
          }
        }
      },
      geo: {
        map: 'shandong',
        center: [118.0, 36.0], // 适度调整中心点位置
        zoom: 1.0,
        label: {
          normal: {
            show: true,
            fontSize: 10,
            color: 'rgba(255,255,255,0.8)'
          },
          emphasis: {
            show: true,
            fontSize: 12,
            color: '#fff'
          }
        },
        roam: false,
        itemStyle: {
          normal: {
            areaColor: '#4c60ff',
            borderColor: '#002097'
          },
          emphasis: {
            areaColor: '#293fff'
          }
        }
      },
      series: [{
        name: '数据分布',
        type: 'scatter',
        coordinateSystem: 'geo',
        data: convertData(data),
        symbolSize: function(val: any) {
          return Math.max(val[2] / mapData.value.symbolSize, 8)
        },
        label: {
          normal: {
            formatter: '{b}',
            position: 'right',
            show: false
          },
          emphasis: {
            show: true
          }
        },
        itemStyle: {
          normal: {
            color: '#ffeb7b'
          }
        }
      }]
    }
  } else {
    // 城市地图
    option = {
      tooltip: {
        trigger: 'item',
        formatter: function(params: any) {
          return `${mapName || mapType}: ${params.name || '区域'}`
        }
      },
      geo: {
        map: mapType,
        zoom: 0.9, // 缩小城市地图
        center: getCityCenter(mapType), // 动态获取城市中心点
        label: {
          normal: {
            show: true,
            fontSize: 10,
            color: 'rgba(255,255,255,0.8)'
          },
          emphasis: {
            show: true,
            fontSize: 12,
            color: '#fff'
          }
        },
        roam: false,
        itemStyle: {
          normal: {
            areaColor: '#4c60ff',
            borderColor: '#002097'
          },
          emphasis: {
            areaColor: '#293fff'
          }
        }
      }
    }
  }
  
  mapChart.setOption(option, true)
  
  // 清除旧事件并重新绑定
  mapChart.off('click')
  mapChart.off('dblclick')
  mapChart.on('click', handleMapClick)
  mapChart.on('dblclick', (params: any) => {
    console.log('地图双击事件:', params)
    // 如果双击的是空白区域（没有名称），则返回上级
    if (!params.name) {
      console.log('双击空白区域，返回上级地图')
      handleMapBackClick()
    }
  })
}

// 处理地图点击事件
const handleMapClick = (params: any) => {
  console.log('地图点击事件:', params)
  
  // 如果点击的是空白区域或者没有名称，则忽略
  if (!params.name) {
    console.log('点击空白区域，忽略')
    return
  }
  
  if (currentMapLevel.value === 'china') {
    // 在中国地图上点击山东省
    if (params.name === '山东' || params.name === '山东省') {
      console.log('点击山东省，进入省级地图')
      currentMapLevel.value = 'shandong'
      mapHistory.value.push('shandong')
      updateMap('shandong', '山东省')
    }
  } else if (currentMapLevel.value === 'shandong') {
    // 在山东省地图上点击城市
    const cityName = params.name
    const cityPinyin = cityPinyinMap[cityName as keyof typeof cityPinyinMap]
    console.log(`点击城市: ${cityName}, 拼音: ${cityPinyin}`)
    if (cityPinyin) {
      console.log(`进入${cityName}地图`)
      currentMapLevel.value = 'city'
      // 显示城市名时去掉"市"字
      const displayCityName = cityName.replace('市', '')
      currentCity.value = displayCityName
      mapHistory.value.push(cityPinyin)
      updateMap(cityPinyin, displayCityName)
    } else {
      console.log(`未找到${cityName}的拼音映射`)
    }
  }
  // 城市级别不再有下级，只能返回上级
}

// 处理地图空白区域点击（返回上级）
const handleMapBackClick = () => {
  if (mapHistory.value.length <= 1) return // 已经是最上级
  
  mapHistory.value.pop() // 移除当前级别
  const previousLevel = mapHistory.value[mapHistory.value.length - 1]
  
  if (previousLevel === 'china') {
    currentMapLevel.value = 'china'
    currentCity.value = ''
    updateMap('china')
  } else if (previousLevel === 'shandong') {
    currentMapLevel.value = 'shandong'
    currentCity.value = ''
    updateMap('shandong', '山东省')
  } else {
    // 应该不会到这里，但以防万一
    currentMapLevel.value = 'china'
    currentCity.value = ''
    mapHistory.value = ['china']
    updateMap('china')
  }
}

// 加载中国地图数据（保持向后兼容）
const loadChinaMap = async () => {
  return loadMapData('china')
}

// 初始化所有图表
const initCharts = async () => {
  await nextTick()
  
  try {
    // 先加载地图数据（允许失败）
    console.log('开始加载中国地图数据...')
    try {
      const mapLoadSuccess = await loadChinaMap()
      console.log('中国地图数据加载完成，结果:', mapLoadSuccess)
      
      // 验证地图是否真的注册成功
      if (echarts.getMap('china')) {
        console.log('验证：中国地图已成功注册到ECharts')
      } else {
        console.error('验证失败：中国地图未注册到ECharts')
      }
    } catch (mapLoadError) {
      console.warn('地图数据加载失败，将使用备选方案:', mapLoadError)
    }
    
    // 初始化横向堆叠条形图2
    if (echart2.value) {
      chart2 = echarts.init(echart2.value)
      const option2 = {
        tooltip: {
          trigger: 'axis',
          axisPointer: { type: 'shadow' },
          formatter: function(params: any) {
            let result = params[0].name + '<br/>'
            let total = 0
            params.forEach((item: any) => {
              result += item.marker + item.seriesName + ': ' + item.value + '<br/>'
              total += item.value
            })
            result += '总计: ' + total
            return result
          }
        },
        legend: {
          data: echart2Data.value.series.map(item => item.name),
          textStyle: {
            color: 'rgba(255,255,255,.8)',
            fontSize: '12'
          },
          top: '5px'
        },
        grid: {
          left: '15%',
          top: '40px',
          right: '5%',
          bottom: '5%',
          containLabel: true
        },
        xAxis: {
          type: 'value',
          axisLabel: {
            show: true,
            textStyle: {
              color: 'rgba(255,255,255,.6)',
              fontSize: '12'
            }
          },
          axisTick: { show: false },
          axisLine: {
            show: true,
            lineStyle: {
              color: 'rgba(255,255,255,.1)',
              width: 1,
              type: 'solid'
            }
          },
          splitLine: {
            lineStyle: {
              color: 'rgba(255,255,255,.1)'
            }
          }
        },
        yAxis: {
          type: 'category',
          data: echart2Data.value.categories,
          axisLine: {
            show: true,
            lineStyle: {
              color: 'rgba(255,255,255,.1)',
              width: 1,
              type: 'solid'
            }
          },
          axisTick: { show: false },
          axisLabel: {
            show: true,
            textStyle: {
              color: 'rgba(255,255,255,.8)',
              fontSize: '12'
            }
          }
        },
        series: echart2Data.value.series.map((seriesItem, index) => ({
          name: seriesItem.name,
          type: 'bar',
          stack: 'total',
          data: seriesItem.data,
          barWidth: '60%',
          itemStyle: {
            normal: {
              color: ['#4c60ff', '#27d08a', '#ff6b6b'][index],
              opacity: 0.9
            }
          }
        }))
      }
      chart2.setOption(option2)
    }
    
    // 初始化词云图表
    if (wordCloud.value) {
      try {
        const wordCloudChart = echarts.init(wordCloud.value)
        const colors = ['#4c60ff', '#27d08a', '#2db7f5', '#f50', '#fa541c', '#faad14', '#722ed1', '#eb2f96']
        
        const wordCloudOption = {
          backgroundColor: 'transparent',
          tooltip: {
            show: true,
            formatter: function(params: any) {
              return `${params.name}: ${params.value}`
            }
          },
          series: [{
            type: 'wordCloud',
            gridSize: 2,
            sizeRange: [12, 32],
            rotationRange: [0, 0],
            shape: 'circle',
            width: '100%',
            height: '100%',
            drawOutOfBound: false,
            textStyle: {
              fontFamily: 'Arial, sans-serif',
              fontWeight: 'normal',
              color: function (params: any) {
                return colors[Math.floor(Math.random() * colors.length)]
              }
            },
            emphasis: {
              focus: 'self',
              textStyle: {
                shadowBlur: 5,
                shadowColor: '#333'
              }
            },
            data: wordCloudData.value.data.map(item => ({
              name: item.name,
              value: item.value
            }))
          }]
        }
        
        wordCloudChart.setOption(wordCloudOption)
        console.log('词云初始化成功')
      } catch (error) {
        console.error('词云初始化失败:', error)
      }
    }
    
    
    
    
    // 初始化折线图
    if (echart4.value) {
      chart4 = echarts.init(echart4.value)
      const option4 = {
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            lineStyle: {
              color: '#dddc6b'
            }
          }
        },
        legend: {
          top: '0%',
          data: echart4Data.value.data.map(item => item.name),
          textStyle: {
            color: 'rgba(255,255,255,.5)',
            fontSize: '12'
          }
        },
        grid: {
          left: '10',
          top: '30',
          right: '10',
          bottom: '10',
          containLabel: true
        },
        xAxis: [{
          type: 'category',
          boundaryGap: false,
          axisLabel: {
            textStyle: {
              color: 'rgba(255,255,255,.6)',
              fontSize: 12
            }
          },
          axisLine: {
            lineStyle: {
              color: 'rgba(255,255,255,.2)'
            }
          },
          data: echart4Data.value.xAxis
        }],
        yAxis: [{
          type: 'value',
          axisTick: { show: false },
          axisLine: {
            lineStyle: {
              color: 'rgba(255,255,255,.1)'
            }
          },
          axisLabel: {
            textStyle: {
              color: 'rgba(255,255,255,.6)',
              fontSize: 12
            }
          },
          splitLine: {
            lineStyle: {
              color: 'rgba(255,255,255,.1)'
            }
          }
        }],
        series: [
          {
            name: echart4Data.value.data[0].name,
            data: echart4Data.value.data[0].value,
            type: 'line',
            smooth: true,
            symbol: 'circle',
            symbolSize: 5,
            showSymbol: false,
            lineStyle: {
              normal: {
                color: '#0184d5',
                width: 2
              }
            },
            areaStyle: {
              normal: {
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{
                  offset: 0,
                  color: 'rgba(1, 132, 213, 0.4)'
                }, {
                  offset: 0.8,
                  color: 'rgba(1, 132, 213, 0.1)'
                }], false),
                shadowColor: 'rgba(0, 0, 0, 0.1)'
              }
            },
            itemStyle: {
              normal: {
                color: '#0184d5',
                borderColor: 'rgba(221, 220, 107, .1)',
                borderWidth: 12
              }
            }
          },
          {
            name: echart4Data.value.data[1].name,
            data: echart4Data.value.data[1].value,
            type: 'line',
            smooth: true,
            symbol: 'circle',
            symbolSize: 5,
            showSymbol: false,
            lineStyle: {
              normal: {
                color: '#00d887',
                width: 2
              }
            },
            areaStyle: {
              normal: {
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{
                  offset: 0,
                  color: 'rgba(0, 216, 135, 0.4)'
                }, {
                  offset: 0.8,
                  color: 'rgba(0, 216, 135, 0.1)'
                }], false),
                shadowColor: 'rgba(0, 0, 0, 0.1)'
              }
            },
            itemStyle: {
              normal: {
                color: '#00d887',
                borderColor: 'rgba(221, 220, 107, .1)',
                borderWidth: 12
              }
            }
          }
        ]
      }
      chart4.setOption(option4)
    }
    
    // 初始化柱状图5
    if (echart5.value) {
      chart5 = echarts.init(echart5.value)
      const option5 = {
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'shadow'
          }
        },
        grid: {
          left: '0%',
          top: '10px',
          right: '0%',
          bottom: '2%',
          containLabel: true
        },
        xAxis: [{
          type: 'category',
          data: echart5Data.value.data.map(item => item.name),
          axisLine: {
            show: true,
            lineStyle: {
              color: 'rgba(255,255,255,.1)',
              width: 1,
              type: 'solid'
            }
          },
          axisTick: {
            show: false
          },
          axisLabel: {
            interval: 0,
            show: true,
            splitNumber: 15,
            textStyle: {
              color: 'rgba(255,255,255,.6)',
              fontSize: '12'
            }
          }
        }],
        yAxis: [{
          type: 'value',
          axisLabel: {
            show: true,
            textStyle: {
              color: 'rgba(255,255,255,.6)',
              fontSize: '12'
            }
          },
          axisTick: {
            show: false
          },
          axisLine: {
            show: true,
            lineStyle: {
              color: 'rgba(255,255,255,.1)',
              width: 1,
              type: 'solid'
            }
          },
          splitLine: {
            lineStyle: {
              color: 'rgba(255,255,255,.1)'
            }
          }
        }],
        series: [{
          type: 'bar',
          data: echart5Data.value.data.map(item => item.value),
          barWidth: '35%',
          itemStyle: {
            normal: {
              color: '#2f89cf',
              opacity: 1,
              barBorderRadius: 5
            }
          }
        }]
      }
      chart5.setOption(option5)
    }
    
    // 初始化南丁格尔玫瑰图6
    if (echart6.value) {
      chart6 = echarts.init(echart6.value)
      
      const option6 = {
        color: ['#4c60ff', '#27d08a', '#ff6b6b', '#ffa726', '#ab47bc', '#26c6da', '#66bb6a', '#ffca28'],
        tooltip: {
          trigger: 'item',
          formatter: '{a} <br/>{b} : {c} ({d}%)'
        },
        legend: {
          orient: 'vertical',
          left: 'right',
          top: 'center',
          itemWidth: 10,
          itemHeight: 10,
          itemGap: 8,
          data: echart6Data.value.data.map(item => item.name),
          textStyle: {
            color: 'rgba(255,255,255,.8)',
            fontSize: '11'
          }
        },
        series: [{
          name: '监控数据',
          type: 'pie',
          radius: ['30%', '80%'],
          center: ['40%', '50%'],
          roseType: 'radius',
          itemStyle: {
            borderRadius: 5,
            borderColor: 'rgba(255,255,255,0.1)',
            borderWidth: 1
          },
          label: {
            show: false
          },
          emphasis: {
            label: {
              show: true,
              fontSize: '12',
              fontWeight: 'bold',
              color: '#fff'
            },
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)'
            }
          },
          animationType: 'scale',
          animationEasing: 'elasticOut',
          animationDelay: function (idx: number) {
            return Math.random() * 200;
          },
          data: echart6Data.value.data.map(item => ({
            name: item.name,
            value: item.value
          }))
        }]
      }
      chart6.setOption(option6)
    }
    
    // 初始化地图
    if (map1.value) {
      try {
        console.log('开始初始化地图图表...')
        mapChart = echarts.init(map1.value)
        console.log('ECharts实例创建成功')
        
        // 确保地图数据已加载后再初始化为中国地图
        console.log('开始更新地图为中国地图...')
        await updateMap('china')
        console.log('中国地图初始化完成')
        
        // 添加地图容器的双击事件（用于返回上级）
        if (map1.value) {
          map1.value.addEventListener('dblclick', (e: MouseEvent) => {
            e.preventDefault()
            // 延迟执行，确保先处理单击事件
            setTimeout(() => {
              handleMapBackClick()
            }, 100)
          })
        }
        
        // 添加ECharts的双击事件监听（用于在地图区域双击时返回上级）
        mapChart.on('dblclick', (params: any) => {
          console.log('地图双击事件:', params)
          // 如果双击的是空白区域（没有名称），则返回上级
          if (!params.name) {
            console.log('双击空白区域，返回上级地图')
            handleMapBackClick()
          }
        })
        
      } catch (mapError) {
        console.warn('地图初始化失败，显示替代内容:', mapError)
        // 如果地图初始化失败，显示一个简单的统计图表
        if (map1.value) {
          mapChart = echarts.init(map1.value)
          const fallbackOption = {
            title: {
              text: '数据统计',
              left: 'center',
              textStyle: {
                color: '#fff',
                fontSize: 20
              }
            },
            tooltip: {
              trigger: 'item'
            },
            series: [{
              name: '数据分布',
              type: 'pie',
              center: ['50%', '50%'],
              radius: '60%',
              data: mapData.value.data,
              itemStyle: {
                emphasis: {
                  shadowBlur: 10,
                  shadowOffsetX: 0,
                  shadowColor: 'rgba(0, 0, 0, 0.5)'
                }
              },
              label: {
                color: '#fff'
              }
            }]
          }
          mapChart.setOption(fallbackOption)
        }
      }
    }
    
    console.log('所有图表初始化完成')
  } catch (error) {
    console.error('图表初始化失败:', error)
  }
}

// 处理窗口大小变化
const handleResize = () => {
  if (chart2) chart2.resize()
  if (chart4) chart4.resize()
  if (chart5) chart5.resize()
  if (chart6) chart6.resize()
  if (mapChart) mapChart.resize()
}

onMounted(async () => {
  console.log('数据大屏页面已挂载')
  
  // 隐藏fixed-header区域
  const fixedHeader = document.querySelector('.fixed-header') as HTMLElement
  if (fixedHeader) {
    fixedHeader.style.display = 'none'
  }
  
  // 重置地图状态
  currentMapLevel.value = 'china'
  currentCity.value = ''
  mapHistory.value = ['china']
  loadedMaps.value.clear()
  
  // 显示页面加载动画
  pageLoading.value = true
  
  // 初始化时间（减少更新频率）
  updateTime()
  timeTimer = setInterval(updateTime, 60000) // 改为每分钟更新一次
  
  try {
    // 初始化图表
    await initCharts()
    
    // 添加窗口resize监听器
    window.addEventListener('resize', handleResize)
    
    // 延迟隐藏加载动画
    setTimeout(() => {
      pageLoading.value = false
    }, 1000) // 减少等待时间
    
  } catch (error) {
    console.error('页面初始化失败:', error)
    pageLoading.value = false
  }
})

onUnmounted(() => {
  console.log('数据大屏页面已卸载')
  
  // 恢复fixed-header区域显示
  const fixedHeader = document.querySelector('.fixed-header') as HTMLElement
  if (fixedHeader) {
    fixedHeader.style.display = ''
  }
  
  // 清理定时器
  if (timeTimer) {
    clearInterval(timeTimer)
  }
  
  // 销毁图表实例
  if (chart2) chart2.dispose()
  if (chart4) chart4.dispose()
  if (chart5) chart5.dispose()
  if (chart6) chart6.dispose()
  if (mapChart) mapChart.dispose()
  
  // 移除窗口resize监听器
  window.removeEventListener('resize', handleResize)
})

// 设置响应式字体大小
if (typeof window !== 'undefined') {
  const setFontSize = () => {
    const whei = window.innerWidth
    document.documentElement.style.fontSize = whei / 20 + 'px'
  }
  
  window.addEventListener('load', setFontSize)
  window.addEventListener('resize', setFontSize)
  
  // 初始设置
  setFontSize()
}
</script>

<style scoped>
@font-face {
  font-family: electronicFont;
  src: url('/big_screen_assets/font/DS-DIGIT.TTF');
}

* {
  -webkit-box-sizing: border-box;
  -moz-box-sizing: border-box;
  box-sizing: border-box;
  padding: 0px;
  margin: 0px;
  color: #222;
  font-family: '微软雅黑';
}

.big-screen {
  width: calc(100% - 220px);
  height: 100vh;
  background: #0B1426;
  color: #666;
  font-size: 0.1rem;
  overflow: hidden;
  position: fixed;
  top: 0;
  left: 220px;
  right: 0;
  bottom: 0;
}

.clearfix:after, .clearfix:before {
  display: table;
  content: ' ';
}

.clearfix:after {
  clear: both;
}

.pulll_left {
  float: left;
}

.pulll_right {
  float: right;
}

/* 加载动画 */
.loading {
  position: fixed;
  left: 0;
  top: 0;
  font-size: 18px;
  z-index: 100000000;
  width: 100%;
  height: 100%;
  background: #1a1a1c;
  text-align: center;
}

.loadbox {
  position: absolute;
  width: 160px;
  height: 150px;
  color: #aaa;
  left: 50%;
  top: 50%;
  margin-top: -100px;
  margin-left: -75px;
}

.loading-spinner {
  margin: 10px auto;
  display: block;
  width: 40px;
  height: 40px;
  border: 3px solid #333;
  border-top: 3px solid #666;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}


/* 主体内容 */
.mainbox {
  padding: 0.15rem 0.15rem 0rem 0.15rem;
  height: 100vh;
  display: flex;
}

.mainbox > ul {
  list-style: none;
  margin: 0;
  padding: 0;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: stretch;
}

.mainbox > ul > li {
  padding: 0 0.15rem;
  height: 100%;
}

.left-panel,
.right-panel {
  width: 25%;
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.center-panel {
  width: 50%;
  padding: 0;
  display: flex;
  flex-direction: column;
}

/* 图表容器 - 简约圆角矩形 */
.boxall {
  background: #1C2236;
  border: 1px solid #2a3145;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
  position: relative;
  z-index: 10;
}


.alltitle {
  font-size: 18px;
  color: #ffffff;
  font-weight: 500;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid #3a4258;
}

.allnav {
  height: calc(100% - 60px);
  min-height: 200px;
}

.boxfoot {
  display: none;
}

/* 图表高度设置 */
.chart-box {
  height: 400px;
  flex: 1;
}

.title-card {
  height: 80px;
  flex: none;
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: none;
}

.main-title {
  font-size: 28px;
  font-weight: 600;
  color: #ffffff;
  text-align: center;
  font-family: 'Microsoft YaHei', 'PingFang SC', 'Helvetica Neue', Arial, sans-serif;
  letter-spacing: 2px;
  margin: 0;
  padding: 0;
}

.chart-box.small {
  height: 350px;
  flex: none;
}

.chart-box.medium {
  height: 420px;
  flex: 1;
}

.chart-box.half-chart {
  height: 300px;
  flex: 1;
  margin-bottom: 20px;
}

.chart-box .allnav {
  height: calc(100% - 60px);
}

/* 饼图组合 */
.pie-charts {
  height: 3.2rem;
}

.pie-container {
  height: calc(100% - 0.6rem);
  display: flex;
  justify-content: space-between;
}

.sy {
  width: 32%;
  height: 100%;
}

/* 统计数字区域 */
.bar {
  background: rgba(101, 132, 226, 0.1);
  padding: 0.15rem;
  position: relative;
  margin-bottom: 0.2rem;
}

.bar:before,
.bar:after {
  position: absolute;
  width: 0.3rem;
  height: 0.1rem;
  content: '';
}

.bar:before {
  border-left: 2px solid #02a6b5;
  left: 0;
  border-top: 2px solid #02a6b5;
}

.bar:after {
  border-right: 2px solid #02a6b5;
  right: 0;
  bottom: 0;
  border-bottom: 2px solid #02a6b5;
}

.barbox {
  border: 1px solid rgba(25, 186, 139, 0.17);
  position: relative;
}

.barbox li,
.barbox2 li {
  width: 50%;
  text-align: center;
  position: relative;
  z-index: 100;
}

.barbox li:first-child:before {
  position: absolute;
  content: '';
  height: 50%;
  width: 1px;
  background: rgba(255, 255, 255, 0.2);
  right: 0;
  top: 25%;
}

.barbox li {
  font-size: 0.7rem;
  color: #ffeb7b;
  padding: 0.05rem 0;
  font-family: electronicFont;
  font-weight: bold;
}

.barbox2 li {
  font-size: 0.19rem;
  color: rgba(255, 255, 255, 0.7);
  padding-top: 0.1rem;
}

/* 地图区域 */
.map {
  position: relative;
  height: 8.5rem;
  z-index: 9;
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 地图导航提示 */
.map-navigation-hint {
  position: absolute;
  bottom: 0.1rem;
  left: 50%;
  transform: translateX(-50%);
  z-index: 20;
}

.hint-text {
  background: rgba(0, 0, 0, 0.7);
  color: rgba(255, 255, 255, 0.9);
  padding: 0.05rem 0.15rem;
  border-radius: 0.05rem;
  font-size: 0.12rem;
  text-align: center;
  border: 1px solid rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(5px);
  white-space: nowrap;
}

.map4 {
  width: 100%;
  height: 8rem;
  position: relative;
  left: 0;
  top: -0.5rem; /* 向上偏移0.5rem */
  margin: 0 auto;
  z-index: 5;
  display: flex;
  align-items: center;
  justify-content: center;
}


/* 背景 */
.back {
  position: fixed;
  width: 100%;
  height: 100%;
  top: 0;
  left: 0;
  z-index: -1;
}

/* 侧边栏折叠时的样式调整 */
.hideSidebar .big-screen {
  width: calc(100% - 64px);
  left: 64px;
}

/* 移动端样式 */
.mobile .big-screen {
  width: 100%;
  left: 0;
}

/* 响应式设计 */
@media (max-width: 1600px) {
  html {
    font-size: 18px;
  }
}

@media (max-width: 1200px) {
  html {
    font-size: 16px;
  }
  
  .mainbox > ul {
    flex-direction: column;
    overflow-y: auto;
  }
  
  .left-panel,
  .right-panel {
    width: 100%;
    height: auto;
    margin-bottom: 0.2rem;
  }
  
  .center-panel {
    width: 100%;
    height: auto;
  }
  
  .chart-box {
    height: 2.5rem;
  }
  
  .map {
    height: 5rem;
  }
  
  .map4 {
    width: 100%;
    left: 0;
    height: 4.5rem;
  }
}

@media (max-width: 768px) {
  html {
    font-size: 14px;
  }
  
  .chart-box {
    height: 2.5rem;
  }
  
  .map {
    height: 5rem;
  }
}

/* 初始化时设置根元素字体大小 */
html {
  font-size: calc(100vw / 20);
}
</style>

