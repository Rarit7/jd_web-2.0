<template>
  <div class="relation-graph-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span class="card-title">关联图谱</span>
        </div>
      </template>
      <el-empty description="功能开发中，敬请期待...">
        <template #image>
          <el-icon :size="100" color="#909399">
            <Share />
          </el-icon>
        </template>
      </el-empty>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { Share } from '@element-plus/icons-vue'
</script>

<style scoped lang="scss">
.relation-graph-container {
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
