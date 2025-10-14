<template>
  <div class="relation-graph-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>关联图谱</span>
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
  height: 100vh;
  padding: 0;
  margin: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;

  > .el-card {
    width: 100%;
    flex: 1;
    margin: 0;
    display: flex;
    flex-direction: column;
    min-height: 0;

    :deep(.el-card__body) {
      padding: 20px;
      flex: 1;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      min-height: 0;
    }
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .el-empty {
    padding: 100px 0;
  }
}
</style>
