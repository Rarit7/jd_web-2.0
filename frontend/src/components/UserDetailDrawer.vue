<template>
  <el-drawer
    v-model="isVisible"
    title="用户详情"
    direction="rtl"
    size="400px"
  >
    <div v-if="userDetail" class="user-detail-drawer">
      <!-- 用户头像和基本信息 -->
      <div class="user-basic-info">
        <div class="user-avatar-large">
          <el-avatar :size="80" :src="userDetail.avatar" shape="square">
            <span>{{ userDetail.senderName.charAt(0) }}</span>
          </el-avatar>
        </div>
        <div class="user-name-info">
          <h3 class="user-name" :class="{ 'key-focus': userDetail.is_key_focus }">
            {{ userDetail.senderName }}
          </h3>
          <p class="user-id">ID: {{ userDetail.user_id }}</p>
          <p class="username" v-if="userDetail.username">
            @{{ userDetail.username }}
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
              <div v-if="userDetail.bio" class="bio-text">
                {{ userDetail.bio }}
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
  </el-drawer>
</template>

<script setup lang="ts">
import { computed, ref, watch, nextTick } from 'vue'
import { Edit, Plus, ArrowRight } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { chatHistoryApi } from '@/api/chat-history'
import { tgUsersApi } from '@/api/tg-users'
import { tagsApi, type Tag as TagType } from '@/api/tags'

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

// 定义组件props
interface Props {
  visible: boolean
  userDetail: UserInfo | null
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

// 响应式数据
const editingRemark = ref(false)
const tempRemark = ref('')
const localRemark = ref('')
const remarkInput = ref()

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

// 双向绑定visible属性
const isVisible = computed({
  get: () => props.visible,
  set: (value: boolean) => emit('update:visible', value)
})

// 监听用户详情变化，加载相关数据
watch(() => props.userDetail, (newUserDetail) => {
  if (newUserDetail) {
    localRemark.value = newUserDetail.remark || ''
    localKeyFocus.value = newUserDetail.is_key_focus || false
    loadUserStats()
    loadUserTags()
    loadUserGroups()
  }
}, { immediate: true })

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
  if (!props.userDetail) return
  
  try {
    // 获取当前用户标签ID列表
    const tagIds = userTags.value.map(t => t.id).join(',')
    
    // 调用API保存备注和标签
    await tgUsersApi.updateUser({
      tg_user_id: props.userDetail.id,
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
const handleFocusToggle = async (value: boolean) => {
  if (!props.userDetail) return
  
  focusLoading.value = true
  try {
    // 调用API更新重点关注状态
    const response = await tgUsersApi.toggleFocus(props.userDetail.id)
    
    if (response.data.err_code === 0) {
      // 更新本地状态
      localKeyFocus.value = response.data.payload.is_key_focus
      if (props.userDetail) {
        props.userDetail.is_key_focus = response.data.payload.is_key_focus
      }
      ElMessage.success(response.data.payload.message)
    } else {
      // 如果失败，恢复先前的状态
      localKeyFocus.value = !value
      ElMessage.error(response.data.err_msg || '操作失败')
    }
  } catch (error) {
    console.error('更新重点关注状态失败:', error)
    // 如果失败，恢复先前的状态
    localKeyFocus.value = !value
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
  if (!props.userDetail) return
  
  try {
    // 获取当前用户所有标签ID
    const currentTagIds = userTags.value.map(t => t.id)
    const newTagIds = [...currentTagIds, tag.id]
    
    // 调用API更新用户标签
    await tgUsersApi.updateUser({
      tg_user_id: props.userDetail.id,
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
  if (!props.userDetail) return
  
  try {
    // 获取删除该标签后的标签ID列表
    const remainingTagIds = userTags.value
      .filter(t => t.id !== tag.id)
      .map(t => t.id)
    
    // 调用API更新用户标签
    await tgUsersApi.updateUser({
      tg_user_id: props.userDetail.id,
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
  if (!props.userDetail) return
  
  statsLoading.value = true
  try {
    const response = await chatHistoryApi.getUserStats(props.userDetail.user_id)
    
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
  if (!props.userDetail) return
  
  try {
    // 从用户详情获取标签信息
    if (props.userDetail.remark && props.userDetail.id) {
      // 先获取完整的用户信息，包括标签
      const response = await tgUsersApi.getList({
        keyword: '',
        group_id: '',
        tag_ids: '',
        page: 1,
        page_size: 1
      })
      
      if (response.data.err_code === 0) {
        // 找到当前用户
        const currentUser = response.data.payload.data.find((user: any) => user.id === props.userDetail?.id)
        if (currentUser && currentUser.tag_id_list) {
          // 获取标签库中的所有标签
          const tagsResponse = await tagsApi.getList()
          if (tagsResponse.err_code === 0) {
            const tagIds = currentUser.tag_id_list.split(',').map((id: string) => parseInt(id.trim())).filter((id: number) => !isNaN(id))
            userTags.value = tagsResponse.payload.data.filter(tag => tagIds.includes(tag.id))
          }
        }
      }
    }
  } catch (error) {
    console.error('加载用户标签失败:', error)
  }
}

// 加载用户所在群组
const loadUserGroups = async () => {
  if (!props.userDetail) return
  
  groupsLoading.value = true
  try {
    const response = await chatHistoryApi.getUserStats(props.userDetail.user_id)
    
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

// 导航到用户在指定群组的消息记录
const navigateToUserMessages = (group: UserGroup) => {
  if (!props.userDetail) return
  
  // 触发父组件事件，实现页面内导航
  emit('navigate-to-user-messages', {
    groupId: group.chat_id,
    userId: props.userDetail.user_id
  })
  
  // 关闭抽屉
  emit('update:visible', false)
}
</script>

<style scoped>
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
</style>