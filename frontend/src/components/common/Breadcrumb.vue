<template>
  <el-breadcrumb class="app-breadcrumb" separator="/">
    <transition-group name="breadcrumb">
      <el-breadcrumb-item v-for="(item, index) in levelList" :key="item.path">
        <span
          v-if="item.redirect === 'noRedirect' || index === levelList.length - 1"
          class="no-redirect"
        >
          {{ item.meta?.title }}
        </span>
        <a v-else @click.prevent="handleLink(item)">
          {{ item.meta?.title }}
        </a>
      </el-breadcrumb-item>
    </transition-group>
  </el-breadcrumb>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { RouteLocationMatched } from 'vue-router'

const route = useRoute()
const router = useRouter()

const levelList = ref<RouteLocationMatched[]>([])

const getBreadcrumb = () => {
  // 只显示有title的路由
  let matched = route.matched.filter(item => item.meta && item.meta.title)
  
  const first = matched[0]
  
  // 如果不是首页，手动添加首页
  if (!isDashboard(first)) {
    matched = [
      { 
        path: '/dashboard', 
        meta: { title: '首页' }
      } as RouteLocationMatched
    ].concat(matched)
  }

  levelList.value = matched.filter(item => {
    return item.meta && item.meta.title && item.meta.breadcrumb !== false
  })
}

const isDashboard = (route?: RouteLocationMatched) => {
  const name = route?.name
  if (!name) {
    return false
  }
  return name.toString().trim() === 'Dashboard'
}

const handleLink = (item: RouteLocationMatched) => {
  const { redirect, path } = item
  if (redirect) {
    router.push(redirect as string)
    return
  }
  router.push(path)
}

// 监听路由变化
watch(
  () => route.path,
  () => getBreadcrumb(),
  { immediate: true }
)
</script>

<style lang="scss" scoped>
.app-breadcrumb.el-breadcrumb {
  display: inline-block;
  font-size: 14px;
  line-height: var(--layout-header-height);

  .no-redirect {
    color: var(--el-text-color-placeholder);
    cursor: text;
  }
}

.breadcrumb-enter-active,
.breadcrumb-leave-active {
  transition: all 0.5s;
}

.breadcrumb-enter-from,
.breadcrumb-leave-active {
  opacity: 0;
  transform: translateX(20px);
}

.breadcrumb-leave-to {
  position: absolute;
}
</style>