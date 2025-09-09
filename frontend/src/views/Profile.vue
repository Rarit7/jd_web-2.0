<template>
  <div class="login-container">
    <el-form
      ref="profileFormRef"
      :model="profileForm"
      :rules="profileRules"
      class="login-form"
      autocomplete="off"
      label-position="left"
    >
      <div class="title-container">
        <h3 class="title">修改密码</h3>
      </div>

      <el-form-item prop="username">
        <span class="svg-container">
          <el-icon class="svg-container-icon"><User /></el-icon>
        </span>
        <el-input
          ref="usernameInput"
          v-model="profileForm.username"
          placeholder="用户名"
          name="username"
          type="text"
          tabindex="1"
          autocomplete="off"
        />
      </el-form-item>

      <el-form-item prop="newPassword">
        <span class="svg-container">
          <el-icon class="svg-container-icon"><Lock /></el-icon>
        </span>
        <el-input
          :key="passwordType"
          ref="passwordInput"
          v-model="profileForm.newPassword"
          :type="passwordType"
          placeholder="新密码"
          name="newPassword"
          tabindex="2"
          autocomplete="new-password"
        />
        <span class="show-pwd" @click="showPwd">
          <el-icon class="show-pwd-icon">
            <View v-if="passwordType === 'password'" />
            <Hide v-else />
          </el-icon>
        </span>
      </el-form-item>

      <el-form-item prop="confirmPassword">
        <span class="svg-container">
          <el-icon class="svg-container-icon"><Lock /></el-icon>
        </span>
        <el-input
          :key="confirmPasswordType"
          ref="confirmPasswordInput"
          v-model="profileForm.confirmPassword"
          :type="confirmPasswordType"
          placeholder="确认新密码"
          name="confirmPassword"
          tabindex="3"
          autocomplete="new-password"
          @keyup.enter="handleUpdate"
        />
        <span class="show-pwd" @click="showConfirmPwd">
          <el-icon class="show-pwd-icon">
            <View v-if="confirmPasswordType === 'password'" />
            <Hide v-else />
          </el-icon>
        </span>
      </el-form-item>

      <div class="button-group">
        <el-button
          :loading="loading"
          type="primary"
          class="update-button"
          @click.prevent="handleUpdate"
        >
          更新
        </el-button>
        
        <el-button
          class="back-button"
          @click="goBack"
        >
          返回
        </el-button>
      </div>

    </el-form>

  </div>
</template>

