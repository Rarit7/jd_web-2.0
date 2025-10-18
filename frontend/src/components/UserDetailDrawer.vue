<template>
  <el-drawer
    v-model="isVisible"
    title="用户详情"
    direction="rtl"
    size="400px"
  >
    <!-- 用户不存在时的空状态 -->
    <div v-if="userNotFound && !userDetailLoading" class="user-not-found">
      <el-empty
        description="该用户可能已经注销或者退群"
        :image-size="120"
      >
        <template #description>
          <p class="empty-title">该用户可能已经注销或者退群</p>
          <p class="empty-subtitle" v-if="attemptedUserId">User ID: {{ attemptedUserId }}</p>
        </template>
      </el-empty>
    </div>

    <div v-if="currentUserDetail" class="user-detail-drawer" v-loading="userDetailLoading">
      <!-- 用户头像和基本信息 -->
      <div class="user-basic-info">
        <div class="user-avatar-large">
          <el-avatar :size="80" :src="currentUserDetail.avatar" shape="square">
            <span>{{ currentUserDetail.senderName.charAt(0) }}</span>
          </el-avatar>
        </div>
        <div class="user-name-info">
          <h3 class="user-name" :class="{ 'key-focus': currentUserDetail.is_key_focus }">
            {{ currentUserDetail.senderName }}
          </h3>
          <p class="user-id">ID: {{ currentUserDetail.user_id }}</p>
          <p class="username" v-if="currentUserDetail.username">
            @{{ currentUserDetail.username }}
          </p>
        </div>
      </div>

      <!-- 占位符内容 -->
      <div class="placeholder-sections">
        <div class="section">
          <h4>个人信息</h4>
          <div class="placeholder-item">
            <span class="label">备注:</span>
            <div class="remark-container">
              <span v-if="!editingRemark" class="value remark-display" @click="startEditRemark">
                {{ localRemark || '点击添加备注' }}
              </span>
              <div v-if="editingRemark" class="remark-edit">
                <el-input
                  v-model="tempRemark"
                  size="small"
                  placeholder="请输入备注"
                  @blur="saveRemark"
                  @keyup.enter="saveRemark"
                  @keyup.escape="cancelEditRemark"
                  ref="remarkInput"
                />
              </div>
              <el-button 
                v-if="!editingRemark"
                type="text" 
                size="small" 
                @click="startEditRemark"
                class="edit-btn"
              >
                <el-icon><Edit /></el-icon>
              </el-button>
            </div>
          </div>
          <div class="placeholder-item bio-item">
            <span class="label">个人简介:</span>
            <div class="bio-content">
              <div v-if="localUserBio || currentUserDetail.bio" class="bio-text">
                {{ localUserBio || currentUserDetail.bio }}
              </div>
              <div v-else class="bio-empty">
                暂无个人简介
              </div>
            </div>
          </div>
          
          <!-- 重点关注开关 -->
          <div class="placeholder-item focus-switch-item">
            <span class="label">重点关注:</span>
            <div class="focus-switch-container">
              <el-switch
                v-model="localKeyFocus"
                @change="handleFocusToggle"
                :loading="focusLoading"
                active-color="#f56c6c"
                inactive-color="#dcdfe6"
                size="default"
              />
            </div>
          </div>

          <!-- 创建全息档案按钮 -->
          <div class="placeholder-item holistic-profile-item">
            <el-button
              v-if="!profileExists"
              type="primary"
              size="small"
              @click="handleCreateHolisticProfile"
              :loading="profileCreating"
              class="holistic-profile-btn"
            >
              <el-icon><Plus /></el-icon>
              创建全息档案
            </el-button>
            <el-button
              v-else
              type="success"
              disabled
              size="small"
              class="holistic-profile-btn"
            >
              <el-icon><SuccessFilled /></el-icon>
              已创建全息档案
            </el-button>
          </div>
        </div>

        <div class="section">
          <h4>聊天统计</h4>
          <div v-loading="statsLoading" class="stats-content">
            <div class="placeholder-item">
              <span class="label">消息总数:</span>
              <span class="value">{{ userStats.totalMessages || 0 }}</span>
            </div>
            <div class="placeholder-item">
              <span class="label">首次发言:</span>
              <span class="value">{{ formatDate(userStats.firstMessageTime) || '暂无数据' }}</span>
            </div>
            <div class="placeholder-item">
              <span class="label">最后发言:</span>
              <span class="value">{{ formatDate(userStats.lastMessageTime) || '暂无数据' }}</span>
            </div>
          </div>
        </div>

        <div class="section">
          <h4>标签管理</h4>
          <div class="tags-content">
            <div class="user-tags">
              <el-tag
                v-for="tag in userTags"
                :key="tag.id"
                closable
                @close="removeTag(tag)"
                class="tag-item"
                :color="tag.color"
                effect="dark"
                style="color: white; border: none;"
              >
                {{ tag.name }}
              </el-tag>
              <el-button 
                size="small" 
                type="primary" 
                plain
                @click="showAddTagDialog"
                class="add-tag-btn"
              >
                <el-icon><Plus /></el-icon>
                添加标签
              </el-button>
            </div>
          </div>
        </div>

        <div class="section">
          <h4>信息变动历史</h4>
          <div v-loading="changeRecordsLoading" class="change-records-content">
            <div v-if="userChangeRecords.length === 0 && !changeRecordsLoading" class="empty-records">
              暂无变动记录
            </div>
            <div v-else class="change-records-list">
              <div
                v-for="record in userChangeRecords"
                :key="record.id"
                class="change-record-item"
              >
                <div class="change-header">
                  <span class="change-type">{{ getChangeTypeText(record.changed_fields) }}</span>
                  <span class="change-time">{{ formatDate(record.update_time) }}</span>
                </div>
                <div class="change-content">
                  <div class="change-before-after">
                    <div v-if="record.changed_fields === 3" class="avatar-change">
                      <div class="change-item">
                        <span class="change-label">变动前:</span>
                        <div v-if="!record.original_value" class="empty-avatar">无头像</div>
                        <el-avatar
                          v-else
                          :size="32"
                          :src="formatAvatarUrl(record.original_value)"
                          shape="square"
                          class="change-avatar"
                        />
                      </div>
                      <div class="change-item">
                        <span class="change-label">变动后:</span>
                        <div v-if="!record.new_value" class="empty-avatar">无头像</div>
                        <el-avatar
                          v-else
                          :size="32"
                          :src="formatAvatarUrl(record.new_value)"
                          shape="square"
                          class="change-avatar"
                        />
                      </div>
                    </div>
                    <div v-else class="text-change">
                      <div class="change-item">
                        <span class="change-label">变动前:</span>
                        <span class="change-value before" :class="{ 'username-value': record.changed_fields === 2 }">
                          <span v-if="record.changed_fields === 2">@</span>{{ record.original_value || '(空)' }}
                        </span>
                      </div>
                      <div class="change-item">
                        <span class="change-label">变动后:</span>
                        <span class="change-value after" :class="{ 'username-value': record.changed_fields === 2 }">
                          <span v-if="record.changed_fields === 2">@</span>{{ record.new_value || '(空)' }}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 查看更多按钮 -->
            <div v-if="userChangeRecords.length > 0" class="view-more-container">
              <el-button
                type="text"
                size="small"
                @click="navigateToChangeRecord"
                class="view-more-btn"
              >
                查看完整历史 <el-icon><ArrowRight /></el-icon>
              </el-button>
            </div>
          </div>
        </div>

        <div class="section">
          <h4>所在群组</h4>
          <div v-loading="groupsLoading" class="groups-content">
            <div v-if="userGroups.length === 0 && !groupsLoading" class="empty-groups">
              暂无群组数据
            </div>
            <div v-else class="group-list">
              <div 
                v-for="group in userGroups" 
                :key="group.chat_id"
                class="group-item"
                @click="navigateToUserMessages(group)"
              >
                <div class="group-info">
                  <div class="group-name">{{ group.title || group.name }}</div>
                  <div class="group-meta">
                    <span class="message-count">{{ group.messageCount || 0 }}条消息</span>
                    <span class="last-active">最后活跃: {{ formatDate(group.lastActiveTime) }}</span>
                  </div>
                </div>
                <el-icon class="group-arrow">
                  <ArrowRight />
                </el-icon>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 添加标签对话框 -->
    <el-dialog
      v-model="showTagDialog"
      title="选择标签"
      width="500px"
      append-to-body
    >
      <div class="tag-selection-content">
        <div class="available-tags-section">
          <h4>可选标签：</h4>
          <div v-loading="availableTagsLoading" class="available-tags">
            <div v-if="availableTags.length === 0 && !availableTagsLoading" class="empty-tags">
              暂无可选标签
            </div>
            <div v-else class="tag-grid">
              <el-tag
                v-for="tag in availableTags"
                :key="tag.id"
                :color="tag.color"
                effect="dark"
                style="color: white; border: none; cursor: pointer; margin: 4px;"
                @click="addTagToUser(tag)"
                class="selectable-tag"
              >
                {{ tag.name }}
              </el-tag>
            </div>
          </div>
        </div>

        <div class="selected-tags-section" v-if="userTags.length > 0">
          <h4>已选标签：</h4>
          <div class="selected-tags">
            <el-tag
              v-for="tag in userTags"
              :key="tag.id"
              :color="tag.color"
              effect="dark"
              style="color: white; border: none; margin: 4px;"
              closable
              @close="removeTag(tag)"
            >
              {{ tag.name }}
            </el-tag>
          </div>
        </div>
      </div>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showTagDialog = false">关闭</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 创建全息档案对话框 -->
    <el-dialog
      v-model="createProfileDialogVisible"
      title="创建全息档案"
      width="500px"
      @close="resetCreateProfileForm"
      append-to-body
    >
      <el-form
        ref="createProfileFormRef"
        :model="createProfileForm"
        :rules="createProfileRules"
        label-width="100px"
        @submit.prevent
      >
        <el-form-item label="档案标题" prop="profile_name">
          <el-input
            v-model="createProfileForm.profile_name"
            placeholder="请输入档案标题"
            clearable
          />
        </el-form-item>

        <el-form-item label="所属目录" prop="folder_id">
          <el-tree-select
            v-model="createProfileForm.folder_id"
            :data="folderOnlyData"
            :props="treeSelectorProps"
            clearable
            placeholder="选择所属目录（可选）"
          />
        </el-form-item>

        <el-form-item label="档案状态" prop="status">
          <el-select
            v-model="createProfileForm.status"
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
          <el-button @click="createProfileDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSaveHolisticProfile" :loading="profileCreating">
            创建档案
          </el-button>
        </span>
      </template>
    </el-dialog>
  </el-drawer>
