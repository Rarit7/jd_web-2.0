<template>
  <div class="chat-content">
    <!-- 顶部工具栏 -->
    <div class="chat-toolbar">
      <div class="toolbar-left">
        <div class="search-boxes">
          <el-input
            v-model="contentSearchText"
            placeholder="搜索聊天记录..."
            :prefix-icon="Search"
            clearable
            @input="handleContentSearch"
            class="search-input-content"
          />
          <el-input
            v-model="userIdSearchText"
            placeholder="搜索用户ID..."
            :prefix-icon="User"
            clearable
            @keyup.enter="handleUserIdSearch"
            @clear="handleUserIdClear"
            class="search-input-userid"
          >
            <template #append>
              <el-button 
                :icon="Search" 
                @click="handleUserIdSearch"
                :loading="userIdSearchLoading"
              />
            </template>
          </el-input>
        </div>
      </div>
      <div class="toolbar-center">
        <div class="date-filter">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            @change="handleDateChange"
          />
        </div>
      </div>
      <div class="toolbar-right">
        <el-button-group>
          <el-button :icon="Refresh" @click="refreshData">刷新</el-button>
          <el-button :icon="Download" @click="exportMessages">导出</el-button>
        </el-button-group>
      </div>
    </div>
    
    <div class="chat-layout">
      <!-- 左侧面板 (1/4宽度) -->
      <div class="left-panel">
        <el-card class="chat-list-card">
          <template #header>
            <div class="card-header">
              <span>聊天列表</span>
              <el-input
                v-model="searchText"
                placeholder="搜索聊天..."
                size="small"
                :prefix-icon="Search"
                clearable
                class="search-input"
              />
            </div>
          </template>
          
          <div v-loading="loading" class="chat-list">
            <!-- 群组聊天区域 -->
            <div v-if="groupedChats.group.length > 0" class="chat-group">
              <div class="chat-group-header">
                <el-icon><ChatLineSquare /></el-icon>
                <span>群组聊天 ({{ groupedChats.group.length }})</span>
              </div>
              <div 
                v-for="chat in groupedChats.group" 
                :key="chat.id"
                class="chat-item"
                :class="{ active: selectedChatId === chat.id }"
                @click="selectChat(chat.id)"
              >
                <div class="chat-avatar">
                  <el-avatar :size="40" :src="chat.avatar" >
                    <span>{{ chat.name.charAt(0) }}</span>
                  </el-avatar>
                  <div class="chat-type-indicator group"></div>
                </div>
                <div class="chat-info">
                  <div class="chat-name">
                    <span class="chat-title">{{ chat.title || chat.name }}</span>
                    <span v-if="chat.remark" class="chat-remark">({{ chat.remark }})</span>
                  </div>
                  <div class="chat-last-message">{{ chat.lastMessage }}</div>
                  <div class="chat-time">{{ chat.lastTime }}</div>
                </div>
              </div>
            </div>
            
            <!-- 频道聊天区域 -->
            <div v-if="groupedChats.channel.length > 0" class="chat-group">
              <div class="chat-group-header">
                <el-icon><ChatRound /></el-icon>
                <span>频道 ({{ groupedChats.channel.length }})</span>
              </div>
              <div 
                v-for="chat in groupedChats.channel" 
                :key="chat.id"
                class="chat-item"
                :class="{ active: selectedChatId === chat.id }"
                @click="selectChat(chat.id)"
              >
                <div class="chat-avatar">
                  <el-avatar :size="40" :src="chat.avatar" >
                    <span>{{ chat.name.charAt(0) }}</span>
                  </el-avatar>
                  <div class="chat-type-indicator channel"></div>
                </div>
                <div class="chat-info">
                  <div class="chat-name">
                    <span class="chat-title">{{ chat.title || chat.name }}</span>
                    <span v-if="chat.remark" class="chat-remark">({{ chat.remark }})</span>
                  </div>
                  <div class="chat-last-message">{{ chat.lastMessage }}</div>
                  <div class="chat-time">{{ chat.lastTime }}</div>
                </div>
              </div>
            </div>
            
            <!-- 空状态 -->
            <div v-if="filteredChats.length === 0 && !loading" class="empty-chat-list">
              <el-empty description="暂无聊天记录" :image-size="60" />
            </div>
          </div>
        </el-card>
      </div>
      
      <!-- 右侧面板 (3/4宽度) -->
      <div class="right-panel">
        <el-card class="chat-detail-card">
          <div class="chat-header">
            <div v-if="selectedChat" class="chat-title">
              <el-avatar :size="32" :src="selectedChat.avatar" >
                <span>{{ selectedChat.name.charAt(0) }}</span>
              </el-avatar>
              <div class="title-info">
                <span class="title-name">
                  {{ selectedChat.title || selectedChat.name }}
                  <span v-if="selectedChat.remark" class="title-remark">({{ selectedChat.remark }})</span>
                </span>
                <span class="title-status">
                  群组ID: {{ selectedChat.chat_id }} · 
                  {{ selectedChat.memberCount }}人 · 
                  {{ selectedChat.status }}
                </span>
              </div>
            </div>
            <div v-else class="no-selection">
              选择一个聊天开始查看消息
            </div>
            
            <!-- 搜索框 -->
            <div v-if="selectedChat" class="chat-search">
              <div class="search-container">
                <el-input
                  v-model="searchKeyword"
                  placeholder="搜索本群聊天..."
                  :prefix-icon="Search"
                  clearable
                  @keyup.enter="handleChatSearch"
                  @clear="clearChatSearch"
                  @focus="showSearchHistory = searchHistory.length > 0"
                  @blur="handleSearchBlur"
                  class="search-input"
                />
                <!-- 搜索历史下拉 -->
                <div v-if="showSearchHistory && searchHistory.length > 0" class="search-history-dropdown">
                  <div class="search-history-header">
                    <span>搜索历史</span>
                    <el-button 
                      type="text" 
                      size="small"
                      @click="clearSearchHistory"
                      class="clear-history-btn"
                    >
                      清空
                    </el-button>
                  </div>
                  <div class="search-history-list">
                    <div 
                      v-for="(item, index) in searchHistory" 
                      :key="index"
                      class="search-history-item"
                      @mousedown.prevent="selectSearchHistory(item)"
                    >
                      <el-icon class="history-icon"><Search /></el-icon>
                      <span class="history-text">{{ item }}</span>
                    </div>
                  </div>
                </div>
              </div>
              <el-button 
                type="primary" 
                :icon="Search" 
                @click="handleChatSearch"
                :loading="searchLoading"
                size="small"
              >
                搜索
              </el-button>
            </div>
          </div>
          
          <div class="chat-messages" :style="{ backgroundImage: 'url(/bg.webp)', backgroundColor: '#e8f4fd' }">
            <!-- 自定义加载遮罩层 -->
            <div v-if="messageLoading" class="custom-loading-mask">
              <div class="loading-content">
                <el-icon class="is-loading"><Loading /></el-icon>
                <span>加载中...</span>
              </div>
            </div>
            <div v-if="selectedChat && messageList.length > 0" class="message-list">
              <div 
                v-for="message in messageList" 
                :key="message.id"
                :data-message-id="message.id"
                class="message-item"
                :class="{ 'message-self': message.isSelf }"
              >
                <div class="message-avatar" @click="showUserDetail(message)">
                  <el-avatar :size="32" :src="message.avatar" class="clickable-avatar">
                    <span>{{ message.senderName.charAt(0) }}</span>
                  </el-avatar>
                </div>
                <div class="message-content">
                  <div class="message-header">
                    <span class="sender-name" :class="{ 'key-focus': message.is_key_focus }">{{ message.senderName }}</span>
                    <span class="message-time">{{ message.time }}</span>
                  </div>
                  <div class="message-body">
                    <!-- 文本内容 -->
                    <div v-if="message.textContent" class="text-message">
                      {{ message.textContent }}
                    </div>
                    
                    <!-- 图片内容 -->
                    <div v-if="message.images && message.images.length > 0" class="image-message">
                      <div class="image-grid" :class="`images-${Math.min(message.images.length, 4)}`">
                        <el-image
                          v-for="(image, index) in message.images.slice(0, 9)"
                          :key="index"
                          :src="image"
                          :preview-src-list="message.images"
                          :initial-index="index"
                          fit="cover"
                          lazy
                          class="message-image"
                          :scroll-container="'.chat-messages'"
                        >
                          <template #placeholder>
                            <div class="image-placeholder">
                              <el-icon><Picture /></el-icon>
                              <span>加载中...</span>
                            </div>
                          </template>
                          <template #error>
                            <div class="image-error">
                              <el-icon><Picture /></el-icon>
                              <span>{{ image.split('/').pop() || '加载失败' }}</span>
                            </div>
                          </template>
                        </el-image>
                        <!-- 如果图片超过9张，显示更多提示 -->
                        <div v-if="message.images.length > 9" class="more-images">
                          +{{ message.images.length - 9 }}
                        </div>
                      </div>
                    </div>
                    
                    <!-- 文件内容 -->
                    <div v-if="message.files && message.files.length > 0" class="file-message">
                      <div v-for="(file, index) in message.files" :key="index" class="file-item">
                        <!-- 视频文件：有缩略图显示缩略图+图标，否则显示视频图标 -->
                        <div v-if="file.fileType === 'video' && file.videoThumbnail" class="file-video-with-thumbnail">
                          <div class="video-thumbnail-wrapper">
                            <img :src="file.videoThumbnail" class="video-thumbnail" />
                            <el-icon class="video-overlay-icon">
                              <Film />
                            </el-icon>
                          </div>
                          <div class="file-info">
                            <span class="file-name">{{ file.displayName }}</span>
                            <span v-if="file.fileSize" class="file-size">{{ formatFileSize(file.fileSize) }}</span>
                          </div>
                        </div>
                        <!-- 普通文件显示 -->
                        <template v-else>
                          <el-icon class="file-type-icon">
                            <Picture v-if="file.fileType === 'sticker'" />
                            <Film v-else-if="file.fileType === 'video'" />
                            <Microphone v-else-if="file.fileType === 'audio'" />
                            <FolderOpened v-else-if="file.fileType === 'archive'" />
                            <Document v-else-if="file.fileType === 'document'" />
                            <Cpu v-else-if="file.fileType === 'program'" />
                            <Paperclip v-else />
                          </el-icon>
                          <div class="file-info">
                            <span class="file-name">{{ file.displayName }}</span>
                            <span v-if="file.fileSize" class="file-size">{{ formatFileSize(file.fileSize) }}</span>
                          </div>
                        </template>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div v-else-if="selectedChat && messageList.length === 0 && !messageLoading" class="empty-message">
              <el-empty description="该群组暂无聊天记录" />
            </div>
            <div v-else class="empty-message">
              <el-empty description="请选择一个聊天开始查看消息" />
            </div>
          </div>
          
          <!-- 分页 -->
          <div v-if="selectedChat && totalMessages > 0" class="message-pagination">
            <el-pagination
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :page-sizes="[20, 50, 100]"
              :total="totalMessages"
              layout="total, sizes, prev, pager, next, jumper"
              @current-change="handlePageChange"
              @size-change="handleSizeChange"
              small
            />
          </div>
        </el-card>
      </div>
    </div>

    <!-- 用户详情抽屉 -->
    <UserDetailDrawer
      v-model:visible="showUserDrawer"
      :userId="selectedUserId"
      :currentGroupId="selectedChat?.chat_id"
      @navigate-to-user-messages="handleNavigateToUserMessages"
    />

    <!-- 搜索结果抽屉 -->
    <el-drawer
      v-model="showSearchDrawer"
      title="搜索结果"
      direction="rtl"
      size="700px"
    >
      <div class="search-results-drawer">
        <!-- 搜索信息 -->
        <div class="search-info">
          <div class="search-summary">
            <span class="search-keyword">搜索: "{{ currentSearchKeyword }}"</span>
            <span class="result-count">共找到 {{ searchResults.length }} 条结果</span>
          </div>
          <el-button @click="clearChatSearch" size="small" type="info">清空搜索</el-button>
        </div>

        <!-- 搜索结果列表 -->
        <div v-loading="searchLoading" class="search-results">
          <div v-if="searchResults.length === 0 && !searchLoading" class="empty-results">
            <el-empty description="未找到匹配的聊天记录" />
          </div>
          <div v-else class="result-list">
            <div 
              v-for="message in searchResults" 
              :key="message.id"
              class="result-item"
              @click="jumpToMessage(message)"
            >
              <div class="result-header">
                <el-avatar :size="24" :src="message.avatar" >
                  <span>{{ message.senderName.charAt(0) }}</span>
                </el-avatar>
                <span class="sender-name" :class="{ 'key-focus': message.is_key_focus }">
                  {{ message.senderName }}
                </span>
                <span class="message-time">{{ formatSearchTime(message.rawTime) }}</span>
              </div>
              <div class="result-content" v-html="highlightKeyword(message.content, currentSearchKeyword)"></div>
              <div class="result-meta">
                <el-tag size="small" type="info">{{ message.type === 'text' ? '文本' : message.type === 'image' ? '图片' : '文件' }}</el-tag>
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-drawer>

    <!-- 导出对话框 -->
    <el-dialog v-model="showExportDialog" title="导出群组聊天记录" width="500px">
      <el-form :model="exportForm" :rules="exportRules" ref="exportFormRef" label-width="120px">
        <el-form-item label="选择群组" prop="chat_id">
          <el-select v-model="exportForm.chat_id" placeholder="请选择群组" style="width: 100%">
            <el-option
              v-for="chat in allChats"
              :key="chat.chat_id"
              :label="chat.title || chat.name"
              :value="chat.chat_id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="选择时间段">
          <el-date-picker
            v-model="exportForm.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="包含图片文件">
          <el-switch v-model="exportForm.get_photo" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showExportDialog = false">取消</el-button>
        <el-button type="primary" @click="handleExport" :loading="exportLoading">确定导出</el-button>
      </template>
    </el-dialog>

  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { Search, User, Document, Refresh, Download, Picture, PictureRounded, ChatDotSquare, ChatLineSquare, ChatRound, Loading, Film, Microphone, FolderOpened, Cpu, Paperclip } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { tgGroupsApi, type TgGroup } from '@/api/tg-groups'
