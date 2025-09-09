<template>
  <div>
    <h2>API测试页面</h2>
    <el-button @click="testLogin" type="primary">测试登录API</el-button>
    <div v-if="result">
      <h3>结果:</h3>
      <pre>{{ result }}</pre>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { authApi } from '@/api/auth'

const result = ref('')

const testLogin = async () => {
  try {
    console.log('开始测试登录...')
    const response = await authApi.login({
      username: 'admin',
      password: 'admin123'
    })
    console.log('登录成功:', response)
    result.value = JSON.stringify(response, null, 2)
  } catch (error) {
    console.error('登录失败:', error)
    result.value = '错误: ' + (error as Error).message
  }
}
</script>