</template>

<script setup lang="ts">
import { computed, ref, watch, nextTick } from 'vue'
import { Edit, Plus, ArrowRight, SuccessFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { chatHistoryApi } from '@/api/chat-history'
import { tgUsersApi } from '@/api/tg-users'
import { tagsApi, type Tag as TagType } from '@/api/tags'
import { userProfileApi, profileFolderApi, type FolderTreeNode } from '@/api/user-profile'
import { useUserStore } from '@/store/modules/user'

// 定义用户信息接口
interface UserInfo {
  id: number
  senderName: string
  nickname: string
  username: string
  user_id: string
  avatar: string
  is_key_focus?: boolean
  bio?: string
  remark?: string
}

// 定义用户统计信息接口
interface UserStats {
  totalMessages: number
  firstMessageTime: string
  lastMessageTime: string
}

// 使用标签库的标签接口
type Tag = TagType

// 定义群组信息接口
interface UserGroup {
  chat_id: string
  title: string
  name: string
  messageCount: number
  lastActiveTime: string
}

// 定义组件props - 支持两种模式：完整用户信息或仅user_id
interface Props {
  visible: boolean
  userDetail?: UserInfo | null  // 可选：完整用户信息
  userId?: string              // 可选：仅用户ID，组件自己加载详细信息
  currentGroupId?: string
}

// 定义emits
interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'navigate-to-user-messages', data: { groupId: string, userId: string }): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const router = useRouter()
const userStore = useUserStore()

