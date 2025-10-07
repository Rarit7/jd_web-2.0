import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/store/modules/user'
import AppLayout from '@/components/layouts/AppLayout.vue'

const router = createRouter({
  history: createWebHistory(),
  scrollBehavior(to, _from, savedPosition) {
    // 如果有保存的滚动位置，恢复到该位置
    if (savedPosition) {
      return savedPosition
    }
    // 如果路由有锚点，滚动到锚点
    if (to.hash) {
      return {
        el: to.hash,
        behavior: 'smooth'
      }
    }
    // 默认滚动到顶部
    return { top: 0 }
  },
  routes: [
    {
      path: '/login',
      component: () => import('@/views/Login.vue'),
      meta: { 
        hidden: true,
        title: '登录',
        noTagsView: true
      }
    },
    {
      path: '/profile',
      component: () => import('@/views/Profile.vue'),
      meta: { 
        hidden: true,
        title: '修改密码',
        noTagsView: true
      }
    },
    {
      path: '/404',
      component: () => import('@/views/404.vue'),
      meta: { 
        hidden: true,
        title: '404',
        noTagsView: true
      }
    },
    {
      path: '/403',
      component: () => import('@/views/403-simple.vue'),
      meta: { 
        hidden: true,
        title: '权限不足',
        noTagsView: true
      }
    },
    {
      path: '/',
      component: AppLayout,
      redirect: '/dashboard',
      children: [
        {
          path: 'dashboard',
          name: 'Dashboard',
          component: () => import('@/views/dashboard/index.vue'),
          meta: { 
            title: '首页',
            icon: 'House',
            affix: true
          }
        }
      ]
    },
    // Telegram监控
    {
      path: '/tg-groups',
      component: AppLayout,
      children: [
        {
          path: '',
          name: 'TgGroups',
          component: () => import('@/views/TgGroups.vue'),
          meta: { 
            title: '群组管理',
            icon: 'ChatDotRound'
          }
        }
      ]
    },
    {
      path: '/tg-users',
      component: AppLayout,
      children: [
        {
          path: '',
          name: 'TgUsers',
          component: () => import('@/views/TgUsers.vue'),
          meta: { 
            title: '用户信息',
            icon: 'Avatar'
          }
        }
      ]
    },
    {
      path: '/chat-history',
      component: AppLayout,
      children: [
        {
          path: '',
          name: 'ChatHistory',
          component: () => import('@/views/ChatHistory.vue'),
          meta: { 
            title: '聊天内容',
            icon: 'ChatLineRound'
          }
        }
      ]
    },
    {
      path: '/tg-accounts',
      component: AppLayout,
      children: [
        {
          path: '',
          name: 'TgAccounts',
          component: () => import('@/views/TgAccounts.vue'),
          meta: { 
            title: '监听账户',
            icon: 'Monitor'
          }
        }
      ]
    },
    {
      path: '/change_record',
      component: AppLayout,
      children: [
        {
          path: '',
          name: 'ChangeRecord',
          component: () => import('@/views/ChangeRecord.vue'),
          meta: {
            title: '变动分析',
            icon: 'DataAnalysis'
          }
        }
      ]
    },
    // 广告追踪
    {
      path: '/ad-tracking',
      component: AppLayout,
      children: [
        {
          path: '',
          name: 'AdTracking',
          component: () => import('@/views/ad-tracking/index.vue'),
          meta: {
            title: '广告追踪',
            icon: 'Warning'
          }
        }
      ]
    },
    // 数据大屏
    {
      path: '/dashboard-screen',
      component: AppLayout,
      children: [
        {
          path: '',
          name: 'DashboardScreen',
          component: () => import('@/views/DashboardScreen.vue'),
          meta: { 
            title: '数据大屏',
            icon: 'DataBoard'
          }
        }
      ]
    },
    // 后台管理
    {
      path: '/user-manage',
      component: AppLayout,
      children: [
        {
          path: '',
          name: 'UserManage',
          component: () => import('@/views/UserManage.vue'),
          meta: { 
            title: '用户管理',
            icon: 'User',
            roles: [1]
          }
        }
      ]
    },
    {
      path: '/tag-manage',
      component: AppLayout,
      children: [
        {
          path: '',
          name: 'TagManage',
          component: () => import('@/views/TagManage.vue'),
          meta: {
            title: '标签管理',
            icon: 'Collection',
            roles: [1]
          }
        }
      ]
    },
    {
      path: '/search-queue',
      component: AppLayout,
      children: [
        {
          path: '',
          name: 'SearchQueue',
          component: () => import('@/views/SearchQueue.vue'),
          meta: { 
            title: '抓取进度',
            icon: 'Loading',
            roles: [1]
          }
        }
      ]
    },
    {
      path: '/black-words',
      component: AppLayout,
      children: [
        {
          path: '',
          name: 'BlackWords',
          component: () => import('@/views/BlackWords.vue'),
          meta: { 
            title: '黑词管理',
            icon: 'Warning',
            roles: [1]
          }
        }
      ]
    },
    {
      path: '/website-settings',
      component: AppLayout,
      children: [
        {
          path: '',
          name: 'WebsiteSettings',
          component: () => import('@/views/WebsiteSettings.vue'),
          meta: { 
            title: '网站设置',
            icon: 'Tools',
            roles: [1]
          }
        }
      ]
    },
    // 化工产品
    {
      path: '/chemical-products',
      component: AppLayout,
      children: [
        {
          path: '',
          name: 'ChemicalProducts',
          component: () => import('@/views/ChemicalProducts.vue'),
          meta: { 
            title: '化工产品',
            icon: 'Sell'
          }
        }
      ]
    },
    {
      path: '/api-test',
      component: AppLayout,
      meta: { hidden: true },
      children: [
        {
          path: '',
          name: 'ApiTest',
          component: () => import('@/views/ApiTest.vue'),
          meta: { 
            title: 'API测试',
            icon: 'Setting'
          }
        }
      ]
    },
    // 404页面必须放在最后  
    { path: '/:pathMatch(.*)*', name: 'NotFound', redirect: '/404', meta: { hidden: true } }
  ]
})

