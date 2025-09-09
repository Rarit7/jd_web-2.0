<template>
  <div class="drawer-container">
    <div class="drawer-title">
      <h4>系统设置</h4>
    </div>
    
    <div class="drawer-item">
      <span>固定头部</span>
      <el-switch v-model="fixedHeader" />
    </div>
    
    <div class="drawer-item">
      <span>显示标签栏</span>
      <el-switch v-model="showTagsView" />
    </div>
    
    <div class="drawer-item">
      <span>显示侧边栏Logo</span>
      <el-switch v-model="showSidebarLogo" />
    </div>
    
    <div class="drawer-item">
      <span>显示面包屑导航</span>
      <el-switch v-model="showBreadcrumb" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useSettingsStore } from '@/store/modules/settings'

const settingsStore = useSettingsStore()

const fixedHeader = computed({
  get: () => settingsStore.fixedHeader,
  set: (value) => settingsStore.updateSettings({ fixedHeader: value })
})

const showTagsView = computed({
  get: () => settingsStore.showTagsView,
  set: (value) => settingsStore.updateSettings({ showTagsView: value })
})

const showSidebarLogo = computed({
  get: () => settingsStore.showSidebarLogo,
  set: (value) => settingsStore.updateSettings({ showSidebarLogo: value })
})

const showBreadcrumb = computed({
  get: () => settingsStore.showBreadcrumb,
  set: (value) => settingsStore.updateSettings({ showBreadcrumb: value })
})
</script>

<style lang="scss" scoped>
.drawer-container {
  padding: 24px;
  font-size: 14px;
  line-height: 1.5;
  word-wrap: break-word;
}

.drawer-title {
  margin-bottom: 12px;
  color: var(--el-text-color-primary);
  font-size: 14px;
  line-height: 22px;
}

.drawer-item {
  color: var(--el-text-color-primary);
  font-size: 14px;
  padding: 12px 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.drawer-item span {
  flex: 1;
}
</style>