// 响应式数据
const editingRemark = ref(false)
const tempRemark = ref('')
const localRemark = ref('')
const remarkInput = ref()

// 全息档案相关
const profileExists = ref(false)
const profileCreating = ref(false)
const createProfileDialogVisible = ref(false)

interface CreateProfileForm {
  profile_name: string
  folder_id: number | null
  status: 'draft' | 'generated' | 'archived'
}

const createProfileForm = ref<CreateProfileForm>({
  profile_name: '',
  folder_id: null,
  status: 'draft'
})
const createProfileFormRef = ref()

// 文件夹树数据
const folderTreeData = ref<FolderTreeNode[]>([])

// 表单验证规则
const createProfileRules = {
  profile_name: [
    { required: true, message: '请输入档案标题', trigger: 'blur' },
    { min: 1, max: 200, message: '档案标题长度在 1 到 200 个字符之间', trigger: 'blur' }
  ]
}

// 树形选择器配置
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

  return filterFolders(folderTreeData.value)
})

const showTagDialog = ref(false)
const userTags = ref<Tag[]>([])
const availableTags = ref<Tag[]>([])
const availableTagsLoading = ref(false)

const statsLoading = ref(false)
const focusLoading = ref(false)
const localKeyFocus = ref(false)
const userStats = ref<UserStats>({
  totalMessages: 0,
  firstMessageTime: '',
  lastMessageTime: ''
})

const groupsLoading = ref(false)
const userGroups = ref<UserGroup[]>([])

// 本地维护用户信息，确保响应式更新
const localUserBio = ref('')
const localUserDetail = ref<UserInfo | null>(null)
const userDetailLoading = ref(false)

