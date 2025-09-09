<template>
  <div class="error-page">
    <div class="error-code">
      <div class="error-number">404</div>
    </div>
    <div class="error-desc">
      <h1>404</h1>
      <h2>抱歉，你访问的页面不存在</h2>
      <div class="error-handle">
        <el-button type="primary" size="large" @click="back">返回上一页</el-button>
        <el-button type="info" size="large" @click="toHome">回到首页</el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

const back = () => {
  router.go(-1)
}

const toHome = () => {
  router.push('/dashboard')
}
</script>

<style lang="scss" scoped>
.error-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #f0f2f5;
  
  .error-code {
    .error-number {
      font-size: 160px;
      font-weight: bold;
      color: #409eff;
      line-height: 1;
    }
  }

  .error-desc {
    margin-left: 40px;

    h1 {
      color: #1890ff;
      font-size: 72px;
      font-weight: bold;
      line-height: 72px;
      margin-bottom: 24px;
    }

    h2 {
      color: rgba(0, 0, 0, 0.45);
      font-size: 20px;
      font-weight: normal;
      line-height: 28px;
      margin-bottom: 32px;
    }

    .error-handle {
      .el-button {
        margin-right: 12px;
      }
    }
  }
}

@media screen and (max-width: 768px) {
  .error-page {
    flex-direction: column;
    
    .error-code {
      .error-number {
        font-size: 100px;
      }
    }

    .error-desc {
      margin-left: 0;
      margin-top: 30px;
      text-align: center;
    }
  }
}
</style>