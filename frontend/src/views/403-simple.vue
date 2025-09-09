<template>
  <div style="text-align: center; padding: 50px;">
    <h1 style="color: red; font-size: 72px;">403</h1>
    <h2>权限不足</h2>
    <p>您没有权限访问此页面</p>
    <button @click="$router.push('/dashboard')">返回首页</button>
  </div>
</template>

<script setup lang="ts">
// 简单的403页面用于测试
</script>