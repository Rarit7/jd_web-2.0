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
            <el-button type="primary" size="small" text @click="handleAddFolder">
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
              <span class="custom-tree-node" @contextmenu.prevent="handleTreeNodeContextMenu($event, node, data)">
                <el-icon v-if="data.type === 'folder'">
                  <Folder />
                </el-icon>
                <el-icon v-else>
                  <User />
                </el-icon>
                <span class="node-label">{{ node.label }}</span>
                <!-- 档案状态标签 - 已生成状态不显示 -->
                <el-tag v-if="data.type === 'resource' && data.status && data.status !== 'generated'" :type="getStatusTagType(data.status)" size="small" class="status-badge">
                  {{ getStatusLabel(data.status) }}
                </el-tag>
                <!-- 文件夹操作按钮 -->
                <div class="node-actions" v-if="data.type === 'folder'" @click.stop>
                  <el-button-group>
                    <el-button size="small" text type="primary" @click.stop="openFolderEditor(data)">
                      <el-icon><Edit /></el-icon>
                    </el-button>
                    <el-button size="small" text type="danger" @click.stop="openFolderDeleter(data)">
                      <el-icon><Delete /></el-icon>
                    </el-button>
                  </el-button-group>
                </div>
              </span>
            </template>
          </el-tree>
        </div>

        <!-- 右侧展示区域 -->
        <div class="right-panel">
          <div v-if="selectedNode && selectedNode.type === 'resource'" class="content-display">
            <div class="profile-header">
              <div class="profile-title-section">
                <h2>{{ selectedNode.label }}</h2>
                <el-tag v-if="(selectedNode as any).status" :type="getStatusTagType((selectedNode as any).status)" class="header-status-badge">
                  <el-icon style="margin-right: 4px;" :class="`status-icon-${(selectedNode as any).status}`">
                    <component :is="getStatusIcon((selectedNode as any).status)" />
                  </el-icon>
                  {{ getStatusLabel((selectedNode as any).status) }}
                </el-tag>
              </div>
              <el-button type="primary" size="small" @click="handleEditProfile">
                <el-icon><Edit /></el-icon>
                编辑档案
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
                <div class="section-content" v-loading="userDataLoading">
                  <div class="user-header-compact">
                    <el-avatar :size="80" :src="mockUserData.avatar" class="user-avatar">
                      <el-icon :size="40"><UserFilled /></el-icon>
                    </el-avatar>
                    <div class="user-main-info-compact">
                      <!-- 昵称行 - 大字体显示,备注以灰色括号跟随 -->
                      <div class="nickname-row">
                        <span class="nickname-text">{{ mockUserData.nickname || mockUserData.username || mockUserData.userId }}</span>
                        <span v-if="mockUserData.remark" class="remark-text">({{ mockUserData.remark }})</span>
                      </div>
                      <!-- 用户名行 -->
                      <div v-if="mockUserData.username" class="username-row">
                        <span class="username-text">@{{ mockUserData.username }}</span>
                      </div>
                      <!-- 用户ID行 -->
                      <div class="userid-row">
                        <span class="userid-text">{{ mockUserData.userId }}</span>
                      </div>
                      <!-- 个人简介 -->
                      <div v-if="mockUserData.bio" class="bio-row">
                        <span class="bio-text">{{ mockUserData.bio }}</span>
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
                      @click="navigateToGroupMessages(group)"
                      :title="'点击查看此用户在「' + group.name + '」的聊天记录'"
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
                <div class="section-content" v-loading="recentMessagesLoading">
                  <div v-if="mockRecentMessages.length === 0 && !recentMessagesLoading" class="empty-message">
                    <el-empty description="暂无消息记录" />
                  </div>
                  <transition-group v-else name="message-list" tag="div">
                    <el-table
                      v-if="mockRecentMessages.length > 0"
                      key="table"
                      :data="mockRecentMessages"
                      stripe
                      size="small"
                      style="width: 100%"
                    >
                      <el-table-column prop="groupName" label="群组名" width="120" />
                      <el-table-column prop="content" label="发言内容" show-overflow-tooltip />
                      <el-table-column prop="time" label="发言时间" width="150" />
                      <el-table-column label="操作" width="80" align="center">
                        <template #default>
                          <el-button type="primary" text size="small">查看</el-button>
                        </template>
                      </el-table-column>
                    </el-table>
                  </transition-group>

                  <!-- 图片展示行 -->
                  <div class="photo-gallery">
                    <div v-if="mockPhotos.length > 0" class="image-row">
                      <div
                        v-for="(photo, index) in mockPhotos"
                        :key="photo.message_id"
                        class="image-item-wrapper"
                      >
                        <img
                          :src="`/static/${photo.path}`"
                          :alt="`Image ${index}`"
                          class="message-image"
                          @click="openImagePreview(index)"
                          @error="handleImageError"
                        />
                      </div>
                    </div>
                    <div v-else class="photo-empty">
                      <el-icon :size="40"><PictureFilled /></el-icon>
                      <p>暂无图片</p>
                    </div>
                  </div>

                  <!-- 图片预览对话框 -->
                  <el-dialog
                    v-model="imagePreviewVisible"
                    :show-close="true"
                    :close-on-click-modal="true"
                    :close-on-press-escape="true"
                    @keydown.left="previousImage"
                    @keydown.right="nextImage"
                  >
                    <div class="image-preview-container">
                      <div v-if="currentImageIndex >= 0 && mockPhotos[currentImageIndex]" class="preview-content">
                        <img
                          :src="`/static/${mockPhotos[currentImageIndex].path}`"
                          class="preview-image"
                          @error="handleImageError"
                        />
                        <div class="preview-nav">
                          <button @click="previousImage" class="nav-btn" :disabled="currentImageIndex === 0">
                            <el-icon><ArrowLeft /></el-icon>
                          </button>
                          <span class="preview-counter">{{ currentImageIndex + 1 }} / {{ mockPhotos.length }}</span>
                          <button @click="nextImage" class="nav-btn" :disabled="currentImageIndex === mockPhotos.length - 1">
                            <el-icon><ArrowRight /></el-icon>
                          </button>
                        </div>
                      </div>
                    </div>
                  </el-dialog>
                </div>
              </section>

              <!-- 面板2: 信息变动记录 -->
              <section class="resume-section">
                <div class="section-header">
                  <el-icon><Clock /></el-icon>
                  <h3>信息变动</h3>
                </div>
                <div class="section-content" v-loading="changeRecordsLoading">
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

                      <!-- 头像变动 - 显示图片 -->
                      <div v-if="change.changeType === 3" class="change-values avatar-change-values">
                        <div class="avatar-change-item">
                          <span class="change-label-text">变动前:</span>
                          <div v-if="!change.originalValue || change.originalValue === '(空)'" class="empty-avatar-box">
                            无头像
                          </div>
                          <el-avatar
                            v-else
                            :size="40"
                            :src="formatAvatarUrl(change.originalValue)"
                            shape="square"
                            class="change-avatar-img"
                          />
                        </div>
                        <el-icon class="arrow-icon"><Right /></el-icon>
                        <div class="avatar-change-item">
                          <span class="change-label-text">变动后:</span>
                          <div v-if="!change.newOriginalValue || change.newOriginalValue === '(空)'" class="empty-avatar-box">
                            无头像
                          </div>
                          <el-avatar
                            v-else
                            :size="40"
                            :src="formatAvatarUrl(change.newOriginalValue)"
                            shape="square"
                            class="change-avatar-img"
                          />
                        </div>
                      </div>

                      <!-- 非头像变动 - 显示文字 -->
                      <div v-else class="change-values">
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
                <div class="section-content" v-loading="tagsLoading">
                  <el-table :data="mockTags" stripe border>
                    <el-table-column prop="tagName" label="标签名称" width="150">
                      <template #default="{ row }">
                        <el-tag type="success">{{ row.tagName }}</el-tag>
                      </template>
                    </el-table-column>
                    <el-table-column prop="keyword" label="触发关键词" width="150" />
                    <el-table-column prop="content" label="详细内容">
                      <template #default="{ row }">
                        <HighlightText
                          v-if="row.originalText"
                          :text="row.originalText"
                          :keywords="row.keyword"
                        />
                        <span v-else>{{ row.content }}</span>
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

    <!-- 编辑档案对话框 -->
    <el-dialog
      v-model="editProfileDialogVisible"
      title="编辑档案"
      width="500px"
      @close="resetEditForm"
    >
      <el-form
        ref="editFormRef"
        :model="editProfileForm"
        :rules="editProfileRules"
        label-width="100px"
      >
        <el-form-item label="档案标题" prop="profile_name">
          <el-input
            v-model="editProfileForm.profile_name"
            placeholder="请输入档案标题"
            clearable
          />
        </el-form-item>

        <el-form-item label="所属目录" prop="folder_id">
          <el-tree-select
            v-model="editProfileForm.folder_id"
            :data="folderOnlyData"
            :props="treeSelectorProps"
            clearable
            placeholder="选择所属目录（可选）"
          />
        </el-form-item>

        <el-form-item label="档案状态" prop="status">
          <el-select
            v-model="editProfileForm.status"
            placeholder="请选择档案状态"
          >
            <el-option label="草稿" value="draft" />
            <el-option label="已生成" value="generated" />
            <el-option label="已归档" value="archived" />
          </el-select>
        </el-form-item>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="editProfileDialogVisible = false">取消</el-button>
          <el-button type="danger" @click="handleDeleteProfile">删除档案</el-button>
          <el-button type="primary" @click="handleSaveProfile">保存</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 文件夹管理对话框 -->
    <FolderManager
      ref="folderManagerRef"
      :parent-folder-id="selectedParentFolderId"
      :current-folder-id="selectedFolderId"
      :current-folder-name="selectedFolderName"
      :user-id="currentUserId"
      @success="handleFolderManagerSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store/modules/user'
