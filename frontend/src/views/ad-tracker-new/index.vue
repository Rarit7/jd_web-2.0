<template>
  <div class="tracker-page">
    <el-tabs v-model="activeTab" class="tracker-tabs">
      <!-- 展示标签页 -->
      <el-tab-pane label="广告追踪" name="display">
        <DisplayTab />
      </el-tab-pane>

      <!-- 管理标签页 -->
      <el-tab-pane label="管理" name="management">
        <ManagementTab />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import DisplayTab from './components/DisplayTab.vue'
import ManagementTab from './components/ManagementTab.vue'
import { ElMessage } from 'element-plus'

// 当前激活的标签页
const activeTab = ref('display')

// 监听标签页切换
watch(activeTab, (newTab) => {
  if (newTab === 'display') {
    // 刷新展示页面数据
  } else if (newTab === 'management') {
    // 加载管理页面数据
  }
})
</script>

<style scoped lang="scss">
.tracker-page {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: calc(100vh - 60px);

  .tracker-tabs {
    :deep(.el-tabs__header) {
      margin-bottom: 20px;
    }

    :deep(.el-tabs__nav-wrap::after) {
      background-color: #e4e7ed;
    }

    :deep(.el-tabs__item) {
      font-size: 16px;
      font-weight: 500;
      color: #606266;

      &.is-active {
        color: #409eff;
      }
    }
  }
}
</style>