<template>
  <div class="dashboard-container">
    <el-container>
      <!-- 侧边栏 -->
      <el-aside width="250px" class="sidebar">
        <div class="logo">
          <h3>JD Web</h3>
        </div>
        
        <el-menu
          :default-active="$route.path"
          class="sidebar-menu"
          router
          background-color="#004080"
          text-color="#f0f0f0"
          active-text-color="#ffffff"
        >
          <el-menu-item index="/dashboard">
            <el-icon><House /></el-icon>
            <span>首页</span>
          </el-menu-item>
          
          <el-menu-item index="/tg-groups">
            <el-icon><ChatDotRound /></el-icon>
            <span>Tg群组管理</span>
          </el-menu-item>
          
          <!-- 管理员功能 -->
          <template v-if="userStore.isAdmin">
            <el-menu-item index="/user-manage">
              <el-icon><User /></el-icon>
              <span>用户管理</span>
            </el-menu-item>
            
            <el-menu-item index="/tag-manage">
              <el-icon><Collection /></el-icon>
              <span>标签管理</span>
            </el-menu-item>
            
            <el-menu-item index="/search-queue">
              <el-icon><Loading /></el-icon>
              <span>抓取进度</span>
            </el-menu-item>
            
            <el-menu-item index="/black-words">
              <el-icon><Warning /></el-icon>
              <span>黑词管理</span>
            </el-menu-item>
            
            <el-menu-item index="/search-result">
              <el-icon><DataAnalysis /></el-icon>
              <span>账户分析</span>
            </el-menu-item>
            
            <el-menu-item index="/chat-history">
              <el-icon><ChatLineRound /></el-icon>
              <span>Tg聊天内容</span>
            </el-menu-item>
            
            <el-menu-item index="/tg-users">
              <el-icon><Avatar /></el-icon>
              <span>Tg用户信息</span>
            </el-menu-item>
            
            <el-menu-item index="/tg-accounts">
              <el-icon><Monitor /></el-icon>
              <span>监听账户</span>
            </el-menu-item>
            
            <el-menu-item index="/chemical-products">
              <el-icon><Opportunity /></el-icon>
              <span>化工产品</span>
            </el-menu-item>
          </template>
        </el-menu>
        
        <!-- 退出登录 -->
        <div class="logout-section">
          <el-button type="danger" @click="handleLogout" style="width: 100%">
            <el-icon><SwitchButton /></el-icon>
            退出登录
          </el-button>
        </div>
      </el-aside>
      
      <!-- 主内容区 -->
      <el-container>
        <el-header class="header">
          <div class="header-content">
            <span class="welcome-text">欢迎, {{ userStore.userInfo?.username }}</span>
          </div>
        </el-header>
        
        <el-main class="main-content">
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import { useUserStore } from '@/store/user'
import { authApi } from '@/api/auth'

const router = useRouter()
const userStore = useUserStore()

// 初始化用户信息
userStore.initFromStorage()

const handleLogout = async () => {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    try {
      await authApi.logout()
    } catch (error) {
      // 即使API调用失败，也要清除本地状态
      console.warn('Logout API failed:', error)
    }
    
    userStore.logout()
    ElMessage.success('已退出登录')
    router.push('/login')
    
  } catch {
    // 用户取消操作
  }
}
</script>

<style scoped>
.dashboard-container {
  height: 100vh;
}

.sidebar {
  background-color: #004080;
  color: #f0f0f0;
}

.logo {
  padding: 20px;
  text-align: center;
  border-bottom: 1px solid #333;
}

.logo h3 {
  margin: 0;
  color: #f0f0f0;
}

.sidebar-menu {
  border: none;
}

.logout-section {
  position: absolute;
  bottom: 20px;
  left: 20px;
  right: 20px;
}

.header {
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  padding: 0 20px;
}

.header-content {
  width: 100%;
  display: flex;
  justify-content: flex-end;
  align-items: center;
}

.welcome-text {
  color: #606266;
  font-size: 14px;
}

.main-content {
  padding: 20px;
  background: #f5f5f5;
  overflow-y: auto;
}
</style>