import {
  Folder,
  User,
  FolderOpened,
  Avatar,
  UserFilled,
  Clock,
  PriceTag,
  PictureFilled,
  Share,
  TrendCharts,
  ChatDotRound,
  CirclePlus,
  Right,
  Plus,
  ArrowLeft,
  ArrowRight,
  Edit,
  Delete,
  DocumentCopy,
  CircleCheck,
  FolderDelete
} from '@element-plus/icons-vue'
import { profileFolderApi, userProfileApi, type FolderTreeNode } from '@/api/user-profile'
import { tgUsersApi } from '@/api/tg-users'
import { chatHistoryApi } from '@/api/chat-history'
import { tagsApi } from '@/api/tags'
import HighlightText from '@/components/HighlightText.vue'
import FolderManager from '@/components/UserProfile/FolderManager.vue'

// Router 实例
const router = useRouter()

// 用户 Store
const userStore = useUserStore()

// FolderManager 组件 ref
const folderManagerRef = ref<InstanceType<typeof FolderManager>>()

// 获取当前登录用户ID
const currentUserId = computed(() => userStore.userInfo?.id || 1)

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
  avatar?: string
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
  changeType: number  // 1:显示名称 2:用户名 3:头像 4:个人简介
  oldValue: string
  newValue: string
  originalValue: string  // 用于头像变动前的原始路径
  newOriginalValue: string  // 用于头像变动后的原始路径
  time: string
}

