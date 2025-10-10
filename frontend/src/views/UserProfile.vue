<template>
  <div class="user-profile-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span class="card-title">人员档案</span>
        </div>
      </template>
      <el-empty description="功能开发中，敬请期待...">
        <template #image>
          <el-icon :size="100" color="#909399">
            <UserFilled />
          </el-icon>
        </template>
      </el-empty>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { UserFilled } from '@element-plus/icons-vue'
</script>

<style scoped lang="scss">
.user-profile-container {
  padding: 20px;

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .card-title {
      font-size: 18px;
      font-weight: 600;
    }
  }

  .el-empty {
    padding: 100px 0;
  }
}
</style>