// 用户未找到状态
const userNotFound = ref(false)
const attemptedUserId = ref('')

// 变动记录相关数据
const userChangeRecords = ref<any[]>([])
const changeRecordsLoading = ref(false)

// 双向绑定visible属性
const isVisible = computed({
  get: () => props.visible,
  set: (value: boolean) => emit('update:visible', value)
})

// 计算当前有效的用户详情
const currentUserDetail = computed(() => {
  return localUserDetail.value || props.userDetail
})

// 监听props变化，加载用户数据
watch([() => props.userDetail, () => props.userId, () => props.visible],
  async ([newUserDetail, newUserId, visible]) => {
    if (!visible) return

    // 重置状态
    userNotFound.value = false
    attemptedUserId.value = ''

    if (newUserDetail) {
      // 模式1：已提供完整用户信息
      console.log('使用提供的用户详情:', newUserDetail)
      localUserDetail.value = newUserDetail
      localRemark.value = newUserDetail.remark || ''
      localKeyFocus.value = newUserDetail.is_key_focus || false
      localUserBio.value = newUserDetail.bio || ''

      // 如果没有bio，尝试加载完整信息
      if (!newUserDetail.bio && newUserDetail.user_id) {
        await loadCompleteUserInfo(newUserDetail.user_id)
      }
    } else if (newUserId) {
      // 模式2：仅提供user_id，需要加载完整信息
      console.log('仅提供user_id，加载完整信息:', newUserId)
      attemptedUserId.value = newUserId
      await loadCompleteUserInfo(newUserId)
    } else {
      localUserDetail.value = null
      return
    }
    
    // 加载相关数据
    if (currentUserDetail.value) {
      loadUserStats()
      loadUserTags()
      loadUserGroups()
      loadUserChangeRecords(currentUserDetail.value.user_id)
      checkProfileExists(currentUserDetail.value.user_id)
    }
  },
  { immediate: true }
)