interface TagRecord {
  tagName: string
  keyword: string
  content: string
  originalText?: string  // 原始文本用于高亮
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

// 树形数据（从API加载）
const treeData = ref<FolderTreeNode[]>([])
const loading = ref(false)

// 树形组件配置
const treeProps = {
  children: 'children',
  label: 'label'
}

// 当前选中的节点
const selectedNode = ref<TreeNode | null>(null)

// 文件夹管理相关状态
const selectedParentFolderId = ref<number | null>(null)
const selectedFolderId = ref<number | undefined>(undefined)
const selectedFolderName = ref('')

// 节点点击事件
const handleNodeClick = (data: FolderTreeNode) => {
  selectedNode.value = data
}

// 加载文件夹树
const loadFolderTree = async () => {
  try {
    loading.value = true
    const response = await profileFolderApi.getTree()
    if ((response.data as any).err_code === 0) {
      treeData.value = (response.data as any).payload.tree_data
    } else {
      ElMessage.error((response.data as any).err_msg || '加载文件夹树失败')
    }
  } catch (error: any) {
    console.error('加载文件夹树失败:', error)
    ElMessage.error('加载文件夹树失败')
  } finally {
    loading.value = false
  }
}

// 点击'+'按钮打开新建文件夹对话框
const handleAddFolder = () => {
  selectedParentFolderId.value = null
  if (folderManagerRef.value) {
    folderManagerRef.value.openAdd()
  }
}

// 打开文件夹编辑对话框
const openFolderEditor = (data: FolderTreeNode) => {
  const folderId = parseInt(data.id.replace('folder_', ''))
  selectedFolderId.value = folderId
  selectedFolderName.value = data.label
  if (folderManagerRef.value) {
    folderManagerRef.value.openEdit(folderId, data.label)
  }
}

// 打开文件夹删除对话框
const openFolderDeleter = (data: FolderTreeNode) => {
  const folderId = parseInt(data.id.replace('folder_', ''))
  selectedFolderId.value = folderId
  selectedFolderName.value = data.label
  if (folderManagerRef.value) {
    folderManagerRef.value.openDelete(folderId, data.label)
  }
}

// 树节点右键菜单事件
const handleTreeNodeContextMenu = (_event: MouseEvent, _node: any, data: FolderTreeNode) => {
  // 可以在这里添加右键菜单功能，暂时保留以供后续扩展
  console.log('右键点击节点:', data)
}

// 文件夹管理成功回调
const handleFolderManagerSuccess = async () => {
  // 重新加载文件夹树
  await loadFolderTree()
  // 清空相关状态
  selectedParentFolderId.value = null
  selectedFolderId.value = undefined
  selectedFolderName.value = ''
}

// ==================== 编辑档案相关 ====================

interface EditProfileForm {
  profile_name: string
  folder_id: number | null
  status: 'draft' | 'generated' | 'archived'
}

const editProfileDialogVisible = ref(false)
const editFormRef = ref()
const editProfileForm = reactive<EditProfileForm>({
  profile_name: '',
  folder_id: null,
  status: 'draft'
})

const editProfileRules = {
  profile_name: [
    { required: true, message: '请输入档案标题', trigger: 'blur' },
    { min: 1, max: 200, message: '档案标题长度在 1 到 200 个字符之间', trigger: 'blur' }
  ]
}

const treeSelectorProps = {
  children: 'children',
  label: 'label',
  value: 'folder_numeric_id'
}

// 过滤出只包含文件夹的树形数据
const folderOnlyData = computed(() => {
  const filterFolders = (nodes: any[]): any[] => {
    return nodes
      .filter(node => node.type === 'folder')
      .map(node => {
        // 从 "folder_123" 格式中提取数字 ID
        const numericId = parseInt((node.id as string).replace('folder_', ''))
        return {
          ...node,
          folder_numeric_id: numericId,
          children: node.children ? filterFolders(node.children) : []
        }
      })
  }

  return filterFolders(treeData.value)
})

// 打开编辑档案对话框
const handleEditProfile = () => {
  if (!selectedNode.value || selectedNode.value.type !== 'resource') {
    ElMessage.warning('请先选择一个档案')
    return
  }

  editProfileForm.profile_name = selectedNode.value.label
  // 获取档案所属的文件夹ID，默认选中
  editProfileForm.folder_id = (selectedNode.value as any).folder_id ?? null
  editProfileForm.status = (selectedNode.value as any).status || 'draft'
  editProfileDialogVisible.value = true
}

// 保存档案
const handleSaveProfile = async () => {
  if (!editFormRef.value) return

  await editFormRef.value.validate(async (valid: boolean) => {
    if (valid) {
      try {
        if (!selectedNode.value || selectedNode.value.type !== 'resource') return

        const profileId = parseInt((selectedNode.value.id as string).replace('profile_', ''))

        const response = await userProfileApi.update(profileId, {
          profile_name: editProfileForm.profile_name,
          status: editProfileForm.status,
          folder_id: editProfileForm.folder_id
        })

        if ((response.data as any).err_code === 0) {
          ElMessage.success('档案保存成功')

          // 更新选中节点的状态，使右侧面板的badge实时更新
          if (selectedNode.value) {
            const updatedNode = { ...selectedNode.value }
            updatedNode.label = editProfileForm.profile_name
            ;(updatedNode as any).status = editProfileForm.status
            ;(updatedNode as any).folder_id = editProfileForm.folder_id
            selectedNode.value = updatedNode
          }

          editProfileDialogVisible.value = false
          await loadFolderTree()
        } else {
          ElMessage.error((response.data as any).err_msg || '保存档案失败')
        }
      } catch (error: any) {
        console.error('保存档案失败:', error)
        ElMessage.error('保存档案失败')
      }
    }
  })
}

// 删除档案
const handleDeleteProfile = async () => {
  ElMessageBox.confirm('确认删除此档案吗？删除后不可恢复', '删除确认', {
    confirmButtonText: '确认删除',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      if (!selectedNode.value || selectedNode.value.type !== 'resource') return

      const profileId = parseInt((selectedNode.value.id as string).replace('profile_', ''))

      const response = await userProfileApi.delete(profileId)

      if ((response.data as any).err_code === 0) {
        ElMessage.success('档案删除成功')
        editProfileDialogVisible.value = false
        selectedNode.value = null
        await loadFolderTree()
      } else {
        ElMessage.error((response.data as any).err_msg || '删除档案失败')
      }
    } catch (error: any) {
      console.error('删除档案失败:', error)
      ElMessage.error('删除档案失败')
    }
  }).catch(() => {
    // 取消删除
  })
}

