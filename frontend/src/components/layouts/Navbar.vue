<template>
  <div class="navbar">
    <hamburger
      id="hamburger-container"
      :is-active="sidebar.opened"
      class="hamburger-container"
      @toggle-click="toggleSideBar"
    />

    <breadcrumb id="breadcrumb-container" class="breadcrumb-container" />

    <div class="right-menu">
      <template v-if="device !== 'mobile'">
        <!-- 全屏 -->
        <screenfull id="screenfull" class="right-menu-item hover-effect" />
      </template>

      <!-- 用户下拉菜单 -->
      <el-dropdown class="avatar-container right-menu-item hover-effect" trigger="click">
        <div class="avatar-wrapper">
          <img :src="avatar" class="user-avatar" />
          <span class="user-name">{{ nickname }}</span>
          <el-icon class="el-icon-caret-bottom">
            <caret-bottom />
          </el-icon>
        </div>
        <template #dropdown>
          <el-dropdown-menu>
            <router-link to="/profile">
              <el-dropdown-item>
                <el-icon><User /></el-icon>
                修改密码
              </el-dropdown-item>
            </router-link>
            <el-dropdown-item divided @click="logout">
              <el-icon><SwitchButton /></el-icon>
              退出登录
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { CaretBottom, User, SwitchButton } from '@element-plus/icons-vue'
import Hamburger from '@/components/common/Hamburger.vue'
import Breadcrumb from '@/components/common/Breadcrumb.vue'
import Screenfull from '@/components/common/Screenfull.vue'
import { useAppStore } from '@/store/modules/app'
import { useUserStore } from '@/store/modules/user'
import { authApi } from '@/api/auth'

const router = useRouter()
const appStore = useAppStore()
const userStore = useUserStore()

// 计算属性
const sidebar = computed(() => appStore.sidebar)
const device = computed(() => appStore.device)
const avatar = computed(() => userStore.avatar || 'https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png')
const nickname = computed(() => userStore.userInfo?.username || 'Admin')

// 切换侧边栏
const toggleSideBar = () => {
  appStore.toggleSidebar()
}

// 退出登录
const logout = async () => {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    try {
      await authApi.logout()
    } catch (error) {
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

<style lang="scss" scoped>
.navbar {
  height: var(--layout-header-height);
  overflow: hidden;
  position: relative;
  background: var(--el-bg-color);
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  display: flex;
  align-items: center;
  padding: 0 20px;

  .hamburger-container {
    line-height: var(--layout-header-height);
    height: 100%;
    cursor: pointer;
    transition: background 0.3s;

    &:hover {
      background: rgba(0, 0, 0, 0.025);
    }
  }

  .breadcrumb-container {
    flex: 1;
    margin-left: 20px;
  }

  .right-menu {
    float: right;
    height: 100%;
    line-height: var(--layout-header-height);
    display: flex;
    align-items: center;

    &:focus {
      outline: none;
    }

    .right-menu-item {
      display: inline-block;
      padding: 0 8px;
      height: 100%;
      font-size: 18px;
      color: var(--el-text-color-regular);
      vertical-align: text-bottom;
      cursor: pointer;
      
      &.hover-effect {
        transition: background 0.3s;

        &:hover {
          background: rgba(0, 0, 0, 0.025);
        }
      }
    }

    .avatar-container {
      margin-right: 30px;

      .avatar-wrapper {
        margin-top: 5px;
        position: relative;
        display: flex;
        align-items: center;
        cursor: pointer;

        .user-avatar {
          width: 32px;
          height: 32px;
          border-radius: 50%;
        }

        .user-name {
          margin-left: 8px;
          font-size: 14px;
          font-weight: 500;
          color: var(--el-text-color-primary);
        }

        .el-icon-caret-bottom {
          margin-left: 5px;
          font-size: 12px;
        }
      }
    }
  }
}

</style>