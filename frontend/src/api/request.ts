import axios from 'axios'
import { ElMessage } from 'element-plus'

// 创建axios实例
const request = axios.create({
  baseURL: '/api',
  timeout: 10000,
  withCredentials: true // 确保发送cookies以维持session
})

// 请求拦截器
request.interceptors.request.use(
  (config) => {
    // 由于使用session认证，不需要在header中添加token
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  (response) => {
    // 直接返回完整的response，让各个API处理具体的数据格式
    return response
  },
  (error) => {
    // 处理HTTP错误
    if (error.response) {
      const status = error.response.status
      switch (status) {
        case 401:
          ElMessage.error('未授权，请重新登录')
          // 动态导入store以避免循环依赖
          import('@/store/user').then(({ useUserStore }) => {
            const userStore = useUserStore()
            userStore.logout()
          })
          window.location.href = '/login'
          break
        case 403:
          ElMessage.error('没有权限访问')
          break
        case 404:
          ElMessage.error('请求的资源不存在')
          break
        case 500:
          ElMessage.error('服务器内部错误')
          break
        default:
          ElMessage.error('网络错误，请稍后重试')
      }
    } else {
      ElMessage.error('网络连接失败')
    }
    
    return Promise.reject(error)
  }
)

export default request