const resetEditForm = () => {
  if (editFormRef.value) {
    editFormRef.value.clearValidate()
  }
  editProfileForm.profile_name = ''
  editProfileForm.folder_id = null
  editProfileForm.status = 'draft'
}

// 用户详情加载状态
const userDataLoading = ref(false)

// 变动记录相关数据
const changeRecordsLoading = ref(false)

// 标签加载状态
const tagsLoading = ref(false)

// 加载用户基本信息
const loadUserBasicInfo = async (user_id: string) => {
  if (!user_id) return

  userDataLoading.value = true
  try {
    // 获取用户详细信息
    const userResponse = await tgUsersApi.getUserByUserId(user_id)
    if (userResponse.data.err_code === 0) {
      const userData = userResponse.data.payload

      // 更新mockUserData的基本信息
      mockUserData.value.userId = userData.user_id
      mockUserData.value.username = userData.username || ''
      mockUserData.value.nickname = userData.nickname || userData.first_name || ''
      mockUserData.value.remark = userData.notes || ''
      mockUserData.value.bio = userData.bio || ''
      mockUserData.value.avatar = userData.avatar ? `/static/${userData.avatar}` : ''
    }

    // 获取用户统计信息
    const statsResponse = await chatHistoryApi.getUserStats(user_id)
    if (statsResponse.data.err_code === 0) {
      const stats = statsResponse.data.payload
      mockUserData.value.messageCount = stats.total_messages || 0
      mockUserData.value.firstMessage = stats.first_message_time || ''
      mockUserData.value.lastMessage = stats.last_message_time || ''

      // 更新群组列表
      if (stats.groups && Array.isArray(stats.groups)) {
        mockUserData.value.groups = stats.groups.map((group: any) => ({
          id: group.chat_id,
          name: group.title || group.name,
          messageCount: group.message_count || 0,
          lastActiveTime: group.last_active_time || ''
        }))
      }
    }
  } catch (error) {
    console.error('加载用户信息失败:', error)
    ElMessage.error('加载用户信息失败')
  } finally {
    userDataLoading.value = false
  }
}

