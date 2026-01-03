/**
 * 本地存储键名常量
 */
export const STORAGE_KEYS = {
  /** 用户令牌 */
  TOKEN: 'accessToken',
  /** 用户信息 */
  USER_INFO: 'userInfo',
  /** 语言设置 */
  LANGUAGE: 'language',
  /** 布局设置 */
  LAYOUT: 'layout',
  /** 侧边栏状态 */
  SIDEBAR_STATUS: 'sidebarStatus',
  /** 标签页设置 */
  VISITED_VIEWS: 'visitedViews',
  /** 缓存页面 */
  CACHED_VIEWS: 'cachedViews'
}

/**
 * 默认设置
 */
export const DEFAULT_SETTINGS = {
  /** 系统标题 */
  title: '云端猎毒',
  /** 系统版本 */
  version: '1.0.0',
  /** 系统描述 */
  description: '基于Vue3+Element Plus的企业级后台管理系统',
  /** 固定头部 */
  fixedHeader: true,
  /** 显示标签栏 */
  showTagsView: true,
  /** 显示侧边栏Logo */
  showSidebarLogo: true,
  /** 显示设置按钮 */
  showSettings: true,
  /** 显示面包屑导航 */
  showBreadcrumb: true,
  /** 显示面包屑导航图标 */
  showBreadcrumbIcon: false,
  /** 侧边栏展开宽度 */
  sidebarWidth: '220px',
  /** 侧边栏折叠宽度 */
  sidebarCollapsedWidth: '64px'
}

/**
 * 路由白名单
 */
export const ROUTE_WHITE_LIST = ['/login', '/404', '/403', '/401']

/**
 * 系统角色
 */
export const ROLES = {
  /** 超级管理员 */
  SUPER_ADMIN: 1,
  /** 普通用户 */
  USER: 2
}

/**
 * HTTP状态码
 */
export const HTTP_STATUS = {
  SUCCESS: 200,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  INTERNAL_SERVER_ERROR: 500
}

/**
 * 接口响应码
 */
export const API_CODE = {
  SUCCESS: 0,
  ERROR: 1
}