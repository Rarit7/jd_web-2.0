<template>
  <div class="geo-location-tab">
    <!-- 控制条 -->
    <div class="control-bar">
      <div class="left">
        <el-select
          v-model="selectedProvince"
          placeholder="选择省份"
          clearable
          @change="handleProvinceChange"
          style="width: 150px"
        >
          <el-option
            v-for="province in provinceList"
            :key="province"
            :label="province"
            :value="province"
          />
        </el-select>

        <el-select
          v-model="selectedCity"
          placeholder="选择城市"
          clearable
          :disabled="!availableCities.length"
          @change="handleSearch"
          style="width: 150px; margin-left: 10px"
        >
          <el-option
            v-for="city in availableCities"
            :key="city"
            :label="city"
            :value="city"
          />
        </el-select>

        <el-button type="primary" @click="handleSearch" :loading="loading" style="margin-left: 10px">
          查询
        </el-button>
        <el-button @click="handleReset">
          重置
        </el-button>
      </div>

      <div class="right">
        <span style="margin-right: 10px">数据周期：</span>
        <el-select
          v-model="selectedDays"
          style="width: 150px"
          @change="handleSearch"
        >
          <el-option label="近30天" :value="30" />
          <el-option label="近90天" :value="90" />
          <el-option label="近180天" :value="180" />
          <el-option label="近365天" :value="365" />
        </el-select>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="statistics-cards" v-if="statistics">
      <div class="stat-card">
        <div class="stat-icon">📍</div>
        <div class="stat-info">
          <div class="stat-label">地点总数</div>
          <div class="stat-value">{{ statistics.total_locations }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">🗺️</div>
        <div class="stat-info">
          <div class="stat-label">涉及省份</div>
          <div class="stat-value">{{ statistics.provinces_count }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">🏙️</div>
        <div class="stat-info">
          <div class="stat-label">涉及城市</div>
          <div class="stat-value">{{ statistics.cities_count }}</div>
        </div>
      </div>
    </div>

    <!-- 地图和饼图 -->
    <div class="charts-row">
      <div class="chart-box">
        <h3>地理分布热力</h3>
        <GeoHeatmap
          :data="heatmapData"
          :loading="loading"
        />
      </div>

      <div class="chart-box">
        <h3>地区分布占比</h3>
        <GeoLocationPieChart
          :data="pieData"
          :loading="loading"
        />
      </div>
    </div>

    <!-- 热点排名 -->
    <div class="chart-box full-width" style="margin-top: 20px">
      <h3>热点排名 (TOP 50)</h3>
      <GeoLocationBarChart
        :data="barChartData"
        :loading="loading"
      />
    </div>

    <!-- 表格标签页 -->
    <el-tabs v-model="activeTab" class="data-tabs" style="margin-top: 20px">
      <el-tab-pane label="地理位置数据" name="table">
        <div v-loading="loading" style="padding: 20px">
          <GeoLocationTable
            :data="tableData"
            :loading="loading"
            :total="total"
            :page="currentPage"
            :page-size="pageSize"
            @page-change="handlePageChange"
          />
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  useGeoLocationStore,
  useAdAnalysisStore
} from '@/store/modules/adAnalysis'
import {
  apiGetGeoHeatmap,
  apiGetGeoLocations
} from '@/api/adAnalysis'
import GeoHeatmap from './GeoHeatmap.vue'
import GeoLocationPieChart from './GeoLocationPieChart.vue'
import GeoLocationBarChart from './GeoLocationBarChart.vue'
import GeoLocationTable from './GeoLocationTable.vue'
import type {
  GeoHeatmapData,
  GeoLocationData,
  GeoLocationStatistics
} from '@/types/adAnalysis'

// Stores
const geoLocationStore = useGeoLocationStore()
const analysisStore = useAdAnalysisStore()

// State
const loading = ref(false)
const activeTab = ref('table')
const selectedProvince = ref<string | null>(null)
const selectedCity = ref<string | null>(null)
const selectedDays = ref(365)

const heatmapData = ref<GeoHeatmapData[]>([])
const pieData = ref<GeoHeatmapData[]>([])
const barChartData = ref<GeoLocationData[]>([])
const tableData = ref<GeoLocationData[]>([])
const statistics = ref<GeoLocationStatistics | null>(null)
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

// 中国省份列表
const provinceList = [
  '山东省', '浙江省', '江苏省', '广东省', '福建省',
  '北京', '上海', '天津', '重庆',
  '河北省', '山西省', '内蒙古自治区', '辽宁省', '吉林省', '黑龙江省',
  '安徽省', '江西省', '河南省', '湖北省', '湖南省',
  '广西壮族自治区', '海南省', '四川省', '贵州省', '云南省',
  '西藏自治区', '陕西省', '甘肃省', '青海省', '宁夏回族自治区', '新疆维吾尔自治区'
]

// Computed
const availableCities = computed(() => {
  return geoLocationStore.availableCities
})

// Methods
async function loadData() {
  loading.value = true
  try {
    const params: any = {
      province: selectedProvince.value || undefined,
      city: selectedCity.value || undefined,
      days: selectedDays.value
    }

    // 如果选了 chat_id，则添加到参数中；否则查询全表
    if (analysisStore.selectedChatId) {
      params.chat_id = analysisStore.selectedChatId
    }

    // 并行加载数据
    const [heatmapResponse, locationsResponse] = await Promise.all([
      apiGetGeoHeatmap(params),
      apiGetGeoLocations({
        ...params,
        offset: (currentPage.value - 1) * pageSize.value,
        limit: pageSize.value
      })
    ])

    // 后端热力图返回 {provinces, shandong_cities, all_cities}
    heatmapData.value = heatmapResponse.payload.provinces || []
    pieData.value = heatmapResponse.payload.provinces || []

    // 使用 all_cities 聚合数据
    const allCities = heatmapResponse.payload.all_cities || []
    // 计算总热度值（用于计算占比）
    const totalHeatmapValue = allCities.reduce((sum: number, item: any) => sum + (item.value || 0), 0)

    // 热点排名数据源（带 count 字段）
    barChartData.value = allCities.map((item: any) => ({
      province: item.province,
      city: item.name,
      count: item.value
    }))

    // 表格数据源：聚合数据 + 计算占比
    tableData.value = allCities.map((item: any) => ({
      province: item.province,
      city: item.name,
      count: item.value,
      percentage: totalHeatmapValue > 0 ? (item.value / totalHeatmapValue * 100) : 0
    }))

    // 计算统计信息（基于原始记录总数）
    const totalLocations = locationsResponse.payload.total || 0
    const provinceSet = new Set(allCities.map((item: any) => item.province).filter(Boolean))
    const citiesSet = new Set(allCities.map((item: any) => item.name).filter(Boolean))

    statistics.value = {
      total_locations: totalLocations,
      provinces_count: provinceSet.size,
      cities_count: citiesSet.size
    }

    // 表格显示所有聚合数据，不需要后端分页
    total.value = allCities.length

    geoLocationStore.setHeatmapData(heatmapData.value)
    geoLocationStore.setPieData(pieData.value)
    geoLocationStore.setBarChartData(barChartData.value)
    geoLocationStore.setTableData(tableData.value, total.value)
    geoLocationStore.setStatistics(statistics.value)
  } catch (error) {
    console.error('加载数据失败:', error)
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

function handleProvinceChange() {
  geoLocationStore.selectProvince(selectedProvince.value)
  selectedCity.value = null
  handleSearch()
}

function handleSearch() {
  currentPage.value = 1
  loadData()
}

function handleReset() {
  selectedProvince.value = null
  selectedCity.value = null
  selectedDays.value = 365
  currentPage.value = 1
  geoLocationStore.reset()
  loadData()
}

function handlePageChange(page: number) {
  currentPage.value = page
  loadData()
}

// Lifecycle
onMounted(() => {
  // 页面加载时直接加载数据（可以是全表统计，也可以是特定 chat_id 的统计）
  loadData()
})

// Watch for store changes
watch(
  () => analysisStore.selectedChatId,
  () => {
    // 当 selectedChatId 改变时，重新加载数据
    loadData()
  }
)

// Watch for province selection
watch(
  () => selectedProvince.value,
  (newProvince) => {
    geoLocationStore.selectProvince(newProvince)
    selectedCity.value = null
  }
)

watch(
  () => selectedCity.value,
  (newCity) => {
    geoLocationStore.selectCity(newCity)
  }
)
</script>

<style scoped lang="scss">
.geo-location-tab {
  .control-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding: 15px;
    background-color: #f5f7fa;
    border-radius: 4px;

    .left,
    .right {
      display: flex;
      align-items: center;
      gap: 10px;
    }
  }

  .statistics-cards {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 15px;
    margin-bottom: 20px;

    .stat-card {
      background-color: white;
      padding: 20px;
      border-radius: 8px;
      box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
      display: flex;
      align-items: center;
      gap: 15px;

      .stat-icon {
        font-size: 32px;
      }

      .stat-info {
        .stat-label {
          font-size: 14px;
          color: #909399;
          margin-bottom: 8px;
        }

        .stat-value {
          font-size: 24px;
          font-weight: bold;
          color: #303133;
        }
      }
    }
  }

  .charts-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    margin-bottom: 20px;

    @media (max-width: 1200px) {
      grid-template-columns: 1fr;
    }
  }

  .chart-box {
    background-color: white;
    border-radius: 4px;
    padding: 20px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);

    &.full-width {
      grid-column: 1 / -1;
    }

    h3 {
      margin: 0 0 15px 0;
      font-size: 16px;
      font-weight: 600;
      color: #303133;
    }

    > div {
      min-height: 400px;
    }
  }

  .data-tabs {
    background-color: white;
    border-radius: 4px;
    padding: 0;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);

    :deep(.el-tabs__header) {
      background-color: transparent;
      border-bottom: 1px solid #ebeef5;
    }

    :deep(.el-tabs__content) {
      padding: 0;
    }
  }
}
</style>