// 加载用户变动记录
const loadUserChangeRecords = async (user_id: string) => {
  if (!user_id) return

  changeRecordsLoading.value = true
  try {
    // 只获取最近几条记录作为预览（API已支持去重）
    const params = new URLSearchParams({
      page: '1',
      size: '5', // 只显示最近5条记录
      user_id: user_id
    })

    const response = await fetch(`/api/change_record/user?${params}`)
    const result = await response.json()

    if (result.err_code === 0) {
      // 将API数据转换为界面需要的格式
      mockChanges.value = (result.payload.items || []).map((item: any) => ({
        id: item.id,
        type: item.change_type_text,
        changeType: item.changed_fields,
        oldValue: formatChangeValue(item.original_value, item.changed_fields),
        newValue: formatChangeValue(item.new_value, item.changed_fields),
        originalValue: item.original_value || '',  // 保存变动前的原始路径用于头像显示
        newOriginalValue: item.new_value || '',  // 保存变动后的原始路径用于头像显示
        time: item.update_time
      }))
    } else {
      console.error('获取用户变动记录失败:', result.err_msg)
      mockChanges.value = []
    }
  } catch (error) {
    console.error('加载用户变动记录失败:', error)
    mockChanges.value = []
  } finally {
    changeRecordsLoading.value = false
  }
}

// 加载用户标签
const loadUserTags = async (user_id: string) => {
  if (!user_id) return

  tagsLoading.value = true
  try {
    // 首先获取所有标签列表以构建 tag_id -> tag_name 的映射
    let tagIdNameMap: Record<number, string> = {}
    try {
      const tagListResponse = await tagsApi.getList()
      if (tagListResponse.err_code === 0 && tagListResponse.payload.data) {
        tagIdNameMap = tagListResponse.payload.data.reduce((map: Record<number, string>, tag: any) => {
          map[tag.id] = tag.name
          return map
        }, {})
      }
    } catch (tagError) {
      console.warn('加载标签列表失败，将使用tag_id替代:', tagError)
    }

    const response = await tagsApi.getAutoTagLogs({
      user_id: user_id,
      page: 1,
      page_size: 20
    })

    if (response.err_code === 0) {
      const data = response.payload.data || []
      mockTags.value = data.map((item: any) => {
        // 根据来源类型提取原始文本
        let originalText = ''
        const info = item.detail_info || {}

        switch (item.source_type) {
          case 'chat':
            originalText = info.message_text || ''
            break
          case 'nickname':
            originalText = info.nickname || info.new_nickname || info.old_nickname || ''
            break
          case 'desc':
            originalText = info.desc || info.new_desc || info.old_desc || ''
            break
          default:
            originalText = ''
        }

        return {
          tagName: tagIdNameMap[item.tag_id] || `标签${item.tag_id}`,  // 使用真实标签名，如果没有则显示标签ID
          keyword: item.keyword || '',
          content: item.detail_info?.matched_text || item.detail_info?.message_text || '',
          originalText: originalText,  // 保存原始文本用于高亮
          createdAt: item.created_at || ''
        }
      })
    } else {
      console.error('获取用户标签失败:', response.err_msg)
      mockTags.value = []
    }
  } catch (error) {
    console.error('加载用户标签失败:', error)
    mockTags.value = []
  } finally {
    tagsLoading.value = false
  }
}

