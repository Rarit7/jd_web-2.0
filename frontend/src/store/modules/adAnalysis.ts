/**
 * 数据分析系统 (Ad Analysis) Pinia Store
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  apiGetDarkKeywordCategories,
  apiGetTransactionMethodsList
} from '@/api/adAnalysis'
import type {
  DarkKeywordCategory,
  DarkKeywordData,
  DarkKeywordsPieData,
  DarkKeywordsTrendData,
  TransactionMethodData,
  TransactionMethodTrendData,
  PriceTrendData,
  PriceTrendStatistics,
  PriceHistoryRecord,
  GeoHeatmapData,
  GeoLocationData,
  GeoLocationStatistics
} from '@/types/adAnalysis'

// ============ 全局分析 Store ============

/**
 * 数据分析系统全局共享状态
 * 用于存储整个分析系统共享的参数和状态
 */
export const useAdAnalysisStore = defineStore('adAnalysis', () => {
  // 共享状态
  const selectedChatId = ref<string | null>(null)
  const selectedTagIds = ref<number[]>([])
  const dateRange = ref<[Date, Date] | null>(null)
  const days = ref<number>(365)
  const loading = ref(false)

  // 计算属性
  const isReady = computed(() => selectedChatId.value !== null)

  // 方法
  function selectChat(chatId: string | null) {
    selectedChatId.value = chatId
  }

  function selectTags(tagIds: number[]) {
    selectedTagIds.value = tagIds
  }

  function setDateRange(range: [Date, Date] | null) {
    dateRange.value = range
  }

  function setDays(value: number) {
    days.value = value
  }

  function setLoading(value: boolean) {
    loading.value = value
  }

  return {
    selectedChatId,
    selectedTagIds,
    dateRange,
    days,
    loading,
    isReady,
    selectChat,
    selectTags,
    setDateRange,
    setDays,
    setLoading
  }
})

// ============ 黑词分析 Store ============

/**
 * 黑词分析模块专用状态
 */
export const useDarkKeywordsStore = defineStore('darkKeywords', () => {
  // 状态
  const categories = ref<DarkKeywordCategory[]>([])
  const selectedCategoryId = ref<number | null>(null)
  const selectedDrugId = ref<number | null>(null)

  // 黑词分析数据
  const pieData = ref<DarkKeywordsPieData[]>([])
  const trendData = ref<DarkKeywordsTrendData | null>(null)
  const tableData = ref<DarkKeywordData[]>([])
  const total = ref(0)
  const currentPage = ref(1)
  const pageSize = ref(20)

  // UI 状态
  const activeTab = ref<'analysis' | 'table'>('analysis')
  const searchKeyword = ref('')

  // 计算属性
  const selectedCategory = computed(() =>
    categories.value.find(c => c.id === selectedCategoryId.value)
  )

  const availableDrugs = computed(() =>
    selectedCategory.value?.drugs || []
  )

  // 方法
  async function fetchCategories() {
    try {
      const response = await apiGetDarkKeywordCategories()
      categories.value = response.payload.categories || []
      return categories.value
    } catch (error) {
      console.error('加载分类失败', error)
      return []
    }
  }

  function selectCategory(categoryId: number | null) {
    selectedCategoryId.value = categoryId
    selectedDrugId.value = null
  }

  function selectDrug(drugId: number | null) {
    selectedDrugId.value = drugId
  }

  function setSearchKeyword(keyword: string) {
    searchKeyword.value = keyword
    currentPage.value = 1
  }

  function setActiveTab(tab: 'analysis' | 'table') {
    activeTab.value = tab
  }

  function setPieData(data: DarkKeywordsPieData[]) {
    pieData.value = data
  }

  function setTrendData(data: DarkKeywordsTrendData | null) {
    trendData.value = data
  }

  function setTableData(data: DarkKeywordData[], totalCount: number) {
    tableData.value = data
    total.value = totalCount
  }

  function setCurrentPage(page: number) {
    currentPage.value = page
  }

  function reset() {
    selectedCategoryId.value = null
    selectedDrugId.value = null
    searchKeyword.value = ''
    currentPage.value = 1
    pieData.value = []
    trendData.value = null
    tableData.value = []
    total.value = 0
  }

  return {
    categories,
    selectedCategoryId,
    selectedDrugId,
    pieData,
    trendData,
    tableData,
    total,
    currentPage,
    pageSize,
    activeTab,
    searchKeyword,
    selectedCategory,
    availableDrugs,
    fetchCategories,
    selectCategory,
    selectDrug,
    setSearchKeyword,
    setActiveTab,
    setPieData,
    setTrendData,
    setTableData,
    setCurrentPage,
    reset
  }
})

// ============ 交易方式 Store ============

/**
 * 交易方式模块专用状态
 */
