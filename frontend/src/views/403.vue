<template>
  <div class="error-page">
    <div class="error-container">
      <div class="error-icon">
        <el-icon size="120" color="#f56c6c">
          <Lock />
        </el-icon>
      </div>
      
      <div class="error-content">
        <h1 class="error-title">403</h1>
        <h2 class="error-subtitle">权限不足</h2>
        <p class="error-description">
          抱歉，您没有权限访问此页面。请联系管理员获取相应权限。
        </p>
        
        <div class="error-info">
          <p><strong>当前用户：</strong>{{ userInfo?.username || '未知用户' }}</p>
          <p><strong>权限等级：</strong>{{ getPermissionName(userInfo?.permission_level) }}</p>
        </div>
        
        <div class="error-actions">
          <el-button type="primary" @click="goHome">
            <el-icon><House /></el-icon>
            返回首页
          </el-button>
          <el-button @click="goBack">
            <el-icon><Back /></el-icon>
            返回上页
          </el-button>
          <el-button @click="logout">
            <el-icon><SwitchButton /></el-icon>
            切换账户
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store/modules/user'
import { Lock, House, Back, SwitchButton } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()

// 获取用户信息
const userInfo = computed(() => userStore.userInfo)

// 获取权限名称
const getPermissionName = (level: number | undefined) => {
  switch (level) {
    case 1:
      return '超级管理员'
    case 2:
      return '普通用户'
    default:
      return '未知权限'
  }
}

// 返回首页
const goHome = () => {
  router.push('/dashboard')
}

// 返回上一页
const goBack = () => {
  router.go(-1)
}

// 退出登录
const logout = async () => {
  try {
    await userStore.logout()
    ElMessage.success('已退出登录')
    router.push('/login')
  } catch (error) {
    ElMessage.error('退出登录失败')
  }
}
</script>

<style scoped lang="scss">
.error-page {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
  box-sizing: border-box;
}

.error-container {
  background: white;
  border-radius: 20px;
  padding: 60px 40px;
  text-align: center;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  max-width: 600px;
  width: 100%;
}

.error-icon {
  margin-bottom: 30px;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
  100% {
    transform: scale(1);
  }
}

.error-title {
  font-size: 72px;
  font-weight: 700;
  color: #f56c6c;
  margin: 0 0 10px 0;
  line-height: 1;
}

.error-subtitle {
  font-size: 36px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 20px 0;
}

.error-description {
  font-size: 16px;
  color: #606266;
  line-height: 1.6;
  margin-bottom: 30px;
}

.error-info {
  background: #f5f7fa;
  border-radius: 10px;
  padding: 20px;
  margin-bottom: 30px;
  text-align: left;
  
  p {
    margin: 8px 0;
    font-size: 14px;
    color: #606266;
    
    strong {
      color: #303133;
      font-weight: 600;
    }
  }
}

.error-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  flex-wrap: wrap;
  
  .el-button {
    padding: 12px 24px;
    border-radius: 8px;
    font-weight: 500;
    
    .el-icon {
      margin-right: 6px;
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .error-container {
    padding: 40px 20px;
  }
  
  .error-title {
    font-size: 48px;
  }
  
  .error-subtitle {
    font-size: 24px;
  }
  
  .error-actions {
    flex-direction: column;
    align-items: center;
    
    .el-button {
      width: 200px;
    }
  }
}

@media (max-width: 480px) {
  .error-page {
    padding: 10px;
  }
  
  .error-container {
    padding: 30px 15px;
  }
  
  .error-title {
    font-size: 36px;
  }
  
  .error-subtitle {
    font-size: 20px;
  }
  
  .error-description {
    font-size: 14px;
  }
}
</style>