// 加载状态标志
const recentMessagesLoading = ref(false)

// 加载用户最近消息和图片
const loadUserRecentMessages = async (user_id: string) => {
  if (!user_id) {
    console.warn('用户ID为空，跳过加载最近消息')
    return
  }

  recentMessagesLoading.value = true
  console.log(`[加载最近消息] 开始加载用户 ${user_id} 的消息数据...`)

  try {
    const response = await chatHistoryApi.getUserRecentMessages(user_id)
    console.log('[加载最近消息] API 响应:', response.data)

    if (response.data.err_code === 0) {
      const payload = response.data.payload
      console.log('[加载最近消息] 收到的数据:', {
        recentMessagesCount: (payload.recent_messages || []).length,
        recentPhotosCount: (payload.recent_photos || []).length
      })

      // 更新最近消息
      mockRecentMessages.value = (payload.recent_messages || []).map((msg: any) => ({
        groupName: msg.group_name,
        content: msg.content,
        time: msg.time
      }))

      console.log(`[加载最近消息] 已加载 ${mockRecentMessages.value.length} 条消息`)

      // 更新最近图片
      const photos = (payload.recent_photos || [])
        .filter((photo: any) => {
          return photo.type !== 'video_thumbnail' && photo.path
        })
        .slice(0, 10)
        .map((photo: any) => ({
          path: photo.path,
          type: photo.type,
          message_id: photo.message_id
        }))

      mockPhotos.value = photos
      console.log(`[加载最近消息] 已加载 ${photos.length} 张图片`)
    } else {
      console.error('[加载最近消息] 获取用户最近消息失败:', response.data.err_msg)
      mockRecentMessages.value = []
      mockPhotos.value = []
    }
  } catch (error) {
    console.error('[加载最近消息] 加载用户最近消息异常:', error)
    mockRecentMessages.value = []
    mockPhotos.value = []
  } finally {
    recentMessagesLoading.value = false
    console.log('[加载最近消息] 加载完成')
  }
}

// 格式化变动值
const formatChangeValue = (value: string, changeType: number): string => {
  if (!value) return '(空)'

  // 如果是头像变动，显示简化的文件名
  if (changeType === 3) {
    if (value.includes('/')) {
      const parts = value.split('/')
      return parts[parts.length - 1] || value
    }
  }

  return value
}

// 格式化头像URL
const formatAvatarUrl = (avatar: string): string => {
  if (!avatar) return ''
  if (avatar.startsWith('http')) return avatar
  return `/static/${avatar}`
}

// 监听选中节点变化，加载用户数据
watch(selectedNode, (newNode) => {
  if (newNode && newNode.type === 'resource') {
    // 从节点ID中提取tg_user_id (格式: profile_123)
    const tgUserId = (newNode as any).tg_user_id
    if (tgUserId) {
      loadUserBasicInfo(tgUserId)
      loadUserChangeRecords(tgUserId)
      loadUserTags(tgUserId)
      loadUserRecentMessages(tgUserId)
    }
  }
})

// 组件挂载时加载数据
onMounted(() => {
  loadFolderTree()
})

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

// 最近消息 - 加载时为空
const mockRecentMessages = ref<Array<{
  groupName: string
  content: string
  time: string
}>>([])

// 占位符数据 - 最近图片 (加载时为空，由API填充)
const mockPhotos = ref<Array<{
  path: string
  type: string
  message_id: string
}>>([])