import { chatHistoryApi, type ChatMessage, type UserChatHistoryResponse } from '@/api/chat-history'
import { useRoute } from 'vue-router'
import { formatTime, formatDateForApi, formatUTCToLocal } from '@/utils/date'
import UserDetailDrawer from '@/components/UserDetailDrawer.vue'

// Route实例
const route = useRoute()

// 聊天数据接口，基于TgGroup扩展
interface Chat {
  id: number
  name: string
  title: string
  avatar: string
  lastMessage: string
  lastTime: string
  memberCount: number
  status: string
  chat_id: string
  desc: string
  tag: string
  remark: string
  photo: string
  group_type: number
  records_count: number
}

interface DocumentInfo {
  path: string
  ext: string
  mime_type: string
  is_sticker?: boolean
  sticker_type?: string
  display_text?: string
  display_icon?: string
  filename_origin?: string
  file_size?: number
  video_thumb_path?: string
}

interface FileInfo {
  name: string
  displayName: string
  isSticker: boolean
  fileType: string
  fileSize: number
  videoThumbnail?: string
}

interface Message {
  id: number
  chatId: string
  senderName: string
  nickname: string
  username: string
  user_id: string
  avatar: string
  content: string  // 保留用于向后兼容
  type: 'text' | 'image' | 'file' | 'mixed'
  fileName?: string  // 保留用于向后兼容
  time: string
  rawTime: string
  isSelf: boolean
  is_key_focus?: boolean
  photo_paths: string[]
  document_paths: string[]
  documents?: DocumentInfo[]  // 新增：包含类型信息的文档列表
  reply_to_msg_id: number
  // 新增字段支持混合内容
  textContent?: string
  images?: string[]
  files?: FileInfo[]
}

// 响应式数据
const loading = ref(false)
const searchText = ref('')
const selectedChatId = ref<number | null>(null)
const currentPage = ref(1)
const pageSize = ref(20)
const totalMessages = ref(0)
const chatList = ref<Chat[]>([])
const messageList = ref<Message[]>([])
const messageLoading = ref(false)

// 用户详情抽屉相关
const showUserDrawer = ref(false)
const selectedUserId = ref<string>('')

// 搜索相关
const showSearchDrawer = ref(false)
const searchKeyword = ref('')
const currentSearchKeyword = ref('')
const searchResults = ref<Message[]>([])
const searchLoading = ref(false)

// 搜索历史相关
const searchHistory = ref<string[]>([])
const showSearchHistory = ref(false)
const SEARCH_HISTORY_KEY = 'chat_search_history'

// 工具栏相关
const dateRange = ref<[Date, Date] | null>(null)
const contentSearchText = ref('')
const userIdSearchText = ref('')
const userIdSearchLoading = ref(false)

// 导出对话框相关
const showExportDialog = ref(false)
const exportLoading = ref(false)
const exportFormRef = ref()
const exportForm = reactive({
  chat_id: '',
  dateRange: null as [Date, Date] | null,
  get_photo: false
})

const exportRules = {
  chat_id: [
    { required: true, message: '请选择群组', trigger: 'change' }
  ]
}

