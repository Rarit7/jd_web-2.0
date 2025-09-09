<template>
  <div @click="toggle">
    <el-icon v-if="isFullscreen" :size="18">
      <FullScreen />
    </el-icon>
    <el-icon v-else :size="18">
      <FullScreen />
    </el-icon>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { FullScreen } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const isFullscreen = ref(false)

const toggle = () => {
  if (isFullscreen.value) {
    exitFullscreen()
  } else {
    enterFullscreen()
  }
}

const enterFullscreen = () => {
  const element = document.documentElement
  if (element.requestFullscreen) {
    element.requestFullscreen()
  } else {
    ElMessage.warning('浏览器不支持全屏操作')
  }
}

const exitFullscreen = () => {
  if (document.exitFullscreen) {
    document.exitFullscreen()
  }
}

const handleFullscreenChange = () => {
  isFullscreen.value = !!document.fullscreenElement
}

onMounted(() => {
  document.addEventListener('fullscreenchange', handleFullscreenChange)
})
</script>

<style scoped>
div {
  cursor: pointer;
  padding: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>