<template>
  <div class="user-profile-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>人员档案</span>
        </div>
      </template>

      <div class="profile-content">
        <!-- 左侧目录树 -->
        <div class="left-panel">
          <div class="tree-header">
            <span>档案目录</span>
            <el-button type="primary" size="small" text>
              <el-icon><Plus /></el-icon>
            </el-button>
          </div>
          <el-tree
            :data="treeData"
            :props="treeProps"
            node-key="id"
            default-expand-all
            highlight-current
            @node-click="handleNodeClick"
          >
            <template #default="{ node, data }">
              <span class="custom-tree-node">
                <el-icon v-if="data.type === 'folder'">
                  <Folder />
                </el-icon>
                <el-icon v-else>
                  <User />
                </el-icon>
                <span class="node-label">{{ node.label }}</span>
              </span>
            </template>
          </el-tree>
        </div>

        <!-- 右侧展示区域 -->
        <div class="right-panel">
          <div v-if="selectedNode && selectedNode.type === 'resource'" class="content-display">
            <div class="profile-header">
              <h2>{{ selectedNode.label }}</h2>
              <el-button type="primary" size="small">
                <el-icon><RefreshRight /></el-icon>
                刷新数据
              </el-button>
            </div>

            <el-divider />

            <!-- 7个信息面板 - 简历式布局 -->
            <div class="resume-layout">
              <!-- 面板1: 基本信息 -->
              <section class="resume-section">
                <div class="section-header">
                  <el-icon><Avatar /></el-icon>
                  <h3>基本信息</h3>
                </div>
                <div class="section-content">
                  <div class="user-header-compact">
                    <el-avatar :size="80" src="" class="user-avatar">
                      <el-icon :size="40"><UserFilled /></el-icon>
                    </el-avatar>
                    <div class="user-main-info-compact">
                      <div class="info-row">
                        <span class="label">昵称:</span>
                        <span class="value">{{ mockUserData.nickname || mockUserData.username }}</span>
                      </div>
                      <div class="info-row">
                        <span class="label">用户名:</span>
                        <span class="value">@{{ mockUserData.username }}</span>
                      </div>
                      <div class="info-row">
                        <span class="label">用户ID:</span>
                        <span class="value">{{ mockUserData.userId }}</span>
                      </div>
                      <div class="info-row">
                        <span class="label">备注名称:</span>
                        <span class="value">{{ mockUserData.remark || '暂无' }}</span>
                      </div>
                    </div>
                  </div>

                  <div class="stats-grid">
                    <div class="stat-item">
                      <span class="stat-label">消息总数</span>
                      <span class="stat-value">{{ mockUserData.messageCount }}</span>
                    </div>
                    <div class="stat-item">
                      <span class="stat-label">首次发言</span>
                      <span class="stat-value">{{ mockUserData.firstMessage }}</span>
                    </div>
                    <div class="stat-item">
                      <span class="stat-label">最后发言</span>
                      <span class="stat-value">{{ mockUserData.lastMessage }}</span>
                    </div>
                  </div>

                  <h4 class="section-title">所在群组 ({{ mockUserData.groups.length }})</h4>
                  <div class="groups-card-list">
                    <div
                      v-for="group in mockUserData.groups"
                      :key="group.id"
                      class="group-card"
                    >
                      <div class="group-card-name">{{ group.name }}</div>
                      <div class="group-card-meta">
                        <span class="group-msg-count">{{ group.messageCount }}条消息</span>
                        <span class="group-last-active">最后活跃: {{ group.lastActiveTime }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </section>

              <!-- 最近消息 -->
              <section class="resume-section">
                <div class="section-header">
                  <el-icon><ChatDotRound /></el-icon>
                  <h3>最近消息</h3>
                </div>
                <div class="section-content">
                  <el-table :data="mockRecentMessages" stripe size="small" style="width: 100%">
                    <el-table-column prop="groupName" label="群组名" width="120" />
                    <el-table-column prop="content" label="发言内容" show-overflow-tooltip />
                    <el-table-column prop="time" label="发言时间" width="150" />
                    <el-table-column label="操作" width="80" align="center">
                      <template #default>
                        <el-button type="primary" text size="small">查看</el-button>
                      </template>
                    </el-table-column>
                  </el-table>

                  <!-- 图片展示行 -->
                  <div class="photo-gallery">
                    <div v-for="i in 10" :key="i" class="photo-placeholder">
                      <el-icon :size="40"><PictureFilled /></el-icon>
                    </div>
                  </div>
                </div>
              </section>

              <!-- 面板2: 信息变动记录 -->
              <section class="resume-section">
                <div class="section-header">
                  <el-icon><Clock /></el-icon>
                  <h3>信息变动</h3>
                </div>
                <div class="section-content">
                  <div class="change-records-table">
                    <div
                      v-for="change in mockChanges"
                      :key="change.id"
                      class="change-record-row"
                    >
                      <div class="change-row-header">
                        <span class="change-type-badge">{{ change.type }}</span>
                        <span class="change-time-text">{{ change.time }}</span>
                      </div>
                      <div class="change-values">
                        <span class="old-value-text">{{ change.oldValue }}</span>
                        <el-icon class="arrow-icon"><Right /></el-icon>
                        <span class="new-value-text">{{ change.newValue }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </section>

              <!-- 面板3: 用户标签 -->
              <section class="resume-section">
                <div class="section-header">
                  <el-icon><PriceTag /></el-icon>
                  <h3>用户标签</h3>
                </div>
                <div class="section-content">
                  <el-table :data="mockTags" stripe border>
                    <el-table-column prop="tagName" label="标签名称" width="150">
                      <template #default="{ row }">
                        <el-tag type="success">{{ row.tagName }}</el-tag>
                      </template>
                    </el-table-column>
                    <el-table-column prop="keyword" label="触发关键词" width="150" />
                    <el-table-column prop="content" label="详细内容">
                      <template #default="{ row }">
                        <span v-html="highlightKeyword(row.content, row.keyword)"></span>
                      </template>
                    </el-table-column>
                    <el-table-column prop="createdAt" label="创建时间" width="180" />
                  </el-table>
                </div>
              </section>

              <!-- 面板4: 广告行为 -->
              <section class="resume-section">
                <div class="section-header">
                  <el-icon><PictureFilled /></el-icon>
                  <h3>广告行为</h3>
                </div>
                <div class="section-content">
                  <el-alert
                    title="功能开发中"
                    type="info"
                    description="广告行为追踪面板正在开发中,敬请期待..."
                    :closable="false"
                    show-icon
                    style="margin-bottom: 20px;"
                  />
                  <el-table :data="mockAds" stripe border>
                    <el-table-column prop="adType" label="广告类型" width="120">
                      <template #default="{ row }">
                        <el-tag :type="row.adType === '产品推广' ? 'success' : 'warning'">
                          {{ row.adType }}
                        </el-tag>
                      </template>
                    </el-table-column>
                    <el-table-column prop="merchant" label="目标商家" width="150" />
                    <el-table-column prop="content" label="广告内容" show-overflow-tooltip />
                    <el-table-column prop="publishTime" label="发布时间" width="180" />
                  </el-table>
                </div>
              </section>

              <!-- 面板5: 关联图谱 -->
              <section class="resume-section">
                <div class="section-header">
                  <el-icon><Share /></el-icon>
                  <h3>关联图谱</h3>
                </div>
                <div class="section-content">
                  <div class="graph-placeholder">
                    <el-icon :size="60" color="#909399"><Share /></el-icon>
                    <p class="graph-title">关联图谱 (ECharts 力导向图)</p>
                    <p class="hint">将展示用户、群组、商家、广告之间的关系网络</p>
                    <div class="graph-legend">
                      <div class="legend-item">
                        <span class="shape circle user"></span>
                        <span>用户(圆形)</span>
                      </div>
                      <div class="legend-item">
                        <span class="shape square group"></span>
                        <span>群组(方形)</span>
                      </div>
                      <div class="legend-item">
                        <span class="shape diamond merchant"></span>
                        <span>商家(菱形)</span>
                      </div>
                      <div class="legend-item">
                        <span class="shape triangle ad"></span>
                        <span>广告(三角形)</span>
                      </div>
                    </div>
                  </div>
                </div>
              </section>

              <!-- 面板6: AI画像 -->
              <section class="resume-section">
                <div class="section-header">
                  <el-icon><TrendCharts /></el-icon>
                  <h3>AI画像</h3>
                </div>
                <div class="section-content">
                  <el-alert
                    title="功能预留"
                    type="warning"
                    description="AI画像与风险评估功能将在后续版本实现"
                    :closable="false"
                    show-icon
                    style="margin-bottom: 20px;"
                  />
                  <div class="ai-placeholder">
                    <h4>用户画像</h4>
                    <div class="tags-cloud">
                      <el-tag
                        v-for="(tag, index) in mockAITags"
                        :key="tag"
                        :type="(['success', 'warning', 'info', 'danger'] as const)[index % 4]"
                        effect="plain"
                        size="large"
                      >
                        {{ tag }}
                      </el-tag>
                    </div>

                    <h4 style="margin-top: 30px;">风险评估</h4>
                    <div class="risk-section">
                      <el-rate v-model="mockRiskLevel" disabled show-score text-color="#ff9900" score-template="{value} 分" />
                      <p class="risk-description">
                        <strong>评估依据:</strong> 基于用户活动频率、广告发布行为、群组参与度等多维度分析
                      </p>
                    </div>
                  </div>
                </div>
              </section>

              <!-- 面板7: 用户记录 -->
              <section class="resume-section">
                <div class="section-header">
                  <el-icon><ChatDotRound /></el-icon>
                  <h3>用户记录</h3>
                </div>
                <div class="section-content">
                  <div class="comment-input">
                    <el-input
                      v-model="newComment"
                      type="textarea"
                      :rows="3"
                      placeholder="添加评论或备注..."
                      maxlength="500"
                      show-word-limit
                    />
                    <el-button type="primary" style="margin-top: 10px;">
                      <el-icon><CirclePlus /></el-icon>
                      发布评论
                    </el-button>
                  </div>

                  <el-divider />

                  <div class="comments-list">
                    <div v-for="comment in mockComments" :key="comment.id" class="comment-item">
                      <div class="comment-header">
                        <el-avatar :size="32">{{ comment.author[0] }}</el-avatar>
                        <div class="comment-meta">
                          <span class="author">{{ comment.author }}</span>
                          <span class="time">{{ comment.time }}</span>
                        </div>
                      </div>
                      <div class="comment-content">{{ comment.content }}</div>
                    </div>
                  </div>
                </div>
              </section>
            </div>
          </div>

          <div v-else class="empty-state">
            <el-empty description="请从左侧目录树选择一个用户档案">
              <template #image>
                <el-icon :size="80" color="#909399">
                  <FolderOpened />
                </el-icon>
              </template>
            </el-empty>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import {
  Folder,
  User,
  FolderOpened,
  Avatar,
  UserFilled,
  RefreshRight,
  Clock,
  PriceTag,
  PictureFilled,
  Share,
  TrendCharts,
  ChatDotRound,
  CirclePlus,
  Right,
  Plus
} from '@element-plus/icons-vue'

// 目录树数据结构
interface TreeNode {
  id: string
  label: string
  type: 'folder' | 'resource'
  children?: TreeNode[]
}

interface GroupInfo {
  id: string
  name: string
  messageCount: number
  lastActiveTime: string
}

interface UserInfo {
  userId: string
  username: string
  nickname?: string
  phone?: string
  remark?: string
  bio?: string
  lastSeen: string
  messageCount: number
  firstMessage: string
  lastMessage: string
  groups: GroupInfo[]
}

interface ChangeRecord {
  id: string
  type: string
  oldValue: string
  newValue: string
  time: string
}

interface TagRecord {
  tagName: string
  keyword: string
  content: string
  createdAt: string
}

interface AdRecord {
  adType: string
  merchant: string
  content: string
  publishTime: string
}

interface Comment {
  id: string
  author: string
  content: string
  time: string
}

// 测试数据 - 包含1级文件夹
const treeData = ref<TreeNode[]>([
  {
    id: '1',
    label: '商家',
    type: 'folder',
    children: [
      { id: '1-1', label: '商家A', type: 'resource' },
      { id: '1-2', label: '商家B', type: 'resource' },
      { id: '1-3', label: '商家C', type: 'resource' }
    ]
  },
  {
    id: '2',
    label: '嫌疑人',
    type: 'folder',
    children: [
      { id: '2-1', label: '嫌疑人A', type: 'resource' },
      { id: '2-2', label: '嫌疑人B', type: 'resource' },
      { id: '2-3', label: '嫌疑人C', type: 'resource' }
    ]
  },
  {
    id: '3',
    label: '买家',
    type: 'folder',
    children: [
      { id: '3-1', label: '买家A', type: 'resource' },
      { id: '3-2', label: '买家B', type: 'resource' },
      { id: '3-3', label: '买家C', type: 'resource' }
    ]
  }
])

// 树形组件配置
const treeProps = {
  children: 'children',
  label: 'label'
}

// 当前选中的节点
const selectedNode = ref<TreeNode | null>(null)

// 节点点击事件
const handleNodeClick = (data: TreeNode) => {
  selectedNode.value = data
}

// 占位符数据 - 面板1: 基本信息
const mockUserData = ref<UserInfo>({
  userId: '123456789',
  username: 'john_doe',
  nickname: 'John Doe',
  phone: '+86 138****5678',
  remark: '重要联系人',
  bio: '化工行业从业者,专注于有机化学领域',
  lastSeen: '2小时前',
  messageCount: 1234,
  firstMessage: '2024-01-15 10:20',
  lastMessage: '2025-01-14 16:30',
  groups: [
    { id: '1', name: '化工交流群', messageCount: 456, lastActiveTime: '2025-01-14 16:30' },
    { id: '2', name: '产品采购群', messageCount: 234, lastActiveTime: '2025-01-13 15:20' },
    { id: '3', name: '行业资讯', messageCount: 189, lastActiveTime: '2025-01-14 09:15' },
    { id: '4', name: '技术讨论组', messageCount: 267, lastActiveTime: '2025-01-12 14:40' },
    { id: '5', name: '供应商联盟', messageCount: 88, lastActiveTime: '2025-01-11 11:25' }
  ]
})

// 占位符数据 - 最近消息
const mockRecentMessages = ref([
  { groupName: '化工交流群', content: '请问这批聚乙烯的价格是多少?', time: '2025-01-14 16:30' },
  { groupName: '产品采购群', content: '我们需要采购一批乙酸乙酯，有货源的联系', time: '2025-01-14 15:45' },
  { groupName: '化工交流群', content: '最近原料价格波动比较大，大家注意控制成本', time: '2025-01-14 14:20' },
  { groupName: '行业资讯', content: '分享一篇关于化工行业的最新政策解读', time: '2025-01-14 09:15' },
  { groupName: '技术讨论组', content: '这个工艺流程有没有优化空间?', time: '2025-01-13 18:30' },
  { groupName: '化工交流群', content: '感谢大家的支持，合作愉快！', time: '2025-01-13 16:10' },
  { groupName: '供应商联盟', content: '下周有一批新货到，有需要的可以联系', time: '2025-01-13 11:25' },
  { groupName: '产品采购群', content: '质量很好，已经收到货了', time: '2025-01-12 14:50' },
  { groupName: '行业资讯', content: '转发：2025年化工行业发展趋势报告', time: '2025-01-12 10:30' },
  { groupName: '技术讨论组', content: '这个问题我之前遇到过，可以这样解决...', time: '2025-01-11 17:40' }
])

// 占位符数据 - 面板2: 信息变动
const mockChanges = ref<ChangeRecord[]>([
  {
    id: '1',
    type: '用户名变更',
    oldValue: 'john_old',
    newValue: 'john_doe',
    time: '2025-01-10 14:30'
  },
  {
    id: '2',
    type: '个人简介更新',
    oldValue: '化工从业者',
    newValue: '化工行业从业者,专注于有机化学领域',
    time: '2025-01-08 09:15'
  },
  {
    id: '3',
    type: '头像更换',
    oldValue: '默认头像',
    newValue: '自定义头像',
    time: '2025-01-05 16:20'
  },
  {
    id: '4',
    type: '电话号码更新',
    oldValue: '+86 139****1234',
    newValue: '+86 138****5678',
    time: '2025-01-03 11:45'
  },
  {
    id: '5',
    type: '备注名称修改',
    oldValue: '普通联系人',
    newValue: '重要联系人',
    time: '2025-01-01 08:00'
  }
])

// 占位符数据 - 面板3: 用户标签
const mockTags = ref<TagRecord[]>([
  {
    tagName: '化工产品',
    keyword: '聚乙烯',
    content: '我们公司主要经营聚乙烯和聚丙烯等化工原料',
    createdAt: '2025-01-10 10:20'
  },
  {
    tagName: '采购意向',
    keyword: '求购',
    content: '求购一批工业级别的乙酸乙酯,有货的联系',
    createdAt: '2025-01-09 15:30'
  },
  {
    tagName: '价格敏感',
    keyword: '价格',
    content: '请问这批货的价格是多少?能不能再便宜点?',
    createdAt: '2025-01-08 14:15'
  },
  {
    tagName: '物流关注',
    keyword: '发货',
    content: '什么时候可以发货?物流大概多久能到?',
    createdAt: '2025-01-07 09:45'
  }
])

// 占位符数据 - 面板4: 广告行为
const mockAds = ref<AdRecord[]>([
  {
    adType: '产品推广',
    merchant: '化工原料批发商',
    content: '优质聚乙烯现货供应,价格优惠,欢迎咨询',
    publishTime: '2025-01-10 16:30'
  },
  {
    adType: '招商加盟',
    merchant: '化学试剂公司',
    content: '诚招各地区代理商,提供一手货源和技术支持',
    publishTime: '2025-01-08 11:20'
  },
  {
    adType: '产品推广',
    merchant: '有机化合物供应',
    content: '工业级乙酸乙酯,品质保证,支持小批量采购',
    publishTime: '2025-01-05 14:45'
  }
])

// 占位符数据 - 面板6: AI标签
const mockAITags = ref<string[]>([
  '化工从业者',
  '采购决策者',
  '价格敏感',
  '活跃用户',
  '多群参与',
  '可信度高',
  '长期客户'
])

const mockRiskLevel = ref(3.5)

// 占位符数据 - 面板7: 用户记录
const mockComments = ref<Comment[]>([
  {
    id: '1',
    author: '张三',
    content: '该用户是重要的采购决策者,建议重点跟进',
    time: '2025-01-10 15:30'
  },
  {
    id: '2',
    author: '李四',
    content: '用户最近在多个群组中询问聚乙烯的价格,可能有大批量采购需求',
    time: '2025-01-09 10:20'
  },
  {
    id: '3',
    author: '王五',
    content: '已添加联系方式,初步沟通顺利',
    time: '2025-01-08 14:15'
  }
])

const newComment = ref('')

// 高亮关键词
const highlightKeyword = (content: string, keyword: string) => {
  if (!keyword) return content
  const regex = new RegExp(`(${keyword})`, 'gi')
  return content.replace(regex, '<span class="highlight">$1</span>')
}
</script>

<style scoped lang="scss">
.user-profile-container {
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
    font-size: 18px;
    font-weight: 600;
  }

  .profile-content {
    display: flex;
    gap: 20px;
    flex: 1;
    overflow: hidden;

    .left-panel {
      flex: 0 0 280px;
      border-right: 1px solid #e4e7ed;
      padding-right: 20px;
      overflow-y: auto;

      .tree-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
        font-size: 16px;
        font-weight: 600;
        color: #303133;
      }

      .custom-tree-node {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 14px;

        .el-icon {
          font-size: 16px;
        }

        .node-label {
          flex: 1;
        }
      }

      :deep(.el-tree-node__content) {
        height: 36px;
        border-radius: 4px;
        margin-bottom: 4px;

        &:hover {
          background-color: #f5f7fa;
        }
      }

      :deep(.el-tree-node.is-current > .el-tree-node__content) {
        background-color: #ecf5ff;
        color: #409eff;
      }
    }

    .right-panel {
      flex: 1;
      padding-left: 20px;
      overflow-y: auto;

      .content-display {
        .profile-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;

          h2 {
            margin: 0;
            font-size: 24px;
            font-weight: 600;
            color: #303133;
          }
        }

        .el-divider {
          margin: 16px 0;
        }

        .resume-layout {
          display: flex;
          flex-direction: column;
          gap: 16px;

          .resume-section {
            background-color: #fff;
            border: 1px solid #e4e7ed;
            border-radius: 4px;
            overflow: hidden;

            .section-header {
              display: flex;
              align-items: center;
              gap: 8px;
              padding: 8px 16px;
              background-color: #f5f7fa;
              border-bottom: 1px solid #e4e7ed;

              .el-icon {
                font-size: 16px;
                color: #606266;
              }

              h3 {
                margin: 0;
                font-size: 14px;
                font-weight: 600;
                color: #303133;
              }
            }

            .section-content {
              padding: 16px;

              // 基本信息 - 紧凑布局
              .user-header-compact {
                display: flex;
                gap: 16px;
                margin-bottom: 16px;

                .user-avatar {
                  flex-shrink: 0;
                }

                .user-main-info-compact {
                  flex: 1;
                  display: flex;
                  flex-direction: column;
                  gap: 6px;

                  .info-row {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    font-size: 13px;

                    .label {
                      color: #909399;
                      min-width: 65px;
                      font-weight: 500;
                    }

                    .value {
                      color: #303133;
                      font-weight: 400;
                    }
                  }
                }
              }

              // 统计数据网格
              .stats-grid {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 12px;
                margin: 16px 0;
                padding: 12px;
                background-color: #f9fafb;
                border-radius: 6px;

                .stat-item {
                  display: flex;
                  flex-direction: column;
                  align-items: center;
                  gap: 6px;
                  padding: 8px;
                  background-color: #fff;
                  border-radius: 4px;
                  border: 1px solid #e4e7ed;

                  .stat-label {
                    font-size: 12px;
                    color: #909399;
                  }

                  .stat-value {
                    font-size: 16px;
                    font-weight: 600;
                    color: #303133;
                  }
                }
              }

              .info-section {
                margin: 12px 0;

                .info-item {
              display: flex;
              padding: 8px 0;
              border-bottom: 1px solid #f0f0f0;

              &:last-child {
                border-bottom: none;
              }

              .label {
                width: 100px;
                color: #909399;
                font-size: 13px;
              }

                  .value {
                    flex: 1;
                    color: #606266;
                    font-size: 13px;
                  }
                }
              }

              .section-title {
                margin: 12px 0 8px 0;
                font-size: 14px;
                font-weight: 600;
                color: #303133;
              }

              // 群组卡片列表
              .groups-card-list {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 8px;

                .group-card {
                  padding: 10px 12px;
                  background-color: #fafafa;
                  border: 1px solid #e4e7ed;
                  border-radius: 6px;
                  cursor: pointer;
                  transition: all 0.3s ease;

                  &:hover {
                    border-color: #409eff;
                    background-color: #ecf5ff;
                    box-shadow: 0 2px 4px rgba(64, 158, 255, 0.1);
                  }

                  .group-card-name {
                    font-size: 13px;
                    font-weight: 500;
                    color: #303133;
                    margin-bottom: 6px;
                  }

                  .group-card-meta {
                    display: flex;
                    justify-content: space-between;
                    font-size: 11px;
                    color: #909399;

                    .group-msg-count {
                      color: #409eff;
                      font-weight: 500;
                    }
                  }
                }
              }

              // 信息变动 - 表格样式
              .change-records-table {
                display: flex;
                flex-direction: column;
                gap: 8px;

                .change-record-row {
                  padding: 10px 12px;
                  background-color: #fafafa;
                  border: 1px solid #e4e7ed;
                  border-radius: 4px;
                  transition: all 0.3s ease;

                  &:hover {
                    background-color: #f0f8ff;
                    border-color: #d9ecff;
                  }

                  .change-row-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 8px;
                    padding-bottom: 6px;
                    border-bottom: 1px solid #e4e7ed;

                    .change-type-badge {
                      font-size: 12px;
                      font-weight: 600;
                      color: #409eff;
                      background-color: #ecf5ff;
                      padding: 2px 8px;
                      border-radius: 10px;
                    }

                    .change-time-text {
                      font-size: 11px;
                      color: #909399;
                    }
                  }

                  .change-values {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    font-size: 12px;

                    .old-value-text {
                      flex: 1;
                      padding: 4px 8px;
                      background-color: #fff2e8;
                      color: #e6a23c;
                      border-radius: 4px;
                      border: 1px solid #ffd591;
                      word-break: break-all;
                    }

                    .arrow-icon {
                      color: #909399;
                      font-size: 14px;
                      flex-shrink: 0;
                    }

                    .new-value-text {
                      flex: 1;
                      padding: 4px 8px;
                      background-color: #f0f9ff;
                      color: #67c23a;
                      border-radius: 4px;
                      border: 1px solid #b7eb8f;
                      word-break: break-all;
                      font-weight: 500;
                    }
                  }
                }
              }

              // 最近消息和图片展示
              .photo-gallery {
                display: flex;
                gap: 8px;
                margin-top: 16px;
                padding-top: 16px;
                border-top: 1px solid #e4e7ed;
                overflow-x: auto;

                .photo-placeholder {
                  flex-shrink: 0;
                  width: 80px;
                  height: 80px;
                  background-color: #f5f7fa;
                  border: 1px dashed #d9d9d9;
                  border-radius: 4px;
                  display: flex;
                  align-items: center;
                  justify-content: center;
                  color: #c0c4cc;
                  transition: all 0.3s ease;
                  cursor: pointer;

                  &:hover {
                    background-color: #ecf5ff;
                    border-color: #409eff;
                    color: #409eff;
                  }
                }
              }

              // 面板3: 用户标签 - 紧凑表格
              :deep(.el-table) {
                font-size: 13px;

                th {
                  padding: 8px 0;
                  background-color: #fafafa;
                }

                td {
                  padding: 8px 0;
                }
              }

              :deep(.highlight) {
                background-color: #fff566;
                padding: 2px 4px;
                border-radius: 2px;
                font-weight: 600;
              }

              // 面板5: 关联图谱 - 压缩高度
              .graph-placeholder {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                min-height: 300px;
                padding: 24px;
                background-color: #f5f7fa;
                border-radius: 4px;

                .graph-title {
                  font-size: 16px;
                  font-weight: 600;
                  color: #303133;
                  margin: 12px 0 6px 0;
                }

                .hint {
                  color: #909399;
                  margin-bottom: 20px;
                  font-size: 13px;
                }

                .graph-legend {
                  display: flex;
                  gap: 20px;
                  flex-wrap: wrap;
                  justify-content: center;

                  .legend-item {
                    display: flex;
                    align-items: center;
                    gap: 6px;
                    font-size: 13px;

                    .shape {
                      display: inline-block;
                    }

                    .circle {
                      width: 16px;
                      height: 16px;
                      border-radius: 50%;

                      &.user {
                        background-color: #409eff;
                      }
                    }

                    .square {
                      width: 16px;
                      height: 16px;

                      &.group {
                        background-color: #67c23a;
                      }
                    }

                    .diamond {
                      width: 16px;
                      height: 16px;
                      transform: rotate(45deg);

                      &.merchant {
                        background-color: #e6a23c;
                      }
                    }

                    .triangle {
                      width: 0;
                      height: 0;
                      border-left: 8px solid transparent;
                      border-right: 8px solid transparent;
                      border-bottom: 16px solid #f56c6c;

                      &.ad {
                        border-bottom-color: #f56c6c;
                      }
                    }
                  }
                }
              }

              // 面板6: AI画像 - 紧凑显示
              .ai-placeholder {
                h4 {
                  margin: 0 0 12px 0;
                  font-size: 14px;
                  font-weight: 600;
                  color: #303133;
                }

                .tags-cloud {
                  display: flex;
                  gap: 8px;
                  flex-wrap: wrap;
                  padding: 12px;
                  background-color: #f5f7fa;
                  border-radius: 4px;

                  .el-tag {
                    font-size: 13px;
                    padding: 4px 12px;
                  }
                }

                .risk-section {
                  padding: 12px;
                  background-color: #fef0f0;
                  border-radius: 4px;
                  border: 1px solid #fde2e2;

                  .el-rate {
                    margin-bottom: 8px;
                  }

                  .risk-description {
                    margin: 0;
                    color: #606266;
                    font-size: 12px;
                    line-height: 1.5;
                  }
                }
              }

              // 面板7: 用户记录 - 紧凑显示
              .comment-input {
                margin-bottom: 12px;

                :deep(.el-textarea__inner) {
                  font-size: 13px;
                }
              }

              .comments-list {
                .comment-item {
                  padding: 12px;
                  margin-bottom: 10px;
                  background-color: #f5f7fa;
                  border-radius: 4px;
                  transition: all 0.3s;

                  &:hover {
                    background-color: #ecf5ff;
                  }

                  .comment-header {
                    display: flex;
                    gap: 10px;
                    margin-bottom: 8px;

                    .el-avatar {
                      width: 28px;
                      height: 28px;
                    }

                    .comment-meta {
                      flex: 1;
                      display: flex;
                      flex-direction: column;
                      justify-content: center;

                      .author {
                        font-weight: 600;
                        color: #303133;
                        font-size: 13px;
                      }

                      .time {
                        font-size: 11px;
                        color: #909399;
                        margin-top: 2px;
                      }
                    }
                  }

                  .comment-content {
                    padding-left: 38px;
                    color: #606266;
                    font-size: 13px;
                    line-height: 1.5;
                  }
                }
              }
            }
          }
        }
      }

      .empty-state {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 100%;
        min-height: 400px;
      }
    }
  }
}
</style>