// 获取聊天列表（包含群组和私人聊天）
const fetchChatList = async () => {
  loading.value = true
  try {
    const response = await tgGroupsApi.getList()
    if (response.data.err_code === 0) {
      // 将TgGroup数据转换为Chat格式
      const groupChats = response.data.payload.data.map((group: TgGroup) => ({
        id: group.id,
        name: group.title || group.name,
        title: group.title,
        avatar: buildAvatarUrl(group.photo || ''),
        lastMessage: group.desc || '暂无最新消息',
        lastTime: formatTime(group.latest_postal_time),
        memberCount: group.members_count || 0,
        status: group.status,
        chat_id: group.chat_id,
        desc: group.desc,
        tag: group.tag,
        remark: group.remark,
        photo: group.photo,
        group_type: group.group_type,
        records_count: group.records_count || 0
      }))

      // 不再获取私人聊天列表，只显示群组聊天
      chatList.value = groupChats
      
      // 检查路由参数中是否指定了要查看的群组
      const groupIdFromRoute = route.query.group_id as string
      if (groupIdFromRoute && chatList.value.length > 0) {
        // 根据chat_id查找对应的群组
        const targetGroup = chatList.value.find(chat => chat.chat_id === groupIdFromRoute)
        if (targetGroup) {
          selectChat(targetGroup.id)
          return
        }
      }
      
      // 默认选择第一个聊天
      if (chatList.value.length > 0 && !selectedChatId.value) {
        selectChat(chatList.value[0].id)
      }
    } else {
      // 如果是认证错误，给出更清晰的提示  
      if (response.data.err_code === 40101) {
        ElMessage.error('请先登录系统')
      } else {
        ElMessage.error(response.data.err_msg || '获取群组列表失败')
      }
    }
  } catch (error: any) {
    console.error('获取群组列表失败:', error)
    // 检查是否是网络错误或认证问题
    if (error.response?.status === 401) {
      ElMessage.error('请先登录系统')
    } else {
      ElMessage.error('获取群组列表失败')
    }
  } finally {
    loading.value = false
  }
}

// 构建头像URL
const buildAvatarUrl = (avatarPath: string): string => {
  if (!avatarPath) return ''
  
  // 如果已经是完整URL，直接返回
  if (avatarPath.startsWith('http://') || avatarPath.startsWith('https://')) {
    return avatarPath
  }
  
  // 如果是相对路径，构建完整路径
  if (avatarPath.startsWith('images/')) {
    return `/static/${avatarPath}`
  }
  
  // 否则假设是文件名，添加avatar目录前缀
  return `/static/images/avatar/${avatarPath}`
}

// 构建图片URL
const buildImageUrl = (imagePath: string): string => {
  if (!imagePath) return ''
  
  // 如果已经是完整URL，直接返回
  if (imagePath.startsWith('http://') || imagePath.startsWith('https://')) {
    return imagePath
  }
  
  // 如果是相对路径，构建完整路径
  if (imagePath.startsWith('images/') || imagePath.startsWith('document/')) {
    return `/static/${imagePath}`
  }
  
  // 如果是视频缩略图路径，添加document前缀
  if (imagePath.startsWith('thumbs/')) {
    return `/static/document/${imagePath}`
  }
  
  // 如果只是文件名，添加images目录前缀
  return `/static/images/${imagePath}`
}


// 获取选中群组的聊天记录
const fetchMessages = async (chatId: string) => {
  messageLoading.value = true
  try {
    let response: any
    
    // 检查是否是按用户ID搜索
    if (userIdSearchText.value) {
      const userId = userIdSearchText.value.trim()
      if (!userId) {
        messageLoading.value = false
        return
      }
      
      // 根据搜索类型构建搜索参数
      const searchParams: any = {
        page: currentPage.value,
        page_size: pageSize.value,
        start_date: dateRange.value ? formatDateForApi(dateRange.value[0]) : '',
        end_date: dateRange.value ? formatDateForApi(dateRange.value[1]) : ''
      }
      
      // 调用新的API：按用户ID和群组ID搜索
      response = await chatHistoryApi.getByUserInGroup(chatId, userId, searchParams)
      
      if (response.data.err_code === 0) {
        const payload = response.data.payload
        totalMessages.value = payload.total_records
        
        
        // 转换聊天消息数据格式
        messageList.value = payload.data.map((msg: ChatMessage) => ({
          id: msg.id,
          chatId: msg.chat_id,
          senderName: msg.nickname || msg.username,
          nickname: msg.nickname,
          username: msg.username,
          user_id: msg.user_id,
          avatar: buildAvatarUrl(msg.user_avatar || ''),
          content: determineMainMessageType(msg) === 'image' ? buildImageUrl(msg.photo_paths[0]) : (msg.message || ''),
          type: determineMainMessageType(msg),
          fileName: getFileName(msg.document_paths),
          time: formatTime(msg.postal_time),
          rawTime: msg.postal_time,
          isSelf: false,
          is_key_focus: msg.is_key_focus || false,
          photo_paths: msg.photo_paths || [],
          document_paths: msg.document_paths || [],
          documents: msg.documents || [],
          reply_to_msg_id: msg.reply_to_msg_id || 0,
          // 新增混合内容支持
          textContent: hasTextContent(msg) ? msg.message : undefined,
          images: hasImageContent(msg) ? [
            // 原有的photo_paths
            ...msg.photo_paths.filter(path => path).map(path => buildImageUrl(path)),
            // 图片类型的documents
            ...getImageDocuments(msg).map(doc => buildImageUrl(doc.path))
          ] : [],
          files: hasFileContent(msg) ? (() => {
            const files = []
            // 获取非图片类型的文档（自动处理新旧格式兼容性）
            const nonImageDocs = getNonImageDocuments(msg)
            
            
            files.push(...nonImageDocs.map(doc => {
              const fileType = getFileType(doc)
              
              // 检查是否为sticker文件
              if (doc.is_sticker) {
                const displayText = doc.display_text || '【动画表情】'
                return {
                  name: displayText,
                  displayName: displayText,
                  isSticker: true,
                  fileType: 'sticker',
                  fileSize: doc.file_size || 0
                }
              }
              
              // 对于其他文件类型，使用原始文件名和大小
              const fileName = doc.path ? doc.path.split('/').pop() || doc.path : doc.filename_origin || ''
              const displayName = doc.filename_origin || fileName
              
              // 检查是否有视频缩略图
              let videoThumbnail = ''
              if (fileType === 'video') {
                // 只有后端返回了确定的缩略图路径才使用
                if (doc.video_thumb_path) {
                  videoThumbnail = buildImageUrl(doc.video_thumb_path)
                }
                // 不再自动生成可能不存在的缩略图路径
              }
              
              return {
                name: fileName,
                displayName: displayName,
                isSticker: false,
                fileType: fileType,
                fileSize: doc.file_size || 0,
                videoThumbnail: videoThumbnail
              }
            }))
            
            
            return files
          })() : []
        }))
      } else {
        if (response.data.err_code === 40101) {
          ElMessage.error('请先登录系统')
        } else {
          ElMessage.error(response.data.err_msg || '按用户ID搜索失败')
        }
      }
    } else {
      // 常规搜索（按内容）
      const searchParams: any = {
        page: currentPage.value,
        page_size: pageSize.value,
        start_date: dateRange.value ? formatDateForApi(dateRange.value[0]) : '',
        end_date: dateRange.value ? formatDateForApi(dateRange.value[1]) : '',
        show_all: dateRange.value ? '' : 'true'
      }

      // 添加内容搜索参数
      if (contentSearchText.value) {
        searchParams.search_content = contentSearchText.value
      }

      // 根据聊天类型选择合适的API
      const selectedChat = chatList.value.find(chat => chat.chat_id === chatId)
      if (selectedChat && selectedChat.group_type === 0) {
        // 私人聊天使用专用API
        response = await chatHistoryApi.getByPrivateChat(chatId, searchParams)
      } else {
        // 群组聊天使用原有API
        response = await chatHistoryApi.getByGroupId(chatId, searchParams)
      }
      
      if (response.data.err_code === 0) {
        const payload = response.data.payload
        totalMessages.value = payload.total_records
        
        // 转换聊天消息数据格式（后端已按时间排序）
        messageList.value = payload.data.map((msg: ChatMessage) => ({
          id: msg.id,
          chatId: msg.chat_id,
          senderName: msg.nickname || msg.username,
          nickname: msg.nickname,
          username: msg.username,
          user_id: msg.user_id,
          avatar: buildAvatarUrl(msg.user_avatar || ''),
          content: determineMainMessageType(msg) === 'image' ? buildImageUrl(msg.photo_paths[0]) : (msg.message || ''),
          type: determineMainMessageType(msg),
          fileName: getFileName(msg.document_paths),
          time: formatTime(msg.postal_time),
          rawTime: msg.postal_time,
          isSelf: false,
          is_key_focus: msg.is_key_focus || false,
          photo_paths: msg.photo_paths || [],
          document_paths: msg.document_paths || [],
          documents: msg.documents || [],
          reply_to_msg_id: msg.reply_to_msg_id || 0,
          // 新增混合内容支持
          textContent: hasTextContent(msg) ? msg.message : undefined,
          images: hasImageContent(msg) ? [
            // 原有的photo_paths
            ...msg.photo_paths.filter(path => path).map(path => buildImageUrl(path)),
            // 图片类型的documents
            ...getImageDocuments(msg).map(doc => buildImageUrl(doc.path))
          ] : [],
          files: hasFileContent(msg) ? (() => {
            const files = []
            // 获取非图片类型的文档（自动处理新旧格式兼容性）
            const nonImageDocs = getNonImageDocuments(msg)
            
            
            files.push(...nonImageDocs.map(doc => {
              const fileType = getFileType(doc)
              
              // 检查是否为sticker文件
              if (doc.is_sticker) {
                const displayText = doc.display_text || '【动画表情】'
                return {
                  name: displayText,
                  displayName: displayText,
                  isSticker: true,
                  fileType: 'sticker',
                  fileSize: doc.file_size || 0
                }
              }
              
              // 对于其他文件类型，使用原始文件名和大小
              const fileName = doc.path ? doc.path.split('/').pop() || doc.path : doc.filename_origin || ''
              const displayName = doc.filename_origin || fileName
              
              // 检查是否有视频缩略图
              let videoThumbnail = ''
              if (fileType === 'video') {
                // 只有后端返回了确定的缩略图路径才使用
                if (doc.video_thumb_path) {
                  videoThumbnail = buildImageUrl(doc.video_thumb_path)
                }
                // 不再自动生成可能不存在的缩略图路径
              }
              
              return {
                name: fileName,
                displayName: displayName,
                isSticker: false,
                fileType: fileType,
                fileSize: doc.file_size || 0,
                videoThumbnail: videoThumbnail
              }
            }))
            
            
            return files
          })() : []
        }))
      } else {
        if (response.data.err_code === 40101) {
          ElMessage.error('请先登录系统')
        } else {
          ElMessage.error(response.data.err_msg || '获取聊天记录失败')
        }
      }
    }
  } catch (error: any) {
    console.error('获取聊天记录失败:', error)
    if (error.response?.status === 401) {
      ElMessage.error('请先登录系统')
    } else if (error.response?.status === 404) {
      // 对于404错误，显示更友好的提示，并清空消息列表
      messageList.value = []
      totalMessages.value = 0
      // 检查是否为私人聊天
      const selectedChat = chatList.value.find(chat => chat.id === selectedChatId.value)
      if (selectedChat && selectedChat.group_type === 0) {
        ElMessage.info('该私人聊天暂无完整记录，可能尚未同步')
      } else {
        ElMessage.warning('该聊天暂无记录或已被删除')
      }
    } else {
      ElMessage.error('获取聊天记录失败')
    }
  } finally {
    messageLoading.value = false
  }
}

