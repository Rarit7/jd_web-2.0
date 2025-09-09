/**
 * 登录用户类型枚举
 */
export const enum LoginUserTypeEnum {
  /** 系统内置 */
  USERNAME_PASSWORD = 'username_password'
}

/**
 * 设备类型
 */
export const enum DeviceEnum {
  /** 移动端 */
  MOBILE = 'mobile',
  /** 桌面端 */
  DESKTOP = 'desktop'
}

/**
 * 组件尺寸
 */
export const enum ComponentSizeEnum {
  LARGE = 'large',
  DEFAULT = 'default', 
  SMALL = 'small'
}

/**
 * 布局模式
 */
export const enum LayoutModeEnum {
  /** 左侧菜单 */
  LEFT = 'left',
  /** 顶部菜单 */
  TOP = 'top',
  /** 混合菜单 */
  MIX = 'mix'
}

/**
 * 主题模式
 */
export const enum ThemeModeEnum {
  /** 浅色 */
  LIGHT = 'light',
  /** 深色 */
  DARK = 'dark',
  /** 跟随系统 */
  AUTO = 'auto'
}

/**
 * 路由缓存模式
 */
export const enum CacheModeEnum {
  /** 开启缓存 */
  ENABLE = 'enable',
  /** 关闭缓存 */
  DISABLE = 'disable'
}