<template>
  <section class="app-main">
    <router-view v-slot="{ Component }">
      <transition name="fade-transform" mode="out-in">
        <component :is="Component" :key="key" />
      </transition>
    </router-view>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

// 路由key，确保路由切换时组件能正确更新
const key = computed(() => route.path)
</script>

<style lang="scss" scoped>
.app-main {
  min-height: calc(100vh - var(--layout-header-height));
  width: 100%;
  position: relative;
  overflow: auto;
  padding: 20px;
  background-color: var(--el-bg-color-page);
}

.fixed-header + .app-main {
  padding-top: var(--layout-header-height);
}

.fade-transform-leave-active,
.fade-transform-enter-active {
  transition: all 0.5s;
}

.fade-transform-enter-from {
  opacity: 0;
  transform: translateX(-30px);
}

.fade-transform-leave-to {
  opacity: 0;
  transform: translateX(30px);
}
</style>