// 路由守卫
router.beforeEach(async (to, _from, next) => {
  console.log('🔍 Router guard triggered for:', to.path)
  const userStore = useUserStore()
  
  // 确保body滚动行为正常（防止某些页面设置了overflow: hidden）
  document.body.style.overflow = 'auto'
  
  // 白名单路由，无需登录验证
  const whiteList = ['/login', '/404', '/403', '/401']
  if (whiteList.includes(to.path)) {
    next()
    return
  }
  
  // 如果没有用户信息，尝试从localStorage恢复
  if (!userStore.userInfo) {
    userStore.initFromStorage()
    
    // 如果localStorage中也没有用户信息，尝试通过API获取
    if (!userStore.userInfo) {
      try {
        const { authApi } = await import('@/api/auth')
        const response = await authApi.getUserInfo()
        if (response.data.err_code === 0) {
          userStore.setUser(response.data.payload)
        } else {
          next('/login')
          return
        }
      } catch (error) {
        // API调用失败，跳转到登录页
        next('/login')
        return
      }
    }
  }
  
  // 检查角色权限
  if (to.meta?.roles && Array.isArray(to.meta.roles)) {
    const hasRole = to.meta.roles.some((role: number) => userStore.roleIds.includes(role))
    console.log('Permission check:', {
      path: to.path,
      requiredRoles: to.meta.roles,
      userRoles: userStore.roleIds,
      hasRole: hasRole
    })
    if (!hasRole) {
      console.log('Access denied, redirecting to /403')
      next('/403')
      return
    }
  }
  
  // 已登录用户访问登录页，重定向到首页
  if (to.path === '/login') {
    next('/dashboard')
    return
  }
  
  next()
})

export default router