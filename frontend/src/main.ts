import { createApp } from 'vue'
import App from './App.vue'

// 引入全局样式 - 优先加载
import '@/styles/index.scss'

// Element Plus 相关导入
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

// Vue 生态系统
import { createPinia } from 'pinia'
import router from './router'

// 创建应用实例
const app = createApp(App)

// 配置 Element Plus
app.use(ElementPlus, {
  locale: zhCn,
})

// 注册 Element Plus 图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 配置状态管理和路由
app.use(createPinia())
app.use(router)

// 挂载应用
app.mount('#app')