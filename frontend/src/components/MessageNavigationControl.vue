<template>
  <div v-if="visible" class="message-navigation-control">
    <el-button-group>
      <el-button
        :disabled="currentPosition <= 1"
        @click="$emit('prev')"
        :loading="loading"
      >
        <el-icon><ArrowLeft /></el-icon>
        上一条
      </el-button>

      <el-button disabled>
        第 {{ currentPosition }}/{{ totalCount }} 条
      </el-button>

      <el-input
        v-model.number="inputPosition"
        type="number"
        :min="1"
        :max="totalCount"
        size="small"
        placeholder="输入位置"
        style="width: 80px"
        @keyup.enter="handleGoto"
      />

      <el-button @click="handleGoto" size="small">
        跳转
      </el-button>

      <el-button
        :disabled="currentPosition >= totalCount"
        @click="$emit('next')"
        :loading="loading"
      >
        下一条
        <el-icon><ArrowRight /></el-icon>
      </el-button>
    </el-button-group>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { ArrowLeft, ArrowRight } from '@element-plus/icons-vue'

interface Props {
  currentPosition: number      // 当前消息位置
  totalCount: number          // 总消息数
  loading?: boolean            // 是否加载中
  visible?: boolean            // 是否显示控件
}

interface Emits {
  (event: 'prev'): void                  // 点击上一条
  (event: 'next'): void                  // 点击下一条
  (event: 'goto', position: number): void  // 跳转到指定位置
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  visible: false
})

const emit = defineEmits<Emits>()

const inputPosition = ref(props.currentPosition)

// 监听 currentPosition 的变化，更新输入框的值
watch(() => props.currentPosition, (newVal) => {
  inputPosition.value = newVal
})

const handleGoto = () => {
  if (!inputPosition.value || inputPosition.value < 1 || inputPosition.value > props.totalCount) {
    ElMessage.warning('请输入有效的位置（1-' + props.totalCount + '）')
    return
  }
  emit('goto', inputPosition.value)
}
</script>

<style scoped lang="scss">
.message-navigation-control {
  padding: 12px 16px;
  background: linear-gradient(135deg, #f5f7fa 0%, #f0f2f5 100%);
  border-bottom: 2px solid #d9d9d9;
  border-left: 3px solid #409eff;
  margin-bottom: 12px;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
  display: flex;
  justify-content: center;
  align-items: center;

  &:hover {
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  }

  :deep(.el-button-group) {
    display: flex;
    gap: 8px;
    align-items: center;
    flex-wrap: wrap;
    justify-content: center;

    .el-button {
      flex-shrink: 0;
      transition: all 0.3s ease;

      &:not(.is-disabled) {
        &:hover {
          background-color: #e6f7ff;
          transform: translateY(-1px);
        }

        &:active {
          transform: translateY(0);
        }
      }

      &.is-disabled {
        opacity: 0.6;
        cursor: not-allowed;
      }
    }

    .el-input {
      margin: 0 4px;
      width: 100px;

      :deep(.el-input__wrapper) {
        background-color: #fff;
        border: 1px solid #dcdfe6;
        border-radius: 4px;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02);
        transition: all 0.3s ease;

        &:hover {
          border-color: #409eff;
          box-shadow: 0 2px 4px rgba(64, 158, 255, 0.1);
        }

        &:focus-within {
          border-color: #409eff;
          box-shadow: 0 2px 8px rgba(64, 158, 255, 0.15);
        }
      }
    }
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .message-navigation-control {
    padding: 10px 12px;

    :deep(.el-button-group) {
      gap: 6px;

      .el-button {
        padding: 6px 8px;
        font-size: 12px;

        :deep(.el-icon) {
          font-size: 12px;
        }
      }

      .el-input {
        width: 70px;
        margin: 0 2px;
      }
    }
  }
}
</style>