// 获取特定页码的消息（用于计算总数）
const fetchMessagesForPage = async (chatId: string, page: number) => {
  try {
    let response: any
    
    // 检查是否是按用户ID搜索
    if (userIdSearchText.value) {
      const userId = userIdSearchText.value.trim()
      if (!userId) {
        return
      }
      
      const searchParams: any = {
        page: page,
        page_size: pageSize.value,
        start_date: dateRange.value ? formatDateForApi(dateRange.value[0]) : '',
        end_date: dateRange.value ? formatDateForApi(dateRange.value[1]) : ''
      }
      
      response = await chatHistoryApi.getByUserInGroup(chatId, userId, searchParams)
    } else {
      // 常规搜索
      const searchParams: any = {
        page: page,
        page_size: pageSize.value,
        start_date: dateRange.value ? formatDateForApi(dateRange.value[0]) : '',
        end_date: dateRange.value ? formatDateForApi(dateRange.value[1]) : '',
        show_all: dateRange.value ? '' : 'true'
      }

      if (contentSearchText.value) {
        searchParams.search_content = contentSearchText.value
      }

      // 根据聊天类型选择合适的API
      const selectedChat = chatList.value.find(chat => chat.chat_id === chatId)
      if (selectedChat && selectedChat.group_type === 0) {
        // 私人聊天使用专用API
        response = await chatHistoryApi.getByPrivateChat(chatId, searchParams)
      } else {
        // 群组聊天使用原有API
        response = await chatHistoryApi.getByGroupId(chatId, searchParams)
      }
    }
    
    if (response.data.err_code === 0) {
      const payload = response.data.payload
      totalMessages.value = payload.total_records
      // 只更新总数，不更新消息列表
    }
  } catch (error: any) {
    if (error.response?.status === 404) {
      // 404错误通常表示私人聊天没有对应的聊天记录端点
      totalMessages.value = 0
      // 检查是否为私人聊天
      const selectedChat = chatList.value.find(chat => chat.id === selectedChatId.value)
      if (selectedChat && selectedChat.group_type === 0) {
        ElMessage.info('该私人聊天暂无完整记录，请稍后重试')
      } else {
        ElMessage.info('该聊天暂无记录或正在同步中')
      }
    } else {
      console.error('获取消息数量失败:', error)
      ElMessage.error('获取聊天记录失败，请稍后重试')
    }
  }
}


// 检查消息内容类型的辅助函数
const hasTextContent = (msg: ChatMessage): boolean => {
  return !!(msg.message && msg.message.trim())
}

// 判断文件是否为图片类型（优先使用MIME类型，回退到扩展名判断）
const isImageFile = (doc: DocumentInfo): boolean => {
  
  // 如果是sticker，应该被当作文件处理而不是图片
  if (doc.is_sticker) {
    return false
  }
  
  // 优先使用MIME类型判断
  if (doc.mime_type) {
    const result = doc.mime_type.startsWith('image/')
    return result
  }
  
  // 回退到扩展名判断（向后兼容）
  const imageExtensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg', 'ico', 'tiff', 'tif']
  const result = imageExtensions.includes(doc.ext.toLowerCase().replace('.', ''))
  return result
}

// 判断文件类型
const getFileType = (doc: DocumentInfo): string => {
  // 动画表情
  if (doc.is_sticker) {
    return 'sticker'
  }
  
  // 优先使用MIME类型判断
  if (doc.mime_type) {
    if (doc.mime_type.startsWith('video/')) {
      return 'video'
    } else if (doc.mime_type.startsWith('audio/')) {
      return 'audio'
    } else if (doc.mime_type.startsWith('image/')) {
      return 'image'
    }
  }
  
  // 回退到扩展名判断
  const ext = doc.ext.toLowerCase().replace('.', '')
  
  // 视频文件
  if (['mp4', 'mkv', 'webm', 'mov', 'avi', 'wmv', 'flv', 'asf', 'rm', 'rmvb', '3gp'].includes(ext)) {
    return 'video'
  }
  
  // 音频文件
  if (['mp3', 'flac', 'wav', 'ogg', 'aac', 'm4a', 'wma'].includes(ext)) {
    return 'audio'
  }
  
  // 压缩文件
  if (['zip', 'rar', '7z', 'gz', 'bz2', 'tar', 'xz', 'lzma'].includes(ext)) {
    return 'archive'
  }
  
  // 文档文件
  if (['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'rtf', 'odt'].includes(ext)) {
    return 'document'
  }
  
  // 程序文件
  if (['apk', 'exe', 'msi', 'deb', 'rpm', 'dmg', 'elf', 'app'].includes(ext)) {
    return 'program'
  }
  
  // 其他类型
  return 'other'
}

// 格式化文件大小
const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 从document_paths中提取图片类型的文档（向后兼容）
const getImageDocumentsFromLegacy = (msg: ChatMessage): DocumentInfo[] => {
  if (!msg.document_paths || msg.document_paths.length === 0) return []
  return msg.document_paths
    .filter(path => path && path.trim())
    .map(path => {
      const pathParts = path.split('.')
      const ext = pathParts.length > 1 ? pathParts[pathParts.length - 1] : ''
      return { path: path.trim(), ext, mime_type: '' }
    })
    .filter(doc => isImageFile(doc))
}

// 从documents中提取图片类型的文档
const getImageDocuments = (msg: ChatMessage): DocumentInfo[] => {
  if (!msg.documents || msg.documents.length === 0) {
    // 如果没有新的documents字段，尝试从旧的document_paths中提取图片
    return getImageDocumentsFromLegacy(msg)
  }
  return msg.documents.filter(doc => isImageFile(doc))
}

// 从document_paths中提取非图片类型的文档（向后兼容）
const getNonImageDocumentsFromLegacy = (msg: ChatMessage): DocumentInfo[] => {
  if (!msg.document_paths || msg.document_paths.length === 0) return []
  return msg.document_paths
    .filter(path => path && path.trim())
    .map(path => {
      const pathParts = path.split('.')
      const ext = pathParts.length > 1 ? pathParts[pathParts.length - 1] : ''
      return { path: path.trim(), ext, mime_type: '' }
    })
    .filter(doc => !isImageFile(doc))
}

// 从documents中提取非图片类型的文档  
const getNonImageDocuments = (msg: ChatMessage): DocumentInfo[] => {
  
  if (!msg.documents || msg.documents.length === 0) {
    // 如果没有新的documents字段，尝试从旧的document_paths中提取非图片文档
    const legacyResult = getNonImageDocumentsFromLegacy(msg)
    return legacyResult
  }
  
  const result = msg.documents.filter(doc => !isImageFile(doc))
  
  return result
}

const hasImageContent = (msg: ChatMessage): boolean => {
  const hasPhotos = !!(msg.photo_paths && msg.photo_paths.length > 0 && msg.photo_paths[0])
  const hasImageDocs = getImageDocuments(msg).length > 0
  return hasPhotos || hasImageDocs
}

const hasFileContent = (msg: ChatMessage): boolean => {
  // 统一检查非图片类型的文档（自动处理新旧格式）
  return getNonImageDocuments(msg).length > 0
}

// 判断消息的主要类型（用于向后兼容和搜索结果显示）
const determineMainMessageType = (msg: ChatMessage): 'text' | 'image' | 'file' | 'mixed' => {
  const hasText = hasTextContent(msg)
  const hasImage = hasImageContent(msg)
  const hasFile = hasFileContent(msg)
  
  // 计算内容类型数量
  const contentTypes = [hasText, hasImage, hasFile].filter(Boolean).length
  
  if (contentTypes > 1) {
    return 'mixed'  // 混合类型
  } else if (hasImage) {
    return 'image'
  } else if (hasFile) {
    return 'file'
  } else {
    return 'text'
  }
}

// 获取文件名
const getFileName = (documentPaths: string[]): string => {
  if (documentPaths && documentPaths.length > 0 && documentPaths[0]) {
    const path = documentPaths[0]
    return path.split('/').pop() || path
  }
  return ''
}

// 计算属性
const filteredChats = computed(() => {
  if (!searchText.value) {
    return chatList.value
  }
  return chatList.value.filter(chat => 
    chat.name.toLowerCase().includes(searchText.value.toLowerCase()) ||
    chat.title.toLowerCase().includes(searchText.value.toLowerCase()) ||
    chat.remark.toLowerCase().includes(searchText.value.toLowerCase())
  )
})

// 新增：按类型分组的聊天列表，过滤掉私人聊天和消息数为0的群组
const groupedChats = computed(() => {
  const groups = {
    private: [] as Chat[],
    group: [] as Chat[],
    channel: [] as Chat[]
  }

  filteredChats.value.forEach(chat => {
    // 跳过私人聊天（group_type === 0）和消息数为0的群组
    if (chat.records_count > 0) {
      if (chat.group_type === 1) {
        groups.group.push(chat)
      } else if (chat.group_type === 2) {
        groups.channel.push(chat)
      }
    }
    // 移除了 group_type === 0 的处理，不再显示私人聊天
  })

  return groups
})

const selectedChat = computed(() => {
  return chatList.value.find(chat => chat.id === selectedChatId.value)
})

const allChats = computed(() => {
  return chatList.value.map(chat => ({
    chat_id: chat.chat_id,
    name: chat.name,
    title: chat.title
  }))
})

// 搜索处理函数
const handleContentSearch = async () => {
  const selectedChat = chatList.value.find(chat => chat.id === selectedChatId.value)
  if (selectedChat) {
    currentPage.value = 1
    await fetchMessagesForPage(selectedChat.chat_id, 1)
  }
}

const handleUserIdSearch = async () => {
  if (!userIdSearchText.value.trim()) {
    ElMessage.warning('请输入用户ID')
    return
  }

  const selectedChat = chatList.value.find(chat => chat.id === selectedChatId.value)
  if (!selectedChat) {
    ElMessage.warning('请先选择一个聊天')
    return
  }

  userIdSearchLoading.value = true
  try {
    currentPage.value = 1
    await fetchMessages(selectedChat.chat_id)
  } finally {
    userIdSearchLoading.value = false
  }
}

const handleUserIdClear = async () => {
  const selectedChat = chatList.value.find(chat => chat.id === selectedChatId.value)
  if (selectedChat) {
    // 清空用户ID搜索后重新加载正常消息
    await selectChat(selectedChat.id)
  }
}

// 字符串哈希函数
const stringHashCode = (str: string): number => {
  let hash = 0
  if (str.length === 0) return hash
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i)
    hash = ((hash << 5) - hash) + char
    hash = hash & hash // 转为32位整数
  }
  return Math.abs(hash)
}