// 格式化日期
const formatDate = (dateString: string): string => {
  if (!dateString) return ''
  try {
    const date = new Date(dateString)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch (e) {
    return dateString
  }
}

// 备注编辑相关方法
const startEditRemark = async () => {
  editingRemark.value = true
  tempRemark.value = localRemark.value
  await nextTick()
  remarkInput.value?.focus()
}

const saveRemark = async () => {
  const userDetail = currentUserDetail.value
  if (!userDetail) return
  
  try {
    // 获取当前用户标签ID列表
    const tagIds = userTags.value.map(t => t.id).join(',')
    
    // 调用API保存备注和标签
    await tgUsersApi.updateUser({
      tg_user_id: userDetail.id,
      tag_id_list: tagIds,
      remark: tempRemark.value
    })
    
    localRemark.value = tempRemark.value
    editingRemark.value = false
    ElMessage.success('备注保存成功')
  } catch (error) {
    console.error('保存备注失败:', error)
    ElMessage.error('备注保存失败')
  }
}

const cancelEditRemark = () => {
  editingRemark.value = false
  tempRemark.value = ''
}

// 处理重点关注开关
const handleFocusToggle = async (value: string | number | boolean) => {
  const userDetail = currentUserDetail.value
  if (!userDetail) return

  focusLoading.value = true
  try {
    // 调用API更新重点关注状态
    const response = await tgUsersApi.toggleFocus(userDetail.id)

    if (response.data.err_code === 0) {
      // 更新本地状态
      localKeyFocus.value = response.data.payload.is_key_focus
      if (localUserDetail.value) {
        localUserDetail.value.is_key_focus = response.data.payload.is_key_focus
      }
      ElMessage.success(response.data.payload.message)
    } else {
      // 如果失败，恢复先前的状态
      localKeyFocus.value = typeof value === 'boolean' ? !value : false
      ElMessage.error(response.data.err_msg || '操作失败')
    }
  } catch (error) {
    console.error('更新重点关注状态失败:', error)
    // 如果失败，恢复先前的状态
    localKeyFocus.value = typeof value === 'boolean' ? !value : false
    ElMessage.error('操作失败')
  } finally {
    focusLoading.value = false
  }
}

// 标签管理相关方法
const showAddTagDialog = async () => {
  showTagDialog.value = true
  await loadAvailableTags()
}

// 加载可选标签（排除已选择的标签）
const loadAvailableTags = async () => {
  availableTagsLoading.value = true
  try {
    const response = await tagsApi.getList()
    if (response.err_code === 0) {
      // 过滤掉已选择的标签
      availableTags.value = response.payload.data.filter(tag => 
        !userTags.value.some(userTag => userTag.id === tag.id)
      )
    } else {
      ElMessage.error('获取标签列表失败')
    }
  } catch (error) {
    console.error('加载可选标签失败:', error)
    ElMessage.error('加载可选标签失败')
  } finally {
    availableTagsLoading.value = false
  }
}

// 添加标签给用户
const addTagToUser = async (tag: Tag) => {
  const userDetail = currentUserDetail.value
  if (!userDetail) return
  
  try {
    // 获取当前用户所有标签ID
    const currentTagIds = userTags.value.map(t => t.id)
    const newTagIds = [...currentTagIds, tag.id]
    
    // 调用API更新用户标签
    await tgUsersApi.updateUser({
      tg_user_id: userDetail.id,
      tag_id_list: newTagIds.join(','),
      remark: localRemark.value || ''
    })
    
    // 更新本地标签列表
    userTags.value.push(tag)
    // 从可选标签中移除
    const index = availableTags.value.findIndex(t => t.id === tag.id)
    if (index > -1) {
      availableTags.value.splice(index, 1)
    }
    
    ElMessage.success('标签添加成功')
  } catch (error) {
    console.error('添加标签失败:', error)
    ElMessage.error('添加标签失败')
  }
}

// 从用户删除标签
const removeTag = async (tag: Tag) => {
  const userDetail = currentUserDetail.value
  if (!userDetail) return
  
  try {
    // 获取删除该标签后的标签ID列表
    const remainingTagIds = userTags.value
      .filter(t => t.id !== tag.id)
      .map(t => t.id)
    
    // 调用API更新用户标签
    await tgUsersApi.updateUser({
      tg_user_id: userDetail.id,
      tag_id_list: remainingTagIds.join(','),
      remark: localRemark.value || ''
    })
    
    // 更新本地标签列表
    const index = userTags.value.findIndex(t => t.id === tag.id)
    if (index > -1) {
      userTags.value.splice(index, 1)
    }
    
    // 如果对话框打开，将标签添加回可选列表
    if (showTagDialog.value) {
      availableTags.value.push(tag)
      // 按名称排序
      availableTags.value.sort((a, b) => a.name.localeCompare(b.name))
    }
    
    ElMessage.success('标签删除成功')
  } catch (error) {
    console.error('删除标签失败:', error)
    ElMessage.error('删除标签失败')
  }
}

// 加载用户统计数据
const loadUserStats = async () => {
  const userDetail = currentUserDetail.value
  if (!userDetail) return
  
  statsLoading.value = true
  try {
    const response = await chatHistoryApi.getUserStats(userDetail.user_id)
    
    if (response.data.err_code === 0) {
      const stats = response.data.payload
      userStats.value = {
        totalMessages: stats.total_messages || 0,
        firstMessageTime: stats.first_message_time || '',
        lastMessageTime: stats.last_message_time || ''
      }
    } else {
      console.error('获取用户统计数据失败:', response.data.err_msg)
      ElMessage.error(response.data.err_msg || '获取用户统计数据失败')
    }
  } catch (error) {
    console.error('加载用户统计数据失败:', error)
    ElMessage.error('加载用户统计数据失败')
  } finally {
    statsLoading.value = false
  }
}

// 加载用户标签
const loadUserTags = async () => {
  const userDetail = currentUserDetail.value
  if (!userDetail) return

  try {
    // 使用user_id获取完整的用户信息，包括标签
    if (userDetail.user_id) {
      const response = await tgUsersApi.getUserByUserId(userDetail.user_id)

      if (response.data.err_code === 0) {
        const userData = response.data.payload

        // 如果用户有标签
        if (userData.tag_id_list) {
          // 获取标签库中的所有标签
          const tagsResponse = await tagsApi.getList()
          if (tagsResponse.err_code === 0) {
            // 解析标签ID列表
            const tagIds = userData.tag_id_list
              .split(',')
              .map((id: string) => parseInt(id.trim()))
              .filter((id: number) => !isNaN(id))

            // 过滤出用户拥有的标签
            userTags.value = tagsResponse.payload.data.filter(tag => tagIds.includes(tag.id))
            console.log(`✅ 成功加载用户标签: ${userTags.value.length} 个`)
          }
        } else {
          // 用户没有标签
          userTags.value = []
          console.log('ℹ️ 用户暂无标签')
        }
      } else {
        console.error('获取用户信息失败:', response.data.err_msg)
        userTags.value = []
      }
    }
  } catch (error) {
    console.error('加载用户标签失败:', error)
    userTags.value = []
  }
}

// 加载用户所在群组
const loadUserGroups = async () => {
  const userDetail = currentUserDetail.value
  if (!userDetail) return
  
  groupsLoading.value = true
  try {
    const response = await chatHistoryApi.getUserStats(userDetail.user_id)
    
    if (response.data.err_code === 0) {
      const stats = response.data.payload
      userGroups.value = (stats.groups || []).map((group: any) => ({
        chat_id: group.chat_id,
        title: group.title || group.name,
        name: group.name,
        messageCount: group.message_count || 0,
        lastActiveTime: group.last_active_time || ''
      }))
    } else {
      console.error('获取用户群组数据失败:', response.data.err_msg)
    }
  } catch (error) {
    console.error('加载用户群组失败:', error)
  } finally {
    groupsLoading.value = false
  }
}

// 获取用户信息变动记录
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
      userChangeRecords.value = result.payload.items || []
    } else {
      console.error('获取用户变动记录失败:', result.err_msg)
      userChangeRecords.value = []
    }
  } catch (error) {
    console.error('加载用户变动记录失败:', error)
    userChangeRecords.value = []
  } finally {
    changeRecordsLoading.value = false
  }
}