<script setup lang="ts">
import { ref, reactive, nextTick, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { User, Lock, View, Hide } from '@element-plus/icons-vue'
import { useUserStore } from '@/store/modules/user'
import request from '@/api/request'

const router = useRouter()
const userStore = useUserStore()

const profileFormRef = ref<FormInstance>()
const usernameInput = ref<HTMLInputElement>()
const passwordInput = ref<HTMLInputElement>()
const confirmPasswordInput = ref<HTMLInputElement>()
const loading = ref(false)
const passwordType = ref('password')
const confirmPasswordType = ref('password')

const profileForm = reactive({
  username: '',
  newPassword: '',
  confirmPassword: ''
})

const validateUsername = async (rule: any, value: any, callback: any) => {
  if (!value) {
    callback(new Error('请输入用户名'))
    return
  }
  if (value.length < 3) {
    callback(new Error('用户名不能少于3位'))
    return
  }
  
  // Check if username exists (except current user)
  try {
    const response = await request.get(`/user/check-username?username=${encodeURIComponent(value)}`)
    
    if (response.data && response.data.err_code === 0 && response.data.payload.exists && response.data.payload.is_different_user) {
      callback(new Error('用户名已被占用'))
    } else {
      callback()
    }
  } catch (error) {
    console.warn('Username check failed:', error)
    callback() // Continue if check fails
  }
}

const validatePassword = (rule: any, value: any, callback: any) => {
  if (!value) {
    callback(new Error('请输入新密码'))
  } else if (value.length < 6) {
    callback(new Error('密码不能少于6位'))
  } else {
    callback()
  }
}

const validateConfirmPassword = (rule: any, value: any, callback: any) => {
  if (!value) {
    callback(new Error('请确认新密码'))
  } else if (value !== profileForm.newPassword) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const profileRules: FormRules = {
  username: [
    { required: true, trigger: 'blur', validator: validateUsername }
  ],
  newPassword: [
    { required: true, trigger: 'blur', validator: validatePassword }
  ],
  confirmPassword: [
    { required: true, trigger: 'blur', validator: validateConfirmPassword }
  ]
}

const showPwd = () => {
  passwordType.value = passwordType.value === 'password' ? '' : 'password'
  nextTick(() => {
    passwordInput.value?.focus()
  })
}

const showConfirmPwd = () => {
  confirmPasswordType.value = confirmPasswordType.value === 'password' ? '' : 'password'
  nextTick(() => {
    confirmPasswordInput.value?.focus()
  })
}

const handleUpdate = async () => {
  if (!profileFormRef.value) return
  
  try {
    await profileFormRef.value.validate()
    loading.value = true
    
    const response = await request.post('/user/update-profile', {
      username: profileForm.username,
      password: profileForm.newPassword
    })
    
    if (response.data && response.data.err_code === 0) {
      // Update user store if username changed
      if (userStore.userInfo && userStore.userInfo.username !== profileForm.username) {
        userStore.userInfo.username = profileForm.username
      }
      
      ElMessage.success('用户信息更新成功')
      
      // Clear form
      profileForm.newPassword = ''
      profileForm.confirmPassword = ''
      
      // Redirect to dashboard after a delay
      setTimeout(() => {
        router.push('/dashboard')
      }, 1000)
    } else {
      ElMessage.error(response.data.err_msg || '更新失败')
    }
    
  } catch (error) {
    console.error('Update failed:', error)
    ElMessage.error('更新失败，请稍后再试')
  } finally {
    loading.value = false
  }
}

const goBack = () => {
  router.back()
}

// Initialize form with current user data
onMounted(() => {
  if (userStore.userInfo && userStore.userInfo.username) {
    profileForm.username = userStore.userInfo.username
  }
})
</script>

<style lang="scss" scoped>
.login-container {
  min-height: 100vh;
  width: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  justify-content: center;
  align-items: center;
  overflow: hidden;
  position: relative;

  // 添加背景动画效果
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: url("data:image/svg+xml,%3csvg width='100' height='100' xmlns='http://www.w3.org/2000/svg'%3e%3cpath d='M11 18c0 1.657-.343 3.165-.864 4.5h44.728c-.521-1.335-.864-2.843-.864-4.5 0-7.18 5.82-13 13-13s13 5.82 13 13c0 1.657-.343 3.165-.864 4.5h.728c1.657 0 3.165-.343 4.5-.864V74.136c-1.335-.521-2.843-.864-4.5-.864-7.18 0-13 5.82-13 13s5.82 13 13 13c1.657 0 3.165-.343 4.5-.864v44.728c-1.335-.521-2.843-.864-4.5-.864-7.18 0-13 5.82-13 13s5.82 13 13 13c1.657 0 3.165-.343 4.5-.864V.864c-1.335-.521-2.843-.864-4.5-.864-7.18 0-13 5.82-13 13z' fill='%23ffffff' fill-opacity='0.05' fill-rule='evenodd'/%3e%3c/svg%3e") repeat;
    opacity: 0.1;
    animation: move 20s linear infinite;
  }

  @keyframes move {
    0% { background-position: 0 0; }
    100% { background-position: 100px 100px; }
  }

  .login-form {
    position: relative;
    width: 450px;
    max-width: 90%;
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    border-radius: 16px;
    padding: 40px 35px;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    z-index: 10;
  }

  .title-container {
    text-align: center;
    margin-bottom: 40px;

    .title {
      font-size: 32px;
      font-weight: 700;
      background: linear-gradient(135deg, #498cff, #667eea);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      margin: 0;
      letter-spacing: -0.5px;
    }
  }

  .el-form-item {
    margin-bottom: 24px;
    border-radius: 12px;
    
    :deep(.el-form-item__error) {
      color: #f56565;
    }
  }

  .svg-container {
    position: absolute;
    left: 16px;
    top: 50%;
    transform: translateY(-50%);
    color: #498cff;
    z-index: 10;
    
    .svg-container-icon {
      font-size: 18px;
    }
  }

  .el-input {
    :deep(.el-input__wrapper) {
      background: rgba(255, 255, 255, 0.8);
      border: 2px solid rgba(116, 75, 162, 0.1);
      border-radius: 12px;
      height: 50px;
      padding: 0 50px 0 50px;
      box-shadow: none;
      transition: all 0.3s ease;

      &:hover {
        border-color: rgba(73, 140, 255, 0.3);
        background: rgba(255, 255, 255, 0.9);
      }

      &.is-focus {
        border-color: #498cff !important;
        background: rgba(255, 255, 255, 1) !important;
        box-shadow: 0 0 0 3px rgba(73, 140, 255, 0.1) !important;
      }
    }

    :deep(.el-input__inner) {
      color: #2d3748;
      font-size: 14px;
      font-weight: 500;
      
      &::placeholder {
        color: #a0aec0;
        font-weight: 400;
      }

      &:-webkit-autofill {
        -webkit-box-shadow: 0 0 0 1000px rgba(255, 255, 255, 0.9) inset !important;
        -webkit-text-fill-color: #2d3748 !important;
      }
    }
  }

  .show-pwd {
    position: absolute;
    right: 16px;
    top: 50%;
    transform: translateY(-50%);
    color: #a0aec0;
    cursor: pointer;
    user-select: none;
    z-index: 10;
    transition: color 0.3s ease;

    &:hover {
      color: #498cff;
    }

    .show-pwd-icon {
      font-size: 16px;
    }
  }

  .button-group {
    display: flex;
    gap: 16px;
    margin-top: 32px;

    .update-button, .back-button {
      flex: 1;
      height: 50px;
      border-radius: 12px;
      font-size: 16px;
      font-weight: 600;
      transition: all 0.3s ease;
    }

    .update-button {
      background: linear-gradient(135deg, #498cff, #667eea);
      border: none;
      box-shadow: 0 8px 25px rgba(73, 140, 255, 0.3);
      color: white;

      &:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 35px rgba(73, 140, 255, 0.4);
      }

      &:active {
        transform: translateY(0);
      }
    }

    .back-button {
      background: rgba(116, 75, 162, 0.1);
      border: 2px solid rgba(116, 75, 162, 0.2);
      color: #667eea;

      &:hover {
        background: rgba(116, 75, 162, 0.15);
        border-color: rgba(116, 75, 162, 0.3);
        transform: translateY(-2px);
      }

      &:active {
        transform: translateY(0);
      }
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .login-container {
    padding: 20px;
    
    .login-form {
      padding: 30px 25px;
    }
    
    .title-container .title {
      font-size: 28px;
    }

    .button-group {
      flex-direction: column;
      gap: 12px;
    }
  }
}
</style>