// 获取私人聊天列表 - 已禁用，不再显示私人聊天
/*
const fetchPrivateChats = async (existingGroupChatIds: string[]): Promise<Chat[]> => {
  try {
    // 使用通用API获取所有聊天记录，然后筛选私人聊天
    const response = await chatHistoryApi.getList({
      page: 1,
      page_size: 1000,
      show_all: 'true'
    })
    
    if (response.data.err_code !== 0) {
      return []
    }
    
    // 提取私人聊天数据并去重
    const privateChats = new Map<string, Chat>()
    const potentialPrivateChats = new Map<string, any>() // 临时存储可能的私聊
    const messages = response.data.payload.data || []
    
    // 第一步：收集所有可能的私聊信息
    for (const msg of messages) {
      // 改进私人聊天检测逻辑：
      // 1. chat_id不在已知群组列表中
      // 2. chat_id与user_id相同（最可靠的私聊标识）
      // 3. 排除系统消息（777000是Telegram官方通知）
      const isPrivateChat = !existingGroupChatIds.includes(msg.chat_id) && 
        msg.chat_id === msg.user_id && // 只有当chat_id与user_id完全匹配时才认为是私聊
        msg.chat_id !== '777000' && // 排除Telegram官方通知
        msg.chat_id !== '0' && // 排除无效ID
        msg.user_id && msg.user_id !== '0' // 确保有有效的用户ID
      
      if (isPrivateChat && msg.user_id && msg.chat_id) {
        const chatId = msg.chat_id
        if (!potentialPrivateChats.has(chatId)) {
          potentialPrivateChats.set(chatId, {
            id: parseInt(chatId) || stringHashCode(chatId),
            name: msg.nickname || msg.username || `用户${msg.user_id}`,
            title: msg.nickname || msg.username || `用户${msg.user_id}`,
            avatar: buildAvatarUrl(msg.user_avatar || ''),
            lastMessage: msg.message || '[无文本内容]',
            lastTime: formatTime(msg.postal_time),
            memberCount: 2, // 私人聊天固定为2人
            status: 'active',
            chat_id: chatId,
            desc: '私人聊天',
            tag: '',
            remark: `与 ${msg.nickname || msg.username || msg.user_id} 的私聊`,
            photo: msg.user_avatar || '',
            group_type: 0 // 0表示私人聊天
          })
        } else {
          // 更新最后消息时间（保持最新）
          const existing = potentialPrivateChats.get(chatId)!
          const existingTime = new Date(existing.lastTime || '1970-01-01')
          const newTime = new Date(msg.postal_time || '1970-01-01')
          if (newTime > existingTime) {
            existing.lastMessage = msg.message || '[无文本内容]'
            existing.lastTime = formatTime(msg.postal_time)
          }
        }
      }
    }
    
    // 第二步：直接添加所有检测到的私聊
    
    // 直接添加所有私聊到界面
    for (const [chatId, chatInfo] of potentialPrivateChats) {
      chatInfo.hasValidHistory = true // 数据库中存在即有效
      chatInfo.remark = `与 ${chatInfo.name} 的私聊`
      privateChats.set(chatId, chatInfo)
    }
    
    // 兼容旧逻辑：处理已存在私聊的更新
    for (const msg of messages) {
      const isPrivateChat = !existingGroupChatIds.includes(msg.chat_id) && 
        msg.chat_id === msg.user_id && 
        msg.chat_id !== '777000' && 
        msg.chat_id !== '0' && 
        msg.user_id && msg.user_id !== '0'
      
      if (isPrivateChat && msg.user_id && msg.chat_id) {
        const chatId = msg.chat_id
        if (privateChats.has(chatId)) {
          // 更新最后消息时间（保持最新）
          const existing = privateChats.get(chatId)!
          const existingTime = new Date(existing.lastTime || '1970-01-01')
          const newTime = new Date(msg.postal_time || '1970-01-01')
          
          if (newTime > existingTime) {
            existing.lastMessage = msg.message || '[无文本内容]'
            existing.lastTime = formatTime(msg.postal_time)
            // 也更新用户信息，以防昵称等发生变化
            existing.name = msg.nickname || msg.username || existing.name
            existing.title = msg.nickname || msg.username || existing.title
            existing.avatar = buildAvatarUrl(msg.user_avatar || existing.photo)
          }
        }
      }
    }
    
    // 按最后消息时间倒序排列私人聊天
    const sortedChats = Array.from(privateChats.values()).sort((a, b) => {
      const timeA = new Date(a.lastTime || '1970-01-01').getTime()
      const timeB = new Date(b.lastTime || '1970-01-01').getTime()
      return timeB - timeA // 倒序：最新的在前
    })
    
    return sortedChats
  } catch (error) {
    console.error('获取私人聊天失败:', error)
    return []
  }
}
*/


// 方法
const selectChat = async (chatId: number) => {
  selectedChatId.value = chatId
  
  // 清空之前的消息列表
  messageList.value = []
  
  // 根据chatId获取对应的chat_id
  const selectedChat = chatList.value.find(chat => chat.id === chatId)
  if (selectedChat) {
    // 先获取第1页数据来计算总页数
    await fetchMessagesForPage(selectedChat.chat_id, 1)
    
    // 计算最后一页并跳转
    const lastPage = Math.ceil(totalMessages.value / pageSize.value)
    if (lastPage > 1) {
      currentPage.value = lastPage
      await fetchMessages(selectedChat.chat_id)
    } else {
      currentPage.value = 1
    }
  }
}

const handlePageChange = (page: number) => {
  currentPage.value = page
  const selectedChat = chatList.value.find(chat => chat.id === selectedChatId.value)
  if (selectedChat) {
    fetchMessages(selectedChat.chat_id)
  }
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  const selectedChat = chatList.value.find(chat => chat.id === selectedChatId.value)
  if (selectedChat) {
    fetchMessages(selectedChat.chat_id)
  }
}

