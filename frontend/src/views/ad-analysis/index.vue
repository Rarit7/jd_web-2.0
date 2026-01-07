<template>
  <div class="analysis-page">
    <!-- 标签页容器 -->
    <el-tabs v-model="activeTab" class="analysis-tabs">
      <!-- 黑词分析 -->
      <el-tab-pane label="黑词分析" name="dark-keywords">
        <DarkKeywordsTab />
      </el-tab-pane>

      <!-- 交易方式 -->
      <el-tab-pane label="交易方式" name="transaction-methods">
        <TransactionMethodTab />
      </el-tab-pane>

      <!-- 价格趋势 -->
      <el-tab-pane label="价格趋势" name="price-trend">
        <PriceTrendTab />
      </el-tab-pane>

      <!-- 热点地区 -->
      <el-tab-pane label="热点地区" name="geo-location">
        <GeoLocationTab />
      </el-tab-pane>

      <!-- 数据源选择 -->
      <el-tab-pane label="数据源选择" name="data-source">
        <DataSourceSelector />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import DarkKeywordsTab from './components/dark-keywords/DarkKeywordsTab.vue'
import TransactionMethodTab from './components/transaction-methods/TransactionMethodTab.vue'
import PriceTrendTab from './components/price-trend/PriceTrendTab.vue'
import GeoLocationTab from './components/geo-location/GeoLocationTab.vue'
import DataSourceSelector from './components/DataSourceSelector.vue'

// 当前激活的标签页
const activeTab = ref('dark-keywords')
</script>

<style scoped lang="scss">
.analysis-page {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: calc(100vh - 60px);

  .analysis-tabs {
    :deep(.el-tabs__header) {
      margin-bottom: 20px;
      background-color: white;
      padding: 0 10px;
      border-radius: 4px;
    }

    :deep(.el-tabs__nav-wrap::after) {
      background-color: #e4e7ed;
    }

    :deep(.el-tabs__item) {
      font-size: 16px;
      font-weight: 500;
      color: #606266;
      padding: 0 20px;

      &.is-active {
        color: #409eff;
      }

      &:hover {
        color: #409eff;
      }
    }

    :deep(.el-tabs__content) {
      padding: 20px;
      background-color: white;
      border-radius: 4px;
    }
  }
}
</style>
