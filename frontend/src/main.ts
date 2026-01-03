import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router/index'

// Import Element Plus CSS theme
import 'element-plus/dist/index.css'

// Import global styles
import './styles/element-plus.scss'
import './styles/index.scss'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)
app.mount('#app')