// 工具栏方法
const handleDateChange = async (dates: [Date, Date] | null) => {
  dateRange.value = dates
  const selectedChat = chatList.value.find(chat => chat.id === selectedChatId.value)
  if (selectedChat) {
    // 重新计算分页
    await fetchMessagesForPage(selectedChat.chat_id, 1)
    
    // 对于用户ID搜索，跳转到第一页；其他情况跳转到最后一页
    if (userIdSearchText.value) {
      currentPage.value = 1
    } else {
      const lastPage = Math.ceil(totalMessages.value / pageSize.value)
      currentPage.value = Math.max(1, lastPage)
    }
    
    await fetchMessages(selectedChat.chat_id)
  }
}


const refreshData = async () => {
  try {
    // 先触发获取新的聊天历史
    const response = await chatHistoryApi.fetchNewHistory()
    
    if (response.data.err_code === 0) {
      ElMessage.success('聊天历史获取任务已启动，正在后台更新...')
    } else {
      ElMessage.warning(response.data.err_msg || '启动聊天历史获取任务失败')
    }
    
    // 然后刷新当前显示的数据
    fetchChatList()
  } catch (error: any) {
    console.error('启动聊天历史获取任务失败:', error)
    ElMessage.error('启动聊天历史获取任务失败')
    
    // 即使API调用失败，也刷新当前显示的数据
    fetchChatList()
  }
}

// 打开导出对话框
const exportMessages = () => {
  // 设置默认值
  const selectedChat = chatList.value.find(chat => chat.id === selectedChatId.value)
  if (selectedChat) {
    exportForm.chat_id = selectedChat.chat_id
  }
  
  // 如果当前有时间范围选择，设置为默认值
  if (dateRange.value) {
    exportForm.dateRange = [...dateRange.value] as [Date, Date]
  }
  
  showExportDialog.value = true
}