export const useTransactionMethodsStore = defineStore('transactionMethods', () => {
  // 状态
  const methods = ref<Array<{ id: number; name: string }>>([])
  const selectedMethodId = ref<number | null>(null)

  // 分析数据
  const barChartData = ref<TransactionMethodData[]>([])
  const trendData = ref<TransactionMethodTrendData | null>(null)
  const visibleMethods = ref<string[]>([])

  // 统计数据
  const total = ref(0)

  // 方法
  async function fetchMethods() {
    try {
      const response = await apiGetTransactionMethodsList()
      methods.value = response.payload.methods || []
      return methods.value
    } catch (error) {
      console.error('加载交易方式失败', error)
      return []
    }
  }

  function selectMethod(methodId: number | null) {
    selectedMethodId.value = methodId
  }

  function setBarChartData(data: TransactionMethodData[]) {
    barChartData.value = data
    visibleMethods.value = data.map(item => item.name)
  }

  function setTrendData(data: TransactionMethodTrendData | null) {
    trendData.value = data
  }

  function toggleVisibleMethod(methodName: string) {
    const index = visibleMethods.value.indexOf(methodName)
    if (index > -1) {
      visibleMethods.value.splice(index, 1)
    } else {
      visibleMethods.value.push(methodName)
    }
  }

  function setVisibleMethods(methods: string[]) {
    visibleMethods.value = methods
  }

  function setTotal(count: number) {
    total.value = count
  }

  function reset() {
    selectedMethodId.value = null
    barChartData.value = []
    trendData.value = null
    visibleMethods.value = []
    total.value = 0
  }

  return {
    methods,
    selectedMethodId,
    barChartData,
    trendData,
    visibleMethods,
    total,
    fetchMethods,
    selectMethod,
    setBarChartData,
    setTrendData,
    toggleVisibleMethod,
    setVisibleMethods,
    setTotal,
    reset
  }
})

// ============ 价格趋势 Store ============

/**
 * 价格趋势模块专用状态
 */
export const usePriceTrendStore = defineStore('priceTrend', () => {
  // 状态
  const selectedDrugId = ref<number | null>(null)
  const selectedUnit = ref<string | null>(null)

  // 分析数据
  const chartData = ref<PriceTrendData | null>(null)
  const statistics = ref<PriceTrendStatistics | null>(null)
  const historyData = ref<PriceHistoryRecord[]>([])
  const total = ref(0)
  const currentPage = ref(1)
  const pageSize = ref(20)

  // 方法
  function selectDrug(drugId: number | null) {
    selectedDrugId.value = drugId
  }

  function selectUnit(unit: string | null) {
    selectedUnit.value = unit
  }

  function setChartData(data: PriceTrendData | null) {
    chartData.value = data
  }

  function setStatistics(stats: PriceTrendStatistics | null) {
    statistics.value = stats
  }

  function setHistoryData(data: PriceHistoryRecord[], totalCount: number) {
    historyData.value = data
    total.value = totalCount
  }

  function setCurrentPage(page: number) {
    currentPage.value = page
  }

  function reset() {
    selectedDrugId.value = null
    selectedUnit.value = null
    chartData.value = null
    statistics.value = null
    historyData.value = []
    total.value = 0
    currentPage.value = 1
  }

  return {
    selectedDrugId,
    selectedUnit,
    chartData,
    statistics,
    historyData,
    total,
    currentPage,
    pageSize,
    selectDrug,
    selectUnit,
    setChartData,
    setStatistics,
    setHistoryData,
    setCurrentPage,
    reset
  }
})

// ============ 热点地区 Store ============

/**
 * 地理位置模块专用状态
 */
export const useGeoLocationStore = defineStore('geoLocation', () => {
  // 状态
  const selectedProvince = ref<string | null>(null)
  const selectedCity = ref<string | null>(null)
  const availableCities = ref<string[]>([])

  // 分析数据
  const heatmapData = ref<GeoHeatmapData[]>([])
  const pieData = ref<GeoHeatmapData[]>([])
  const barChartData = ref<GeoLocationData[]>([])
  const tableData = ref<GeoLocationData[]>([])
  const statistics = ref<GeoLocationStatistics | null>(null)

  // 分页
  const total = ref(0)
  const currentPage = ref(1)
  const pageSize = ref(20)

  // 山东省城市列表
  const shandongCities = [
    '济南市', '青岛市', '淄博市', '枣庄市', '东营市',
    '烟台市', '潍坊市', '威海市', '济宁市', '泰安市',
    '日照市', '莱芜市', '临沂市', '德州市', '聊城市',
    '滨州市', '菏泽市'
  ]

  // 方法
  function selectProvince(province: string | null) {
    selectedProvince.value = province
    selectedCity.value = null

    // 山东省特殊处理
    if (province === '山东省') {
      availableCities.value = shandongCities
    } else {
      availableCities.value = []
    }
  }

  function selectCity(city: string | null) {
    selectedCity.value = city
  }

  function setHeatmapData(data: GeoHeatmapData[]) {
    heatmapData.value = data
  }

  function setPieData(data: GeoHeatmapData[]) {
    pieData.value = data
  }

  function setBarChartData(data: GeoLocationData[]) {
    barChartData.value = data
  }

  function setTableData(data: GeoLocationData[], totalCount: number) {
    tableData.value = data
    total.value = totalCount
  }

  function setStatistics(stats: GeoLocationStatistics | null) {
    statistics.value = stats
  }

  function setCurrentPage(page: number) {
    currentPage.value = page
  }

  function reset() {
    selectedProvince.value = null
    selectedCity.value = null
    availableCities.value = []
    heatmapData.value = []
    pieData.value = []
    barChartData.value = []
    tableData.value = []
    statistics.value = null
    total.value = 0
    currentPage.value = 1
  }

  return {
    selectedProvince,
    selectedCity,
    availableCities,
    heatmapData,
    pieData,
    barChartData,
    tableData,
    statistics,
    total,
    currentPage,
    pageSize,
    shandongCities,
    selectProvince,
    selectCity,
    setHeatmapData,
    setPieData,
    setBarChartData,
    setTableData,
    setStatistics,
    setCurrentPage,
    reset
  }
})
