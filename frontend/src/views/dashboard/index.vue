<template>
  <div class="dashboard">
    <el-row :gutter="20">
      <el-col :xs="24" :sm="24" :md="12" :lg="8" :xl="6">
        <div class="grid-content">
          <el-card class="box-card">
            <div class="card-panel">
              <div class="card-panel-icon-wrapper icon-users">
                <el-icon class="card-panel-icon">
                  <User />
                </el-icon>
              </div>
              <div class="card-panel-description">
                <div class="card-panel-text">
                  TG用户数
                </div>
                <div class="card-panel-num">
                  {{ statistics.userCount }}
                </div>
              </div>
            </div>
          </el-card>
        </div>
      </el-col>

      <el-col :xs="24" :sm="24" :md="12" :lg="8" :xl="6">
        <div class="grid-content">
          <el-card class="box-card">
            <div class="card-panel">
              <div class="card-panel-icon-wrapper icon-groups">
                <el-icon class="card-panel-icon">
                  <ChatDotRound />
                </el-icon>
              </div>
              <div class="card-panel-description">
                <div class="card-panel-text">
                  TG群组
                </div>
                <div class="card-panel-num">
                  {{ statistics.groupCount }}
                </div>
              </div>
            </div>
          </el-card>
        </div>
      </el-col>

      <el-col :xs="24" :sm="24" :md="12" :lg="8" :xl="6">
        <div class="grid-content">
          <el-card class="box-card">
            <div class="card-panel">
              <div class="card-panel-icon-wrapper icon-messages">
                <el-icon class="card-panel-icon">
                  <ChatLineRound />
                </el-icon>
              </div>
              <div class="card-panel-description">
                <div class="card-panel-text">
                  TG聊天记录
                </div>
                <div class="card-panel-num">
                  {{ statistics.messageCount }}
                </div>
              </div>
            </div>
          </el-card>
        </div>
      </el-col>

      <el-col :xs="24" :sm="24" :md="12" :lg="8" :xl="6">
        <div class="grid-content">
          <el-card class="box-card">
            <div class="card-panel">
              <div class="card-panel-icon-wrapper icon-products">
                <el-icon class="card-panel-icon">
                  <Opportunity />
                </el-icon>
              </div>
              <div class="card-panel-description">
                <div class="card-panel-text">
                  黑词记录
                </div>
                <div class="card-panel-num">
                  {{ statistics.blackwordCount }}
                </div>
              </div>
            </div>
          </el-card>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="mt-20">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>项目文档</span>
            </div>
          </template>
          <div class="readme-content">
            <div v-html="readmeHtml"></div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { User, ChatDotRound, ChatLineRound, Opportunity } from '@element-plus/icons-vue'
import { marked } from 'marked'
import { dashboardApi, type DashboardStatistics } from '@/api/dashboard'
import { ElMessage } from 'element-plus'

// 统计数据
const statistics = ref({
  userCount: 0,
  groupCount: 0,
  messageCount: 0,
  blackwordCount: 0
})

// README内容
const readmeHtml = ref('')

// 获取README内容
const fetchReadme = async () => {
  try {
    const response = await fetch('/README.md')
    const markdown = await response.text()
    readmeHtml.value = await marked(markdown)
  } catch (error) {
    console.error('Failed to load README:', error)
    readmeHtml.value = '<p>无法加载项目文档</p>'
  }
}

// 获取统计数据
const fetchStatistics = async () => {
  try {
    const response = await dashboardApi.getStatistics()
    if (response.data.err_code === 0) {
      const data = response.data.payload
      statistics.value = {
        userCount: data.user_count,
        groupCount: data.group_count,
        messageCount: data.message_count,
        blackwordCount: data.blackword_count
      }
    } else {
      ElMessage.error(response.data.err_msg || '获取统计数据失败')
    }
  } catch (error) {
    console.error('获取统计数据失败:', error)
    ElMessage.error('获取统计数据失败')
  }
}

// 页面加载
onMounted(() => {
  // 加载统计数据
  fetchStatistics()
  
  // 加载README内容
  fetchReadme()
})
</script>

<style lang="scss" scoped>
.dashboard {
  padding: 0;

  .mt-20 {
    margin-top: 20px;
  }

  .box-card {
    height: 100px;
    cursor: pointer;
    transition: all 0.3s;

    &:hover {
      box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.2);
    }
  }

  .card-panel {
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 0;

    .card-panel-icon-wrapper {
      padding: 16px;
      margin-right: 16px;
      border-radius: 8px;

      &.icon-users {
        background: linear-gradient(45deg, #409eff, #66b1ff);
      }

      &.icon-groups {
        background: linear-gradient(45deg, #36d57a, #5daf34);
      }

      &.icon-messages {
        background: linear-gradient(45deg, #f78989, #f56565);
      }

      &.icon-products {
        background: linear-gradient(45deg, #ffc107, #ffb300);
      }

      .card-panel-icon {
        font-size: 24px;
        color: #fff;
      }
    }

    .card-panel-description {
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      flex: 1;

      .card-panel-text {
        line-height: 18px;
        color: var(--el-text-color-secondary);
        font-size: 14px;
        margin-bottom: 8px;
      }

      .card-panel-num {
        font-size: 24px;
        font-weight: bold;
        color: var(--el-text-color-primary);
      }
    }
  }

  .readme-content {
    :deep(h1) {
      color: var(--el-color-primary);
      margin-bottom: 16px;
      border-bottom: 2px solid var(--el-border-color);
      padding-bottom: 8px;
    }

    :deep(h2) {
      color: var(--el-color-primary);
      margin: 24px 0 16px 0;
      border-bottom: 1px solid var(--el-border-color-light);
      padding-bottom: 6px;
    }

    :deep(h3) {
      color: var(--el-text-color-primary);
      margin: 20px 0 12px 0;
    }

    :deep(p) {
      color: var(--el-text-color-regular);
      margin-bottom: 16px;
      line-height: 1.6;
    }

    :deep(ul) {
      color: var(--el-text-color-regular);
      line-height: 1.8;
      margin-bottom: 16px;

      li {
        margin-bottom: 8px;
      }
    }

    :deep(code) {
      background-color: var(--el-fill-color-light);
      padding: 2px 4px;
      border-radius: 3px;
      font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
      color: var(--el-color-danger);
    }

    :deep(pre) {
      background-color: var(--el-fill-color-light);
      border: 1px solid var(--el-border-color);
      border-radius: 6px;
      padding: 16px;
      margin: 16px 0;
      overflow-x: auto;

      code {
        background: none;
        padding: 0;
        color: var(--el-text-color-primary);
      }
    }

    :deep(blockquote) {
      border-left: 4px solid var(--el-color-primary);
      margin: 16px 0;
      padding-left: 16px;
      color: var(--el-text-color-secondary);
    }

    :deep(table) {
      width: 100%;
      border-collapse: collapse;
      margin: 16px 0;

      th, td {
        border: 1px solid var(--el-border-color);
        padding: 8px 12px;
        text-align: left;
      }

      th {
        background-color: var(--el-fill-color);
        font-weight: 600;
      }
    }
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-weight: 500;
  }
}
</style>