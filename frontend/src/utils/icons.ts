// 图标映射 - 按需引入 Element Plus 图标
// 只导入项目中实际使用的图标,实现 tree-shaking

import {
  House,
  ChatDotRound,
  Avatar,
  ChatLineRound,
  Monitor,
  DataAnalysis,
  UserFilled,
  Share,
  Warning,
  DataBoard,
  User,
  Collection,
  Loading,
  Tools,
  Sell,
  Setting,
} from '@element-plus/icons-vue'

import type { Component } from 'vue'

// 图标名称到组件的映射
export const iconMap: Record<string, Component> = {
  House,
  ChatDotRound,
  Avatar,
  ChatLineRound,
  Monitor,
  DataAnalysis,
  UserFilled,
  Share,
  Warning,
  DataBoard,
  User,
  Collection,
  Loading,
  Tools,
  Sell,
  Setting,
}

// 根据图标名称获取图标组件
export function getIcon(iconName: string): Component | undefined {
  return iconMap[iconName]
}