// 变动类型映射
const getChangeTypeText = (changeType: number): string => {
  const typeMap: Record<number, string> = {
    1: '显示名称',
    2: '用户名',
    3: '头像',
    4: '个人简介'
  }
  return typeMap[changeType] || '未知'
}

// 格式化头像URL
const formatAvatarUrl = (avatar: string): string => {
  if (!avatar) return ''
  if (avatar.startsWith('http')) return avatar
  return `/static/${avatar}`
}

// 导航到变动记录页面
const navigateToChangeRecord = () => {
  const user_id = currentUserDetail.value?.user_id
  if (user_id) {
    router.push({
      path: '/change_record',
      query: { user_id }
    })
  }
}

// 加载完整用户信息的统一函数
const loadCompleteUserInfo = async (user_id: string) => {
  if (!user_id) {
    console.log('loadCompleteUserInfo: user_id 为空')
    return
  }
  
  userDetailLoading.value = true
  console.log('loadCompleteUserInfo 开始加载:', user_id)
  
  try {
    const response = await tgUsersApi.getUserByUserId(user_id)
    console.log('API响应:', response.data)
    
    if (response.data.err_code === 0) {
      const userData = response.data.payload
      console.log('找到用户数据:', userData)

      // 构建标准的UserInfo对象
      const userInfo: UserInfo = {
        id: userData.id,
        senderName: userData.nickname || userData.first_name || userData.username || `用户${userData.user_id}`,
        nickname: userData.nickname || '',
        username: userData.username || '',
        user_id: userData.user_id,
        avatar: userData.avatar ? `/static/${userData.avatar}` : '',
        is_key_focus: userData.is_key_focus || false,
        bio: userData.bio || '',
        remark: userData.notes || ''
      }

      // 更新本地状态
      localUserDetail.value = userInfo
      localUserBio.value = userInfo.bio || ''
      localRemark.value = userInfo.remark || ''
      localKeyFocus.value = userInfo.is_key_focus || false

      console.log(`✅ 成功获取用户 ${user_id} 的完整信息`)
    } else {
      console.log(`❌ 未找到用户 ${user_id}:`, response.data.err_msg)
      // 设置用户未找到状态
      userNotFound.value = true
      localUserDetail.value = null
    }
  } catch (error) {
    console.error('加载用户完整信息失败:', error)
    // 网络错误等情况也标记为未找到
    userNotFound.value = true
    localUserDetail.value = null
  } finally {
    userDetailLoading.value = false
  }
}

// 导航到用户在指定群组的消息记录
const navigateToUserMessages = (group: UserGroup) => {
  const userDetail = currentUserDetail.value
  if (!userDetail) return

  // 触发父组件事件，实现页面内导航
  emit('navigate-to-user-messages', {
    groupId: group.chat_id,
    userId: userDetail.user_id
  })

  // 关闭抽屉
  emit('update:visible', false)
}

// 检查用户档案是否存在
const checkProfileExists = async (user_id: string) => {
  try {
    const response = await userProfileApi.getByTgUser(user_id)
    const data = (response.data as any)
    if (data.err_code === 0) {
      const profile = data.payload?.profile
      profileExists.value = !!profile && !profile.is_deleted
    } else {
      // 404或其他错误表示档案不存在
      profileExists.value = false
    }
  } catch (error: any) {
    // 网络错误或404都表示档案不存在，不显示警告信息
    console.debug('用户档案检查:', error.response?.status === 404 ? '档案不存在' : '检查失败')
    profileExists.value = false
  }
}