// 处理导出
const handleExport = async () => {
  if (!exportFormRef.value) return
  
  try {
    await exportFormRef.value.validate()
    exportLoading.value = true
    
    const selectedChat = allChats.value.find(chat => chat.chat_id === exportForm.chat_id)
    if (!selectedChat) {
      ElMessage.error('未找到选中的群组')
      return
    }
    
    // 格式化日期
    const formatDateForApi = (date: Date) => {
      return date.toISOString().split('T')[0]
    }
    
    const response = await chatHistoryApi.export({
      chat_id: exportForm.chat_id,
      start_time: exportForm.dateRange ? formatDateForApi(exportForm.dateRange[0]) : '',
      end_time: exportForm.dateRange ? formatDateForApi(exportForm.dateRange[1]) : '',
      get_photo: exportForm.get_photo
    })
    
    // 创建下载链接
    const blob = new Blob([response.data], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${selectedChat.title || selectedChat.name}_聊天记录.xlsx`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
    
    showExportDialog.value = false
    ElMessage.success('导出成功')
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败')
  } finally {
    exportLoading.value = false
  }
}

// 显示用户详情抽屉
const showUserDetail = (message: Message) => {
  // 简化：只传递user_id，让组件自己加载完整信息
  selectedUserId.value = message.user_id
  showUserDrawer.value = true
}

// 处理聊天搜索
const handleChatSearch = async () => {
  if (!searchKeyword.value.trim()) {
    ElMessage.warning('请输入搜索关键词')
    return
  }
  
  if (!selectedChat.value) {
    ElMessage.warning('请先选择一个群组')
    return
  }
  
  // 保存搜索历史
  saveSearchHistory(searchKeyword.value)
  showSearchHistory.value = false
  
  searchLoading.value = true
  currentSearchKeyword.value = searchKeyword.value
  
  try {
    const response = await chatHistoryApi.getByGroupId(selectedChat.value.chat_id, {
      page: 1,
      page_size: 100, // 搜索结果限制100条
      search_content: searchKeyword.value,
      show_all: 'true' // 搜索全部历史记录
    })
    
    if (response.data.err_code === 0) {
      const payload = response.data.payload
      
      // 转换搜索结果数据格式
      searchResults.value = payload.data.map((msg: ChatMessage) => ({
        id: msg.id,
        chatId: msg.chat_id,
        senderName: msg.nickname || msg.username,
        nickname: msg.nickname,
        username: msg.username,
        user_id: msg.user_id,
        avatar: buildAvatarUrl(msg.user_avatar || ''),
        content: determineMainMessageType(msg) === 'image' ? '[图片]' : (msg.message || ''),
        type: determineMainMessageType(msg),
        fileName: getFileName(msg.document_paths),
        time: formatTime(msg.postal_time),
        rawTime: msg.postal_time,
        isSelf: false,
        is_key_focus: msg.is_key_focus || false,
        photo_paths: msg.photo_paths || [],
        document_paths: msg.document_paths || [],
        reply_to_msg_id: msg.reply_to_msg_id || 0,
        // 新增混合内容支持
        textContent: hasTextContent(msg) ? msg.message : undefined,
        images: hasImageContent(msg) ? msg.photo_paths.filter(path => path).map(path => buildImageUrl(path)) : [],
        files: hasFileContent(msg) ? getNonImageDocuments(msg).map(doc => {
          const fileType = getFileType(doc)
          
          // 检查是否为sticker文件
          if (doc.is_sticker) {
            const displayText = doc.display_text || '【动画表情】'
            return {
              name: displayText,
              displayName: displayText,
              isSticker: true,
              fileType: 'sticker',
              fileSize: doc.file_size || 0
            }
          }
          
          // 对于其他文件类型，使用原始文件名和大小
          const fileName = doc.path ? doc.path.split('/').pop() || doc.path : doc.filename_origin || ''
          const displayName = doc.filename_origin || fileName
          
          // 检查是否有视频缩略图
          let videoThumbnail = ''
          if (fileType === 'video') {
            // 只有后端返回了确定的缩略图路径才使用
            if (doc.video_thumb_path) {
              videoThumbnail = buildImageUrl(doc.video_thumb_path)
            }
            // 不再自动生成可能不存在的缩略图路径
          }
          
          return {
            name: fileName,
            displayName: displayName,
            isSticker: false,
            fileType: fileType,
            fileSize: doc.file_size || 0,
            videoThumbnail: videoThumbnail
          }
        }) : []
      }))
      
      showSearchDrawer.value = true
      
      if (searchResults.value.length === 0) {
        ElMessage.info('未找到匹配的聊天记录')
      }
    } else {
      ElMessage.error(response.data.err_msg || '搜索失败')
    }
  } catch (error) {
    console.error('搜索失败:', error)
    ElMessage.error('搜索失败')
  } finally {
    searchLoading.value = false
  }
}

// 清空搜索
const clearChatSearch = () => {
  searchKeyword.value = ''
  currentSearchKeyword.value = ''
  searchResults.value = []
  showSearchDrawer.value = false
}

// 跳转到指定消息
const jumpToMessage = async (message: Message) => {
  try {
    // 关闭搜索抽屉
    showSearchDrawer.value = false
    
    // 检查消息是否在当前页面中
    const targetMessageIndex = messageList.value.findIndex(msg => msg.id === message.id)
    
    if (targetMessageIndex !== -1) {
      // 消息在当前页面，直接滚动到该消息
      const success = await scrollToMessage(message.id)
      if (success) {
        ElMessage.success(`已跳转到 ${message.senderName} 的消息`)
      }
    } else {
      // 消息不在当前页面，使用简化的搜索策略
      await findMessageAcrossPages(message)
    }
  } catch (error) {
    console.error('跳转到消息失败:', error)
    ElMessage.error('跳转失败，请重试')
  }
}

// 滚动到指定消息并高亮
const scrollToMessage = async (messageId: number) => {
  await nextTick()
  const targetElement = document.querySelector(`[data-message-id="${messageId}"]`)
  const chatMessagesContainer = document.querySelector('.chat-messages')
  
  if (targetElement && chatMessagesContainer) {
    // 计算目标元素在容器中的位置
    const containerRect = chatMessagesContainer.getBoundingClientRect()
    const targetRect = targetElement.getBoundingClientRect()
    
    // 计算需要滚动的距离（将目标消息滚动到容器中央）
    const containerCenter = containerRect.height / 2
    const targetRelativeTop = targetRect.top - containerRect.top + chatMessagesContainer.scrollTop
    const scrollToPosition = targetRelativeTop - containerCenter + targetRect.height / 2
    
    // 在聊天消息容器内平滑滚动
    chatMessagesContainer.scrollTo({
      top: scrollToPosition,
      behavior: 'smooth'
    })
    
    // 高亮消息
    targetElement.classList.add('highlight-message')
    setTimeout(() => {
      targetElement.classList.remove('highlight-message')
    }, 3000)
    return true
  }
  return false
}

// 高效的跨页面消息查找（使用后端计算页数）
const findMessageAcrossPages = async (targetMessage: Message) => {
  messageLoading.value = true
  
  try {
    // 检查是否有选中的群组
    if (!selectedChat.value) {
      ElMessage.warning('请先选择一个群组')
      return
    }
    
    const chatId = selectedChat.value.chat_id
    
    // 清除当前搜索状态
    contentSearchText.value = ''
    userIdSearchText.value = ''
    
    // 调用后端API查找消息所在的页数
    const response = await chatHistoryApi.findMessagePage(chatId, targetMessage.id, pageSize.value)
    
    if (response.data.err_code === 0) {
      const payload = response.data.payload
      const targetPageNumber = payload.page_number
      
      // 直接跳转到目标页面
      currentPage.value = targetPageNumber
      await fetchMessages(chatId)
      
      // 滚动到目标消息
      await nextTick()
      const success = await scrollToMessage(targetMessage.id)
      
      if (success) {
        ElMessage.success(`已跳转到 ${targetMessage.senderName} 的消息（第${targetPageNumber}页）`)
      } else {
        // 如果没有找到元素，可能是因为DOM还没更新，再试一次
        setTimeout(async () => {
          const retrySuccess = await scrollToMessage(targetMessage.id)
          if (retrySuccess) {
            ElMessage.success(`已跳转到 ${targetMessage.senderName} 的消息（第${targetPageNumber}页）`)
          } else {
            ElMessage.warning('消息定位失败，但已跳转到正确页面')
          }
        }, 500)
      }
    } else {
      // API返回错误
      if (response.data.err_code === 1 && response.status === 404) {
        ElMessage.warning('目标消息不存在或已被删除')
      } else {
        ElMessage.error(response.data.err_msg || '查找消息页数失败')
      }
      
      // 回到第一页
      currentPage.value = 1
      await fetchMessages(chatId)
    }
    
  } catch (error: any) {
    console.error('查找消息失败:', error)
    
    // 根据错误类型提供不同的提示
    if (error.response?.status === 404) {
      ElMessage.warning('目标消息不存在')
    } else if (error.response?.status >= 500) {
      ElMessage.error('服务器错误，请稍后重试')
    } else {
      ElMessage.error('查找消息失败')
    }
    
    // 恢复到第一页
    if (selectedChat.value) {
      currentPage.value = 1
      try {
        await fetchMessages(selectedChat.value.chat_id)
      } catch (e) {
        console.error('恢复页面失败:', e)
      }
    }
  } finally {
    messageLoading.value = false
  }
}

// 高亮关键词
const highlightKeyword = (content: string, keyword: string) => {
  if (!keyword || !content) return content
  
  const regex = new RegExp(`(${keyword})`, 'gi')
  return content.replace(regex, '<mark class="highlight">$1</mark>')
}

// 格式化搜索结果时间
const formatSearchTime = (timeString: string): string => {
  if (!timeString) return ''
  
  // 使用统一的UTC+8时间格式化函数，但只显示到分钟
  const formatted = formatUTCToLocal(timeString)
  // 截取前16位：YYYY/MM/DD HH:mm
  return formatted.substring(0, 16)
}

// 搜索历史管理方法
const loadSearchHistory = () => {
  try {
    const history = localStorage.getItem(SEARCH_HISTORY_KEY)
    if (history) {
      searchHistory.value = JSON.parse(history)
    }
  } catch (error) {
    console.warn('加载搜索历史失败:', error)
    searchHistory.value = []
  }
}

const saveSearchHistory = (keyword: string) => {
  if (!keyword.trim()) return
  
  // 去除重复项并添加到开头
  const newHistory = [keyword.trim(), ...searchHistory.value.filter(item => item !== keyword.trim())]
  
  // 限制只保存最近10条
  searchHistory.value = newHistory.slice(0, 10)
  
  // 保存到localStorage
  try {
    localStorage.setItem(SEARCH_HISTORY_KEY, JSON.stringify(searchHistory.value))
  } catch (error) {
    console.warn('保存搜索历史失败:', error)
  }
}

const clearSearchHistory = () => {
  searchHistory.value = []
  try {
    localStorage.removeItem(SEARCH_HISTORY_KEY)
  } catch (error) {
    console.warn('清除搜索历史失败:', error)
  }
}

const selectSearchHistory = (keyword: string) => {
  searchKeyword.value = keyword
  showSearchHistory.value = false
  handleChatSearch()
}

const handleSearchBlur = () => {
  // 延迟隐藏下拉，以便点击事件能够触发
  setTimeout(() => {
    showSearchHistory.value = false
  }, 200)
}

// 页面加载时的初始化
onMounted(() => {
  fetchChatList()
  loadSearchHistory()
  
  // 处理URL参数
  handleUrlParameters()
})

// 处理URL参数
const handleUrlParameters = () => {
  const urlGroupId = route.query.group_id as string
  const urlUserId = route.query.user_id as string
  const urlSearchType = route.query.search_type as string
  
  if (urlGroupId && urlUserId && urlSearchType === 'user_id') {
    // 设置用户ID搜索
    userIdSearchText.value = urlUserId
    
    // 等待群组列表加载完成后选择对应的群组
    const checkAndSelectGroup = () => {
      if (chatList.value.length > 0) {
        const targetGroup = chatList.value.find(chat => chat.chat_id === urlGroupId)
        if (targetGroup) {
          // 手动设置选中的聊天并执行用户ID搜索
          selectedChatId.value = targetGroup.id
          messageList.value = []
          currentPage.value = 1
          
          // 直接执行用户ID搜索
          fetchMessages(targetGroup.chat_id)
        } else {
          // 如果没找到群组，给出提示但不报错
          console.warn(`未找到群组 ID: ${urlGroupId}`)
        }
      } else {
        // 如果群组列表还没加载完，等待100ms再试
        setTimeout(checkAndSelectGroup, 100)
      }
    }
    
    checkAndSelectGroup()
  }
}

// 处理用户详情抽屉的导航事件
const handleNavigateToUserMessages = ({ groupId, userId }: { groupId: string, userId: string }) => {
  // 查找目标群组
  const targetGroup = chatList.value.find(chat => chat.chat_id === groupId)
  
  if (targetGroup) {
    // 设置用户ID搜索
    userIdSearchText.value = userId
    
    // 选择目标群组
    selectChat(targetGroup.id)
    
    ElMessage.success(`已切换到用户 ${userId} 在群组 "${targetGroup.title || targetGroup.name}" 的消息记录`)
  } else {
    ElMessage.warning('未找到目标群组')
  }
}
</script>


<style scoped>
.chat-content {
  height: 100%;
  padding: 0;
}

/* 工具栏样式 */
.chat-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  margin-bottom: 16px;
  min-height: 56px;
}

.toolbar-left {
  flex: 1;
  display: flex;
  align-items: center;
  max-width: 500px;
}

.toolbar-center {
  display: flex;
  align-items: center;
  gap: 20px;
  flex-shrink: 0;
}

.toolbar-right {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.date-filter,
.keyword-search {
  display: flex;
  align-items: center;
}

.search-boxes {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
}

.search-input-content,
.search-input-userid {
  flex: 1;
  min-width: 180px;
}



.chat-layout {
  display: flex;
  height: calc(100vh - 200px);
  min-height: 400px;
  gap: 16px;
}

/* 左侧面板样式 */
.left-panel {
  width: 25%;
  min-width: 300px;
}

.chat-list-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.chat-list-card :deep(.el-card__body) {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 16px;
  min-height: 0;
  overflow: hidden;
}

.card-header {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.search-input {
  width: 100%;
}

.chat-list {
  flex: 1;
  overflow-y: auto;
  min-height: 200px;
  max-height: calc(100vh - 350px);
}

.chat-item {
  display: flex;
  align-items: center;
  padding: 12px;
  cursor: pointer;
  border-radius: 8px;
  margin-bottom: 6px;
  transition: all 0.3s ease;
  position: relative;
  margin-left: 8px; /* 给分组项目添加缩进 */
}

.chat-item:hover {
  background-color: #f5f7fa;
}

.chat-item.active {
  background-color: #e6f7ff;
  border-left: 4px solid #1890ff;
}

.chat-avatar {
  margin-right: 12px;
}

.chat-info {
  flex: 1;
  min-width: 0;
}

.chat-name {
  font-weight: 500;
  font-size: 14px;
  color: #333;
  margin-bottom: 4px;
}

.chat-remark {
  font-weight: normal;
  color: #999;
  font-size: 12px;
}

.chat-last-message {
  font-size: 12px;
  color: #666;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 2px;
}

.chat-time {
  font-size: 11px;
  color: #999;
}

/* 聊天分组样式 */
.chat-group {
  margin-bottom: 16px;
}

.chat-group:last-child {
  margin-bottom: 0;
}

.chat-group-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background-color: #f5f7fa;
  border-radius: 6px;
  margin-bottom: 8px;
  font-size: 12px;
  font-weight: 600;
  color: #666;
  border-left: 3px solid #1890ff;
}

.chat-group-header .el-icon {
  font-size: 14px;
  color: #1890ff;
}

/* 聊天类型指示器 */
.chat-avatar {
  position: relative;
  margin-right: 12px;
}

.chat-type-indicator {
  position: absolute;
  bottom: -2px;
  right: -2px;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 2px solid #fff;
  z-index: 10;
}

.chat-type-indicator.private {
  background-color: #f56c6c; /* 私聊红色 */
}

.chat-type-indicator.group {
  background-color: #409eff; /* 群组蓝色 */
}

.chat-type-indicator.channel {
  background-color: #67c23a; /* 频道绿色 */
}
.chat-type-indicator.invalid {
  background-color: #c0c4cc; /* 无效聊天灰色 */
}
.chat-type-indicator.validating {
  background-color: #e6a23c; /* 验证中橙色 */
}

/* 状态指示器样式 */
.status-indicator {
  position: absolute;
  top: -5px;
  right: -5px;
  width: 16px;
  height: 16px;
  background-color: #f56c6c;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid #fff;
  z-index: 15;
}

.status-indicator .el-icon {
  color: #fff;
  font-size: 10px;
}

.status-indicator.validating {
  background-color: #e6a23c; /* 验证中橙色 */
}

/* 旋转动画 */
.rotating {
  animation: rotate 1s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 无历史记录的聊天项样式 */
.chat-item.no-history {
  opacity: 0.7;
  background-color: #f8f9fa;
}

.chat-item.no-history:hover {
  background-color: #e9ecef;
}

.chat-title {
  font-weight: 500;
  color: #333;
}

.empty-chat-list {
  padding: 40px 20px;
  text-align: center;
}


/* 右侧面板样式 */
.right-panel {
  width: 75%;
  position: relative;
}

.chat-detail-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.chat-detail-card :deep(.el-card__body) {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 0;
}

.chat-header {
  display: flex;
  align-items: center;
  flex-shrink: 0;
  padding: 16px 20px;
  background-color: #fff;
}

.chat-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.title-name {
  font-weight: 500;
  font-size: 16px;
  color: #333;
}

.title-remark {
  font-weight: normal;
  color: #999;
  font-size: 14px;
}

.title-status {
  font-size: 12px;
  color: #666;
}

.no-selection {
  color: #999;
  font-size: 14px;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 16px;
  background-color: #f5f7fa;
  background-repeat: no-repeat;
  background-position: center center;
  background-size: cover;
  background-attachment: fixed;
  min-height: 0;
  max-height: calc(100vh - 300px);
  position: relative;
  height: calc(100vh - 300px);
}

.message-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 100%;
  padding-bottom: 20px;
}

.message-item {
  display: flex;
  gap: 12px;
  min-height: 60px;
  margin-bottom: 8px;
  transition: all 0.3s ease;
}

.message-item.highlight-message {
  background-color: #fff7e6;
  border: 2px solid #ffa940;
  border-radius: 8px;
  padding: 8px;
  margin: 4px 0;
  box-shadow: 0 2px 8px rgba(255, 169, 64, 0.3);
}

.message-item.message-self {
  flex-direction: row-reverse;
}

.message-item.message-self .message-content {
  background-color: #1890ff;
  color: white;
}

.message-item.message-self .message-header {
  flex-direction: row-reverse;
}

.message-content {
  max-width: 60%;
  background-color: #f5f7fa;
  border-radius: 12px;
  padding: 12px;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  gap: 12px;
}

.sender-name {
  font-weight: 500;
  font-size: 13px;
}

.sender-name.key-focus {
  color: #f56c6c;
  font-weight: 700;
}

.message-time {
  font-size: 11px;
  opacity: 0.7;
}

.message-body {
  line-height: 1.4;
}

.text-message {
  word-break: break-word;
}

.image-message {
  margin-top: 8px;
}

.image-grid {
  display: grid;
  gap: 4px;
  max-width: 300px;
}

.image-grid.images-1 {
  grid-template-columns: 1fr;
}

.image-grid.images-2 {
  grid-template-columns: 1fr 1fr;
}

.image-grid.images-3 {
  grid-template-columns: 1fr 1fr 1fr;
}

.image-grid.images-4 {
  grid-template-columns: 1fr 1fr;
}

.message-image {
  width: 100%;
  height: 100px;
  border-radius: 8px;
  cursor: pointer;
}

.image-grid.images-1 .message-image {
  height: 150px;
}

.image-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100px;
  background-color: #f8f9fa;
  border-radius: 8px;
  color: #6c757d;
  font-size: 12px;
}

.image-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100px;
  background-color: #f5f5f5;
  border-radius: 8px;
  color: #999;
  font-size: 12px;
}

.more-images {
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgba(0, 0, 0, 0.6);
  color: white;
  border-radius: 8px;
  font-size: 14px;
  font-weight: bold;
  cursor: pointer;
}

.file-message {
  margin-top: 8px;
}

.file-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 8px;
  background-color: rgba(0, 0, 0, 0.05);
  border-radius: 6px;
  margin-bottom: 4px;
}

.file-item:has(.file-video-with-thumbnail) {
  align-items: stretch;
  padding: 12px;
}

.file-item:last-child {
  margin-bottom: 0;
}

.file-video-with-thumbnail {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 8px;
}

.video-thumbnail-wrapper {
  display: flex;
  justify-content: center;
  width: 100%;
  position: relative;
}

.video-thumbnail {
  max-width: 100%;
  height: auto;
  border-radius: 6px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.video-overlay-icon {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 32px;
  color: white;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
  pointer-events: none;
}

.file-type-icon {
  font-size: 20px;
  flex-shrink: 0;
}

.file-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.file-name {
  word-break: break-all;
  font-size: 14px;
  line-height: 1.2;
}

.file-size {
  font-size: 12px;
  color: #999;
  opacity: 0.8;
}

.empty-message {
  height: 100%;
  min-height: calc(100vh - 400px);
  display: flex;
  align-items: center;
  justify-content: center;
}

.message-pagination {
  padding: 16px 20px;
  display: flex;
  justify-content: center;
  border-top: 1px solid #f0f0f0;
  flex-shrink: 0;
  background-color: #fff;
  position: sticky;
  bottom: 0;
  z-index: 100;
}

/* 滚动条样式 */
.chat-list::-webkit-scrollbar,
.chat-messages::-webkit-scrollbar {
  width: 8px;
}

.chat-list::-webkit-scrollbar-track,
.chat-messages::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.chat-list::-webkit-scrollbar-thumb,
.chat-messages::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}

.chat-list::-webkit-scrollbar-thumb:hover,
.chat-messages::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* 确保在所有浏览器中都显示滚动条 */
.chat-messages {
  scrollbar-width: thin;
  scrollbar-color: #c1c1c1 #f1f1f1;
}

/* 自定义加载遮罩层 */
.custom-loading-mask {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(2px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
  border-radius: 8px;
}

.loading-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  color: #409eff;
  font-size: 14px;
}

.loading-content .el-icon {
  font-size: 28px;
  animation: rotate 2s linear infinite;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* 头像点击样式 */
.message-avatar {
  cursor: pointer;
  transition: all 0.3s ease;
}

.message-avatar:hover {
  transform: scale(1.05);
}

.clickable-avatar {
  transition: all 0.3s ease;
}

.clickable-avatar:hover {
  border: 2px solid #1890ff;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.3);
}


/* 聊天搜索样式 */
.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
  padding: 16px 20px;
  background-color: #fff;
}

.chat-search {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 300px;
}

.search-container {
  position: relative;
  min-width: 200px;
}

.chat-search .search-input {
  min-width: 200px;
}

/* 搜索历史下拉框样式 */
.search-history-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: #fff;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  z-index: 2000;
  margin-top: 4px;
}

.search-history-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: #f5f7fa;
  border-bottom: 1px solid #ebeef5;
  font-size: 12px;
  color: #909399;
}

.clear-history-btn {
  color: #909399;
  font-size: 12px;
  padding: 0;
}

.clear-history-btn:hover {
  color: #f56c6c;
}

.search-history-list {
  max-height: 200px;
  overflow-y: auto;
}

.search-history-item {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.search-history-item:hover {
  background-color: #f5f7fa;
}

.history-icon {
  font-size: 12px;
  color: #c0c4cc;
  margin-right: 8px;
}

.history-text {
  font-size: 13px;
  color: #606266;
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 搜索结果抽屉样式 */
.search-results-drawer {
  padding: 20px;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.search-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 6px;
}

.search-summary {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.search-keyword {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.result-count {
  font-size: 12px;
  color: #666;
}

.search-results {
  flex: 1;
  overflow-y: auto;
}

.empty-results {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.result-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.result-item {
  padding: 12px;
  border: 1px solid #f0f0f0;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: #fff;
}

.result-item:hover {
  border-color: #1890ff;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.15);
}

.result-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.result-header .sender-name {
  font-size: 13px;
  font-weight: 500;
  color: #333;
}

.result-header .sender-name.key-focus {
  color: #f56c6c;
  font-weight: 700;
}

.result-header .message-time {
  font-size: 11px;
  color: #999;
  margin-left: auto;
}

.result-content {
  font-size: 14px;
  color: #666;
  line-height: 1.4;
  margin-bottom: 8px;
  word-break: break-word;
}

.result-content :deep(.highlight) {
  background-color: #fff566;
  color: #000;
  padding: 1px 2px;
  border-radius: 2px;
  font-weight: 600;
}

.result-meta {
  display: flex;
  justify-content: flex-end;
}

</style>