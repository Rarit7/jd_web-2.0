<template>
  <div :class="{ 'has-logo': showLogo }">
    <logo v-if="showLogo" :collapse="isCollapse" />
    <el-scrollbar wrap-class="scrollbar-wrapper">
      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapse"
        :background-color="variables.menuBg"
        :text-color="variables.menuText"
        :unique-opened="false"
        :active-text-color="variables.menuActiveText"
        :collapse-transition="false"
        mode="vertical"
      >
        <sidebar-item
          v-for="route in routes"
          :key="route.path"
          :item="route"
          :base-path="route.path"
        />
      </el-menu>
    </el-scrollbar>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import Logo from './Logo.vue'
import SidebarItem from './SidebarItem.vue'
import variables from '@/styles/variables.module.scss'
import { useAppStore } from '@/store/modules/app'
import { useSettingsStore } from '@/store/modules/settings'
import { useUserStore } from '@/store/modules/user'

const route = useRoute()
const appStore = useAppStore()
const settingsStore = useSettingsStore()
const userStore = useUserStore()

// 路由元信息类型
interface RouteMeta {
  title: string
  icon: string
  affix?: boolean
  roles?: number[]
}

// 菜单路由类型  
interface MenuRoute {
  path: string
  name: string
  meta: RouteMeta
  children?: MenuRoute[]
}

// 检查用户是否有权限访问路由
const hasPermission = (roles?: number[]) => {
  if (!roles || roles.length === 0) return true
  const hasAccess = roles.some(role => userStore.roleIds.includes(role))
  console.log('🔐 Sidebar permission check:', { roles, userRoles: userStore.roleIds, hasAccess })
  return hasAccess
}

// 路由菜单
const routes = computed(() => {
  const allRoutes: MenuRoute[] = [
    {
      path: '/dashboard',
      name: 'Dashboard',
      meta: {
        title: '首页',
        icon: 'House',
        affix: true
      }
    },
    {
      path: '/telegram',
      name: 'Telegram',
      meta: {
        title: 'Telegram监控',
        icon: 'ChatDotRound'
      },
      children: [
        {
          path: '/tg-groups',
          name: 'TgGroups',
          meta: {
            title: '群组管理',
            icon: 'ChatDotRound'
          }
        },
        {
          path: '/tg-users',
          name: 'TgUsers',
          meta: {
            title: '用户信息',
            icon: 'Avatar'
          }
        },
        {
          path: '/chat-history',
          name: 'ChatHistory',
          meta: {
            title: '聊天内容',
            icon: 'ChatLineRound'
          }
        },
        {
          path: '/tg-accounts',
          name: 'TgAccounts',
          meta: {
            title: '监听账户',
            icon: 'Monitor'
          }
        },
        {
          path: '/change_record',
          name: 'ChangeRecord',
          meta: {
            title: '变动分析',
            icon: 'DataAnalysis'
          }
        }
      ]
    },
    {
      path: '/analysis',
      name: 'Analysis',
      meta: {
        title: '分析预警',
        icon: 'Bell'
      },
      children: [
        {
          path: '/user-profile',
          name: 'UserProfile',
          meta: {
            title: '人员档案',
            icon: 'UserFilled'
          }
        },
        {
          path: '/ad-tracking',
          name: 'AdTracking',
          meta: {
            title: '广告追踪',
            icon: 'Warning'
          }
        },
        {
          path: '/tag-manage',
          name: 'TagManage',
          meta: {
            title: '标签管理',
            icon: 'Collection',
            roles: [1]
          }
        },
        {
          path: '/auto-tagging',
          name: 'AutoTagging',
          meta: {
            title: '自动标签',
            icon: 'PriceTag',
            roles: [1]
          }
        },
        {
          path: '/relation-graph',
          name: 'RelationGraph',
          meta: {
            title: '关联图谱',
            icon: 'Share'
          }
        }
      ]
    },
    {
      path: '/dashboard-screen',
      name: 'DashboardScreen',
      meta: {
        title: '数据大屏',
        icon: 'DataBoard'
      }
    },
    {
      path: '/system',
      name: 'System',
      meta: {
        title: '后台管理',
        icon: 'Setting',
        roles: [1]
      },
      children: [
        {
          path: '/user-manage',
          name: 'UserManage',
          meta: {
            title: '用户管理',
            icon: 'User',
            roles: [1]
          }
        },
        {
          path: '/search-queue',
          name: 'SearchQueue',
          meta: {
            title: '抓取进度',
            icon: 'Loading',
            roles: [1]
          }
        },
        {
          path: '/black-words',
          name: 'BlackWords',
          meta: {
            title: '黑词管理',
            icon: 'Warning',
            roles: [1]
          }
        },
        {
          path: '/website-settings',
          name: 'WebsiteSettings',
          meta: {
            title: '网站设置',
            icon: 'Tools',
            roles: [1]
          }
        }
      ]
    },
    {
      path: '/chemical-products',
      name: 'ChemicalProducts',
      meta: {
        title: '化工产品',
        icon: 'Sell'
      }
    }
  ]

  // 过滤有权限访问的路由
  return allRoutes.filter(route => {
    const hasRoutePermission = hasPermission(route.meta?.roles)
    if (route.children) {
      // 创建子路由的副本，不修改原始数组
      const filteredChildren = route.children.filter(child => hasPermission(child.meta?.roles))
      // 创建路由副本并设置过滤后的子路由
      const routeCopy = { ...route, children: filteredChildren }
      // 只有当父路由有权限或者有可访问的子路由时才显示
      if (hasRoutePermission || filteredChildren.length > 0) {
        Object.assign(route, routeCopy)
        return true
      }
      return false
    }
    return hasRoutePermission
  })
})

const activeMenu = computed(() => {
  const { meta, path } = route
  if (meta?.activeMenu) {
    return meta.activeMenu as string
  }
  return path
})

const showLogo = computed(() => settingsStore.showSidebarLogo)
const isCollapse = computed(() => !appStore.sidebar.opened)
</script>

<style lang="scss" scoped>
.has-logo {
  .el-scrollbar {
    height: calc(100% - 50px);
  }
}

.el-scrollbar {
  height: 100%;

  :deep(.scrollbar-wrapper) {
    overflow-x: hidden !important;
  }

  :deep(.el-scrollbar__bar.is-vertical > div) {
    background-color: var(--el-text-color-placeholder);
  }
}

.el-menu {
  border: none;
  height: 100%;
  width: 100% !important;
  border-right: 1px solid #2c3e50;

  // 菜单项悬停效果
  :deep(.el-menu-item) {
    color: v-bind('variables.menuText') !important;
    
    &:hover {
      background-color: v-bind('variables.menuHover') !important;
      color: v-bind('variables.menuActiveText') !important;
    }
    
    &.is-active {
      background-color: #409eff !important;
      color: v-bind('variables.menuActiveText') !important;
    }
  }

  // 子菜单标题悬停效果
  :deep(.el-sub-menu__title) {
    color: v-bind('variables.menuText') !important;
    
    &:hover {
      background-color: v-bind('variables.menuHover') !important;
      color: v-bind('variables.menuActiveText') !important;
    }
  }

  // 子菜单打开时的样式
  :deep(.el-sub-menu.is-opened > .el-sub-menu__title) {
    color: v-bind('variables.menuActiveText') !important;
  }
}
</style>