// 加载文件夹树数据
const loadFolderTree = async () => {
  try {
    const response = await profileFolderApi.getTree()
    if ((response.data as any).err_code === 0) {
      folderTreeData.value = (response.data as any).payload.tree_data
    } else {
      ElMessage.error((response.data as any).err_msg || '加载文件夹树失败')
    }
  } catch (error: any) {
    console.error('加载文件夹树失败:', error)
    ElMessage.error('加载文件夹树失败')
  }
}

// 打开创建全息档案对话框
const handleCreateHolisticProfile = async () => {
  const userDetail = currentUserDetail.value
  if (!userDetail) {
    ElMessage.warning('用户信息不完整')
    return
  }

  // 加载文件夹树
  await loadFolderTree()

  // 初始化表单
  createProfileForm.value = {
    profile_name: userDetail.senderName || userDetail.username || `用户${userDetail.user_id}`,
    folder_id: null,
    status: 'draft'
  }

  createProfileDialogVisible.value = true
}

// 保存全息档案
const handleSaveHolisticProfile = async () => {
  if (!createProfileFormRef.value) return

  await createProfileFormRef.value.validate(async (valid: boolean) => {
    if (valid) {
      const userDetail = currentUserDetail.value
      if (!userDetail) return

      profileCreating.value = true
      try {
        const payload = {
          tg_user_id: userDetail.user_id,
          profile_name: createProfileForm.value.profile_name,
          created_by: userStore.userInfo?.id || 1,
          folder_id: createProfileForm.value.folder_id ? parseInt(String(createProfileForm.value.folder_id)) : null,
          status: createProfileForm.value.status
        }

        console.log('创建档案请求:', payload)
        const response = await userProfileApi.create(payload)

        if ((response.data as any).err_code === 0) {
          ElMessage.success('全息档案创建成功')
          profileExists.value = true
          createProfileDialogVisible.value = false
        } else {
          ElMessage.error((response.data as any).err_msg || '创建全息档案失败')
        }
      } catch (error: any) {
        console.error('创建全息档案失败:', error)
        ElMessage.error('创建全息档案失败: ' + (error.response?.data?.err_msg || error.message))
      } finally {
        profileCreating.value = false
      }
    }
  })
}

// 重置创建档案表单
const resetCreateProfileForm = () => {
  if (createProfileFormRef.value) {
    createProfileFormRef.value.clearValidate()
  }
  createProfileForm.value = {
    profile_name: '',
    folder_id: null,
    status: 'draft'
  }
}
</script>

<style scoped>
/* 用户未找到空状态样式 */
.user-not-found {
  padding: 60px 20px;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

.empty-title {
  font-size: 16px;
  color: #606266;
  margin: 16px 0 8px 0;
  font-weight: 500;
}

.empty-subtitle {
  font-size: 13px;
  color: #909399;
  margin: 0;
  font-family: monospace;
}

/* 用户详情抽屉样式 */
.user-detail-drawer {
  padding: 20px;
}

.user-basic-info {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
}

.user-avatar-large {
  flex-shrink: 0;
}

.user-name-info {
  flex: 1;
}

.user-name {
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.user-name.key-focus {
  color: #f56c6c;
  font-weight: 700;
}

.user-id {
  margin: 0 0 4px 0;
  font-size: 12px;
  color: #666;
}

.username {
  margin: 0;
  font-size: 14px;
  color: #1890ff;
}

.placeholder-sections {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.section {
  background: #fff;
  padding: 16px;
  border-radius: 6px;
  border: 1px solid #f0f0f0;
}

.section h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
  color: #333;
  border-bottom: 1px solid #f0f0f0;
  padding-bottom: 8px;
}

.placeholder-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #fafafa;
}

.placeholder-item:last-child {
  border-bottom: none;
}

.placeholder-item .label {
  font-size: 13px;
  color: #666;
  font-weight: 500;
  min-width: 80px;
}

.placeholder-item .value {
  font-size: 13px;
  color: #333;
}

.placeholder-item .value.key-focus {
  color: #f56c6c;
  font-weight: 600;
}

/* 备注编辑样式 */
.remark-container {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.remark-display {
  cursor: pointer;
  flex: 1;
  padding: 4px 8px;
  border-radius: 4px;
  transition: background-color 0.3s;
  color: #666;
}

.remark-display:hover {
  background-color: #f5f7fa;
}

.remark-edit {
  flex: 1;
}

.edit-btn {
  padding: 4px;
  font-size: 12px;
}

/* 个人简介样式 */
.bio-item {
  flex-direction: column;
  align-items: flex-start !important;
}

.bio-item .label {
  margin-bottom: 8px;
}

.bio-content {
  width: 100%;
  max-height: 120px;
  overflow-y: auto;
}

.bio-text {
  font-size: 13px;
  color: #333;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
}

.bio-empty {
  font-size: 13px;
  color: #999;
  font-style: italic;
}

/* 统计数据样式 */
.stats-content {
  min-height: 80px;
}

/* 标签管理样式 */
.tags-content {
  padding: 8px 0;
}

.user-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.tag-item {
  margin: 0;
}

.add-tag-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  height: 24px;
}

/* 群组列表样式 */
.groups-content {
  padding: 8px 0;
}

.empty-groups {
  text-align: center;
  color: #999;
  padding: 20px 0;
  font-size: 13px;
}

.group-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.group-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  border: 1px solid #f0f0f0;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: #fafafa;
}

