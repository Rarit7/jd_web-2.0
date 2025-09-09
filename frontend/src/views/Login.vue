<template>
  <div class="login-container">
    <el-form
      ref="loginFormRef"
      :model="loginForm"
      :rules="loginRules"
      class="login-form"
      autocomplete="on"
      label-position="left"
    >
      <div class="title-container">
        <h3 class="title">SDJD_TG管理系统</h3>
      </div>

      <el-form-item prop="username">
        <span class="svg-container">
          <el-icon class="svg-container-icon"><User /></el-icon>
        </span>
        <el-input
          ref="username"
          v-model="loginForm.username"
          placeholder="用户名"
          name="username"
          type="text"
          tabindex="1"
          autocomplete="on"
        />
      </el-form-item>

      <el-tooltip content="大写锁定已开启" placement="right" :disabled="!capsTooltip">
        <el-form-item prop="password">
          <span class="svg-container">
            <el-icon class="svg-container-icon"><Lock /></el-icon>
          </span>
          <el-input
            :key="passwordType"
            ref="password"
            v-model="loginForm.password"
            :type="passwordType"
            placeholder="密码"
            name="password"
            tabindex="2"
            autocomplete="on"
            @blur="capsTooltip = false"
            @keyup="checkCapslock"
            @keyup.enter="handleLogin"
          />
          <span class="show-pwd" @click="showPwd">
            <el-icon class="show-pwd-icon">
              <View v-if="passwordType === 'password'" />
              <Hide v-else />
            </el-icon>
          </span>
        </el-form-item>
      </el-tooltip>

      <el-button
        :loading="loading"
        type="primary"
        style="width:100%;margin-bottom:30px;"
        @click.prevent="handleLogin"
      >
        登录
      </el-button>

    </el-form>

  </div>
</template>

<script setup lang="ts">
import { ref, reactive, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { User, Lock, View, Hide } from '@element-plus/icons-vue'
import { authApi } from '@/api/auth'
import { useUserStore } from '@/store/modules/user'

const router = useRouter()
const userStore = useUserStore()

const loginFormRef = ref<FormInstance>()
const username = ref<HTMLInputElement>()
const password = ref<HTMLInputElement>()
const loading = ref(false)
const passwordType = ref('password')
const capsTooltip = ref(false)

const loginForm = reactive({
  username: '',
  password: ''
})

const loginRules: FormRules = {
  username: [
    { required: true, trigger: 'blur', message: '请输入正确的用户名' }
  ],
  password: [
    { required: true, trigger: 'blur', validator: validatePassword }
  ]
}

function validatePassword(rule: any, value: any, callback: any) {
  if (value.length < 6) {
    callback(new Error('密码不能少于6位'))
  } else {
    callback()
  }
}

const showPwd = () => {
  if (passwordType.value === 'password') {
    passwordType.value = ''
  } else {
    passwordType.value = 'password'
  }
  nextTick(() => {
    password.value?.focus()
  })
}

const checkCapslock = (e: KeyboardEvent) => {
  const { key } = e
  capsTooltip.value = key && key.length === 1 && (key >= 'A' && key <= 'Z')
}

const handleLogin = async () => {
  if (!loginFormRef.value) return
  
  try {
    await loginFormRef.value.validate()
    loading.value = true
    
    const response = await authApi.login(loginForm)
    
    // 检查响应格式并处理
    if (response.data && response.data.err_code === 0) {
      // 保存用户信息 (使用session认证，不需要token)
      userStore.setUser(response.data.payload.user)
      
      ElMessage.success('登录成功')
      
      // 跳转到仪表板
      router.push('/dashboard')
    } else {
      ElMessage.error(response.data?.err_msg || '登录失败')
    }
    
  } catch (error) {
    console.error('Login failed:', error)
    ElMessage.error('登录失败，请检查用户名和密码')
  } finally {
    loading.value = false
  }
}
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

  .el-button {
    width: 100%;
    height: 50px;
    border-radius: 12px;
    font-size: 16px;
    font-weight: 600;
    background: linear-gradient(135deg, #498cff, #667eea);
    border: none;
    box-shadow: 0 8px 25px rgba(73, 140, 255, 0.3);
    transition: all 0.3s ease;

    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 12px 35px rgba(73, 140, 255, 0.4);
    }

    &:active {
      transform: translateY(0);
    }

    :deep(.el-button__text-wrapper) {
      color: white;
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
  }
}
</style>