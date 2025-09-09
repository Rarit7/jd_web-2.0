<template>
  <div class="app-wrapper" :class="classObj">
    <div v-if="device === 'mobile' && sidebar.opened" class="drawer-bg" @click="handleClickOutside" />
    
    <!-- 侧边栏 -->
    <Sidebar class="sidebar-container" />
    
    <div class="main-container">
      <!-- 顶部导航栏 -->
      <div :class="{ 'fixed-header': fixedHeader }">
        <Navbar />
      </div>
      
      <!-- 主内容区 -->
      <AppMain />
      
      <!-- 右侧设置面板 -->
      <RightPanel v-if="showSettings">
        <Settings />
      </RightPanel>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useWindowSize } from '@vueuse/core'
import Sidebar from './Sidebar/index.vue'
import Navbar from './Navbar.vue'
import AppMain from './AppMain.vue'
import RightPanel from '@/components/common/RightPanel.vue'
import Settings from './Settings/index.vue'
import { useAppStore } from '@/store/modules/app'
import { useSettingsStore } from '@/store/modules/settings'

const appStore = useAppStore()
const settingsStore = useSettingsStore()

// 窗口尺寸
const { width } = useWindowSize()

// 计算属性
const sidebar = computed(() => appStore.sidebar)
const device = computed(() => appStore.device)
const fixedHeader = computed(() => settingsStore.fixedHeader)
const showSettings = computed(() => settingsStore.showSettings)

const classObj = computed(() => ({
  hideSidebar: !sidebar.value.opened,
  openSidebar: sidebar.value.opened,
  withoutAnimation: sidebar.value.withoutAnimation,
  mobile: device.value === 'mobile'
}))

// 监听窗口大小变化
const WIDTH = 992
const isMobile = computed(() => width.value - 1 < WIDTH)

// 点击遮罩层关闭侧边栏
const handleClickOutside = () => {
  appStore.closeSideBar({ withoutAnimation: false })
}

// 根据屏幕宽度设置设备类型
if (isMobile.value) {
  appStore.toggleDevice('mobile')
  appStore.closeSideBar({ withoutAnimation: true })
}
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.app-wrapper {
  position: relative;
  height: 100%;
  width: 100%;
  
  &.mobile.openSidebar {
    position: fixed;
    top: 0;
  }
}

.drawer-bg {
  background: #000;
  opacity: 0.3;
  width: 100%;
  top: 0;
  height: 100%;
  position: absolute;
  z-index: 999;
}

.fixed-header {
  position: fixed;
  top: 0;
  right: 0;
  z-index: 9;
  width: calc(100% - #{$sidebar-width});
  transition: width 0.28s;
}

.hideSidebar .fixed-header {
  width: calc(100% - 64px);
}

.mobile .fixed-header {
  width: 100%;
}

.sidebar-container {
  transition: width 0.28s;
  width: $sidebar-width !important;
  background-color: #1f2d3d;
  height: 100%;
  position: fixed;
  font-size: 0px;
  top: 0;
  bottom: 0;
  left: 0;
  z-index: 1001;
  overflow: hidden;
}

.hideSidebar .sidebar-container {
  pointer-events: none;
  transition-duration: 0.3s;
  transform: translate3d(-$sidebar-width, 0, 0);
}

.main-container {
  min-height: 100%;
  transition: margin-left 0.28s;
  margin-left: $sidebar-width;
  position: relative;
}

.hideSidebar .main-container {
  margin-left: 64px;
}

.sidebar-container.collapse .scrollbar-wrapper {
  overflow-x: hidden !important;
}

.mobile .main-container {
  margin-left: 0px;
}


.withoutAnimation {
  .main-container,
  .sidebar-container {
    transition: none;
  }
}
</style>