// 占位符数据 - 面板2: 信息变动
const mockChanges = ref<ChangeRecord[]>([
  {
    id: '1',
    type: '用户名变更',
    changeType: 2,
    oldValue: 'john_old',
    newValue: 'john_doe',
    originalValue: 'john_old',
    newOriginalValue: 'john_doe',
    time: '2025-01-10 14:30'
  },
  {
    id: '2',
    type: '个人简介更新',
    changeType: 4,
    oldValue: '化工从业者',
    newValue: '化工行业从业者,专注于有机化学领域',
    originalValue: '化工从业者',
    newOriginalValue: '化工行业从业者,专注于有机化学领域',
    time: '2025-01-08 09:15'
  },
  {
    id: '3',
    type: '头像更换',
    changeType: 3,
    oldValue: '默认头像',
    newValue: '自定义头像',
    originalValue: '',
    newOriginalValue: '',
    time: '2025-01-05 16:20'
  },
  {
    id: '4',
    type: '电话号码更新',
    changeType: 1,
    oldValue: '+86 139****1234',
    newValue: '+86 138****5678',
    originalValue: '+86 139****1234',
    newOriginalValue: '+86 138****5678',
    time: '2025-01-03 11:45'
  },
  {
    id: '5',
    type: '备注名称修改',
    changeType: 1,
    oldValue: '普通联系人',
    newValue: '重要联系人',
    originalValue: '普通联系人',
    newOriginalValue: '重要联系人',
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

// 跳转到用户在指定群组的消息记录
const navigateToGroupMessages = (group: GroupInfo) => {
  if (!mockUserData.value.userId || !group.id) {
    ElMessage.warning('缺少必要的群组或用户信息')
    return
  }

  router.push({
    path: '/chat-history',
    query: {
      group_id: group.id,
      user_id: mockUserData.value.userId,
      search_type: 'user_id'
    }
  })
}

// 图片预览状态
const imagePreviewVisible = ref(false)
const currentImageIndex = ref(-1)

// 打开图片预览
const openImagePreview = (index: number) => {
  currentImageIndex.value = index
  imagePreviewVisible.value = true
}

// 上一张
const previousImage = () => {
  if (currentImageIndex.value > 0) {
    currentImageIndex.value--
  }
}

// 下一张
const nextImage = () => {
  if (currentImageIndex.value < mockPhotos.value.length - 1) {
    currentImageIndex.value++
  }
}

// 图片加载错误处理
const handleImageError = (e: Event) => {
  const img = e.target as HTMLImageElement
  img.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iODAiIGhlaWdodD0iODAiIHZpZXdCb3g9IjAgMCA4MCA4MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iODAiIGhlaWdodD0iODAiIGZpbGw9IiNGNUY3RkEiLz48Y2lyY2xlIGN4PSI0MCIgY3k9IjQwIiByPSIzIiBmaWxsPSIjQ0NBQUQ4Ii8+PC9zdmc+'
}

// ==================== 档案状态相关函数 ====================

/**
 * 获取状态标签的中文显示名称
 */
const getStatusLabel = (status: string): string => {
  const statusMap: Record<string, string> = {
    'draft': '草稿',
    'generated': '已生成',
    'archived': '已归档'
  }
  return statusMap[status] || status
}

/**
 * 获取状态对应的标签类型（用于Element Plus Tag组件）
 */
const getStatusTagType = (status: string): 'success' | 'primary' | 'warning' | 'info' | 'danger' => {
  const typeMap: Record<string, 'success' | 'primary' | 'warning' | 'info' | 'danger'> = {
    'draft': 'info',        // 灰色 - 草稿
    'generated': 'success', // 绿色 - 已生成
    'archived': 'warning'   // 橙色 - 已归档
  }
  return typeMap[status] || 'info'
}

/**
 * 获取状态对应的图标组件
 */
const getStatusIcon = (status: string) => {
  const iconMap: Record<string, any> = {
    'draft': DocumentCopy,      // 文档副本图标 - 草稿
    'generated': CircleCheck,   // 圆形检查图标 - 已生成
    'archived': FolderDelete    // 删除文件夹图标 - 已归档
  }
  return iconMap[status] || DocumentCopy
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
        width: 100%;
        justify-content: space-between;

        .el-icon {
          font-size: 16px;
        }

        .node-label {
          flex: 1;
        }

        .status-badge {
          margin-left: 8px;
          flex-shrink: 0;
          :deep(.el-tag__content) {
            display: flex;
            align-items: center;
            gap: 2px;
          }
        }

        .node-actions {
          display: none;
          margin-left: 8px;

          :deep(.el-button-group) {
            display: flex;
            gap: 4px;

            .el-button {
              padding: 0 4px;
              height: 24px;
              line-height: 24px;
              font-size: 12px;

              .el-icon {
                font-size: 12px;
              }
            }
          }
        }

        &:hover .node-actions {
          display: flex;
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
          gap: 16px;

          .profile-title-section {
            display: flex;
            align-items: center;
            gap: 12px;
            flex: 1;

            h2 {
              margin: 0;
              font-size: 24px;
              font-weight: 600;
              color: #303133;
            }

            .header-status-badge {
              display: flex;
              align-items: center;
              padding: 6px 12px;
              border-radius: 4px;
              font-size: 14px;
              font-weight: 500;
              white-space: nowrap;
              flex-shrink: 0;

              .el-icon {
                font-size: 16px;
              }

              &:deep(.el-tag__content) {
                display: flex;
                align-items: center;
                gap: 6px;
              }
            }
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
                  gap: 8px;

                  // 昵称行 - 大字体,备注灰色括号
                  .nickname-row {
                    display: flex;
                    align-items: baseline;
                    gap: 6px;

                    .nickname-text {
                      font-size: 20px;
                      font-weight: 600;
                      color: #303133;
                      line-height: 1.2;
                    }

                    .remark-text {
                      font-size: 14px;
                      color: #909399;
                      font-weight: 400;
                    }
                  }

                  // 用户名行 - 蓝色等宽字体
                  .username-row {
                    .username-text {
                      font-size: 14px;
                      font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                      color: #409eff;
                      font-weight: 500;
                    }
                  }

                  // 用户ID行
                  .userid-row {
                    .userid-text {
                      font-size: 14px;
                      color: #606266;
                      font-weight: 500;
                    }
                  }

                  // 个人简介
                  .bio-row {
                    margin-top: 4px;
                    padding: 8px 12px;
                    background-color: #f5f7fa;
                    border-radius: 4px;
                    border-left: 3px solid #409eff;

                    .bio-text {
                      font-size: 13px;
                      color: #606266;
                      line-height: 1.5;
                      display: -webkit-box;
                      -webkit-line-clamp: 3;
                      -webkit-box-orient: vertical;
                      overflow: hidden;
                    }
                  }

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

                  // 头像变动样式
                  .avatar-change-values {
                    display: flex;
                    align-items: center;
                    gap: 12px;

                    .avatar-change-item {
                      display: flex;
                      flex-direction: column;
                      align-items: center;
                      gap: 8px;
                      flex: 1;

                      .change-label-text {
                        font-size: 11px;
                        color: #909399;
                        font-weight: 500;
                      }

                      .empty-avatar-box {
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        width: 40px;
                        height: 40px;
                        background-color: #f5f5f5;
                        border: 1px dashed #d9d9d9;
                        border-radius: 4px;
                        font-size: 10px;
                        color: #999;
                        text-align: center;
                      }

                      .change-avatar-img {
                        flex-shrink: 0;
                        border: 1px solid #e4e7ed;
                      }
                    }

                    .arrow-icon {
                      align-self: flex-end;
                      margin-bottom: 20px;
                    }
                  }
                }
              }

              // 最近消息和图片展示
              .photo-gallery {
                margin-top: 16px;
                padding-top: 16px;
                border-top: 1px solid #e4e7ed;

                .image-row {
                  display: flex;
                  gap: 8px;
                  overflow-x: auto;
                  padding-bottom: 8px;

                  .image-item-wrapper {
                    flex-shrink: 0;
                    width: 80px;
                    height: 80px;
                    border-radius: 8px;
                    overflow: hidden;
                    background-color: #f5f7fa;

                    .message-image {
                      width: 100%;
                      height: 100%;
                      object-fit: cover;
                      cursor: pointer;
                      transition: all 0.3s ease;
                      display: block;

                      &:hover {
                        transform: scale(1.05);
                        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                      }
                    }
                  }
                }

                .photo-empty {
                  display: flex;
                  flex-direction: column;
                  align-items: center;
                  justify-content: center;
                  height: 80px;
                  background-color: #f5f7fa;
                  border: 1px dashed #d9d9d9;
                  border-radius: 8px;
                  color: #c0c4cc;

                  p {
                    margin: 0;
                    font-size: 12px;
                    margin-top: 8px;
                  }
                }
              }

              // 图片预览对话框样式
              :deep(.image-preview-container) {
                width: 100%;
                padding: 20px;

                .preview-content {
                  display: flex;
                  flex-direction: column;
                  align-items: center;
                  gap: 16px;

                  .preview-image {
                    max-width: 100%;
                    max-height: 60vh;
                    object-fit: contain;
                  }

                  .preview-nav {
                    display: flex;
                    align-items: center;
                    gap: 16px;
                    justify-content: center;

                    .nav-btn {
                      padding: 8px 12px;
                      border: 1px solid #dcdfe6;
                      background: white;
                      border-radius: 4px;
                      cursor: pointer;
                      transition: all 0.3s ease;
                      display: flex;
                      align-items: center;
                      justify-content: center;

                      &:hover:not(:disabled) {
                        color: #409eff;
                        border-color: #409eff;
                      }

                      &:disabled {
                        opacity: 0.5;
                        cursor: not-allowed;
                      }
                    }

                    .preview-counter {
                      font-size: 14px;
                      color: #606266;
                      min-width: 50px;
                      text-align: center;
                    }
                  }
                }
              }

              :deep(.el-dialog) {
                .el-dialog__header {
                  border-bottom: 1px solid #ebeef5;
                  padding: 16px 20px;
                }

                .el-dialog__body {
                  padding: 0;
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

              :deep(.keyword-highlight) {
                background-color: #FFF3CD;
                color: #856404;
                font-weight: bold;
                padding: 2px 4px;
                border-radius: 2px;
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
