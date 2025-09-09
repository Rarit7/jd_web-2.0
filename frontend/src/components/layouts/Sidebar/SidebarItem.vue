<template>
  <div v-if="!item.meta?.hidden">
    <template v-if="hasOneShowingChild(item.children, item) && (!onlyOneChild.children || onlyOneChild.noShowingChildren) && !item.alwaysShow">
      <app-link v-if="onlyOneChild.meta" :to="resolvePath(onlyOneChild.path, onlyOneChild.query)">
        <el-menu-item :index="resolvePath(onlyOneChild.path)" :class="{ 'submenu-title-noDropdown': !isNest }">
          <el-icon v-if="onlyOneChild.meta.icon">
            <component :is="onlyOneChild.meta.icon" />
          </el-icon>
          <template #title>
            <span>{{ onlyOneChild.meta.title }}</span>
          </template>
        </el-menu-item>
      </app-link>
    </template>

    <el-sub-menu v-else :index="resolvePath(item.path)" popper-append-to-body>
      <template #title>
        <el-icon v-if="item.meta?.icon">
          <component :is="item.meta.icon" />
        </el-icon>
        <span>{{ item.meta?.title }}</span>
      </template>
      <sidebar-item
        v-for="child in item.children"
        :key="child.path"
        :is-nest="true"
        :item="child"
        :base-path="child.path"
        class="nest-menu"
      />
    </el-sub-menu>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import AppLink from './Link.vue'
import { isExternal } from '@/utils/validate'

interface RouteItem {
  path: string
  name?: string
  meta?: {
    title?: string
    icon?: string
    hidden?: boolean
    noCache?: boolean
  }
  children?: RouteItem[]
  alwaysShow?: boolean
  query?: Record<string, any>
  noShowingChildren?: boolean
}

interface Props {
  item: RouteItem
  basePath?: string
  isNest?: boolean
}

const props = defineProps<Props>()

const onlyOneChild = ref<RouteItem>({} as RouteItem)

const hasOneShowingChild = (children: RouteItem[] = [], parent: RouteItem) => {
  if (!children) {
    children = []
  }
  const showingChildren = children.filter(item => {
    if (item.meta?.hidden) {
      return false
    } else {
      // 如果只有一个子项，将其设置为onlyOneChild
      onlyOneChild.value = item
      return true
    }
  })

  // 当只有一个子路由时，默认显示子路由
  if (showingChildren.length === 1) {
    return true
  }

  // 如果没有子路由显示，显示父路由
  if (showingChildren.length === 0) {
    onlyOneChild.value = { ...parent, path: '', noShowingChildren: true }
    return true
  }

  return false
}

const resolvePath = (routePath: string, routeQuery?: Record<string, any>) => {
  if (isExternal(routePath)) {
    return routePath
  }
  if (isExternal(props.basePath || '')) {
    return props.basePath
  }
  
  // 如果路径以 / 开头，直接返回
  if (routePath.startsWith('/')) {
    if (routeQuery) {
      let query = JSON.stringify(routeQuery)
      query = query.replace(/:/g, '_')
      return routePath + query
    }
    return routePath
  }
  
  if (routeQuery) {
    let query = JSON.stringify(routeQuery)
    query = query.replace(/:/g, '_')
    return resolve(props.basePath || '', routePath) + query
  }
  return resolve(props.basePath || '', routePath)
}

const resolve = (base: string, path: string) => {
  if (path.startsWith('/')) {
    return path
  }
  return `${base}/${path}`.replace(/\/+/g, '/')
}
</script>

<style lang="scss" scoped>
// 次级菜单样式
.nest-menu .el-sub-menu > .el-sub-menu__title,
.el-sub-menu .el-menu-item {
  background-color: #273849 !important;
  color: #a6b2c5 !important;

  &:hover {
    background-color: #33506c !important;
    color: #ffffff !important;
  }
  
  &.is-active {
    background-color: #409eff !important;
    color: #ffffff !important;
  }
}

.submenu-title-noDropdown {
  &:hover {
    background-color: #263445 !important;
    color: #ffffff !important;
  }
}
</style>