.group-item:hover {
  border-color: #1890ff;
  background: #f0f8ff;
  box-shadow: 0 2px 4px rgba(24, 144, 255, 0.1);
}

.group-info {
  flex: 1;
}

.group-name {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 4px;
}

.group-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #666;
}

.message-count {
  color: #1890ff;
  font-weight: 500;
}

.group-arrow {
  color: #999;
  font-size: 14px;
  transition: color 0.3s;
}

.group-item:hover .group-arrow {
  color: #1890ff;
}

/* 对话框样式调整 */
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* 标签选择对话框样式 */
.tag-selection-content {
  max-height: 400px;
  overflow-y: auto;
}

.available-tags-section, .selected-tags-section {
  margin-bottom: 20px;
}

.available-tags-section h4, .selected-tags-section h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
  color: #333;
  border-bottom: 1px solid #f0f0f0;
  padding-bottom: 8px;
}

.available-tags, .selected-tags {
  min-height: 60px;
  border: 1px solid #f0f0f0;
  border-radius: 6px;
  padding: 12px;
  background: #fafafa;
}

.tag-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.selectable-tag {
  transition: all 0.3s ease;
  user-select: none;
}

.selectable-tag:hover {
  transform: scale(1.05);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.empty-tags {
  text-align: center;
  color: #999;
  padding: 20px 0;
  font-size: 13px;
  font-style: italic;
}

/* 滚动条样式 */
.bio-content::-webkit-scrollbar {
  width: 6px;
}

.bio-content::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.bio-content::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.bio-content::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* 重点关注开关样式 */
.focus-switch-item {
  .focus-switch-container {
    display: flex;
    align-items: center;
    justify-content: flex-end;
  }
}

/* 全息档案按钮样式 */
.holistic-profile-item {
  flex-direction: column;
  align-items: flex-start !important;
  padding: 12px 0 !important;
  border-bottom: none !important;

  .holistic-profile-btn {
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    font-size: 14px;
    font-weight: 500;
  }
}

/* 信息变动历史样式 */
.change-records-content {
  padding: 8px 0;
  min-height: 60px;
}

.empty-records {
  text-align: center;
  color: #999;
  padding: 20px 0;
  font-size: 13px;
  font-style: italic;
}

.change-records-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.change-record-item {
  border: 1px solid #f0f0f0;
  border-radius: 6px;
  padding: 12px;
  background: #fafafa;
  transition: all 0.3s ease;
}

.change-record-item:hover {
  border-color: #e6f7ff;
  background: #f0f8ff;
}

.change-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  padding-bottom: 8px;
  border-bottom: 1px solid #f0f0f0;
}

.change-type {
  font-size: 13px;
  font-weight: 600;
  color: #1890ff;
  background: #e6f7ff;
  padding: 2px 8px;
  border-radius: 12px;
}

.change-time {
  font-size: 11px;
  color: #999;
}

.change-content {
  padding-top: 4px;
}

.change-before-after {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.change-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.change-label {
  font-size: 12px;
  color: #666;
  min-width: 50px;
  font-weight: 500;
}

.change-value {
  font-size: 12px;
  padding: 4px 8px;
  border-radius: 4px;
  flex: 1;
  word-break: break-all;
}

.change-value.before {
  background: #fff2e8;
  color: #d46b08;
  border: 1px solid #ffd591;
}

.change-value.after {
  background: #f6ffed;
  color: #52c41a;
  border: 1px solid #b7eb8f;
}

.username-value {
  font-family: monospace;
  font-weight: 500;
}

.avatar-change {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.change-avatar {
  flex-shrink: 0;
}

.empty-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: #f5f5f5;
  border: 1px dashed #d9d9d9;
  border-radius: 4px;
  font-size: 10px;
  color: #999;
  text-align: center;
}

.view-more-container {
  margin-top: 16px;
  text-align: center;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

.view-more-btn {
  font-size: 12px;
  color: #1890ff;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  transition: all 0.3s ease;
}

.view-more-btn:hover {
  color: #40a9ff;
  transform: translateX(2px);
}
</style>