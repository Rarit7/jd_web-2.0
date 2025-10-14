<template>
  <div class="tg-users">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>Telegram用户管理</span>
          <div class="header-actions">
            <el-button @click="downloadData">下载数据</el-button>
          </div>
        </div>
      </template>
      
      <!-- 搜索区域 -->
      <div class="search-area">
        <el-form :model="searchForm" inline class="search-form">
          <!-- 第一行：关键字搜索和操作按钮 -->
          <div class="search-row">
            <el-form-item label="关键字" class="search-keyword">
              <div class="search-input-group">
                <el-input 
                  v-model="searchForm.keyword" 
                  placeholder="搜索昵称、用户名、备注..." 
                  clearable 
                  style="width: 300px"
                  @keyup.enter="handleSearch"
                  @clear="handleSearch"
                />
                <el-button type="primary" @click="handleSearch" class="search-button">
                  <el-icon><Search /></el-icon>
                </el-button>
              </div>
            </el-form-item>
          </div>
          
          <!-- 第二行：筛选条件 -->
          <div class="filter-row">
            <el-form-item label="群组" class="filter-group">
              <el-select 
                v-model="searchForm.group_id" 
                placeholder="选择群组" 
                clearable 
                style="width: 200px"
                @change="handleSearch"
              >
                <el-option label="全部群组" value="" />
                <el-option 
                  v-for="group in groupList" 
                  :key="group.id" 
                  :label="group.name" 
                  :value="group.id" 
                />
              </el-select>
            </el-form-item>
            
            <el-form-item label="标签" class="filter-tags">
              <el-select 
                v-model="searchForm.tag_ids" 
                placeholder="选择标签" 
                multiple 
                clearable 
                collapse-tags 
                collapse-tags-tooltip 
                style="width: 250px"
                @change="handleSearch"
              >
                <el-option 
                  v-for="tag in availableTagsForFilter" 
                  :key="tag.id" 
                  :label="tag.name" 
                  :value="String(tag.id)"
                >
                  <span class="tag-option-item">
                    <el-tag :color="tag.color" effect="dark" size="small" style="color: white; border: none; margin-right: 8px;">
                      {{ tag.name }}
                    </el-tag>
                  </span>
                </el-option>
              </el-select>
            </el-form-item>
            
            
            <el-form-item class="filter-focus">
              <el-switch 
                v-model="showOnlyKeyFocus" 
                @change="handleKeyFocusFilterChange"
                active-text="只显示重点关注" 
                style="--el-switch-on-color: #f56c6c"
              />
            </el-form-item>
          </div>
        </el-form>
      </div>

      <!-- 用户表格区域 -->
      <div class="table-area">
        <div class="table-container">
          <el-table 
            :data="userList" 
            v-loading="loading"
            :max-height="tableMaxHeight"
            stripe
            highlight-current-row
            empty-text="暂无用户数据"
            row-key="id"
            style="width: 100%; cursor: pointer;"
            @row-click="handleRowClick"
          >
              <el-table-column type="index" width="60" label="#" />
              
              <el-table-column prop="avatar" label="头像" width="80" align="center">
                <template #default="{ row }">
                  <el-avatar 
                    :size="40" 
                    :src="row.avatar ? `/static/${row.avatar}` : ''"
                    shape="circle"
                  >
                    <el-icon><Avatar /></el-icon>
                  </el-avatar>
                </template>
              </el-table-column>
              
              <el-table-column prop="name" label="用户名" min-width="150" show-overflow-tooltip>
                <template #default="{ row }">
                  <div class="user-name-cell">
                    <span :class="{ 'key-focus': row.is_key_focus }">
                      {{ row.nickname || row.first_name || row.username || '未知' }}
                    </span>
                    <div v-if="row.username" class="username-sub">@{{ row.username }}</div>
                  </div>
                </template>
              </el-table-column>
              
              <el-table-column prop="user_id" label="用户ID" width="120" show-overflow-tooltip>
                <template #default="{ row }">
                  <span class="user-id-text">{{ row.user_id }}</span>
                </template>
              </el-table-column>
              
              <el-table-column prop="notes" label="备注" min-width="120" show-overflow-tooltip>
                <template #default="{ row }">
                  <span class="notes-text">{{ row.notes || '-' }}</span>
                </template>
              </el-table-column>
              
              <el-table-column prop="tags" label="标签" min-width="150">
                <template #default="{ row }">
                  <div class="tags-cell">
                    <el-tag 
                      v-for="tag in (row.tags || '').split(',').filter((t: string) => t.trim())" 
                      :key="tag" 
                      size="small"
                      :color="getTagColor(tag.trim())"
                      effect="dark"
                      style="color: white; border: none; margin-right: 4px; margin-bottom: 2px;"
                    >
                      {{ tag.trim() }}
                    </el-tag>
                  </div>
                </template>
              </el-table-column>
              
              <el-table-column prop="group_name" label="群组" min-width="180" show-overflow-tooltip>
                <template #default="{ row }">
                  <div v-if="row.groups && row.groups.length > 0" class="groups-cell">
                    <span
                      v-for="(group, index) in row.groups"
                      :key="group.chat_id"
                      class="group-link"
                      @click.stop="navigateToGroupChatHistory(row, group, $event)"
                      :title="'点击查看此用户在「' + group.name + '」的聊天记录'"
                    >
                      {{ group.name }}<span v-if="index < row.groups.length - 1">, </span>
                    </span>
                  </div>
                  <span v-else>-</span>
                </template>
              </el-table-column>
              
              <el-table-column prop="updated_at" label="最近修改" width="120" show-overflow-tooltip>
                <template #default="{ row }">
                  <span class="activity-time">{{ formatLastActiveTime(row.updated_at) }}</span>
                </template>
              </el-table-column>
              
              <el-table-column prop="status" label="状态" width="80" align="center">
                <template #default="{ row }">
                  <el-tag :type="getStatusType(row.status)" size="small">
                    {{ row.status === 'active' ? '活跃' : '非活跃' }}
                  </el-tag>
                </template>
              </el-table-column>
              
              <el-table-column label="操作" width="100" align="center" fixed="right">
                <template #default="{ row }">
                  <el-button 
                    :type="row.is_key_focus ? 'warning' : 'primary'" 
                    size="small" 
                    :icon="row.is_key_focus ? StarFilled : Star"
                    @click.stop="toggleFocus(row)"
                    :loading="focusLoading"
                    circle
                    :title="row.is_key_focus ? '取消重点关注' : '列入重点关注'"
                  />
                </template>
              </el-table-column>
            </el-table>
        </div>
        
        <!-- 分页组件 -->
        <div class="pagination-container">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="total"
            layout="total, sizes, prev, pager, next, jumper"
            background
            @size-change="handleSizeChange"
            @current-change="handlePageChange"
          />
        </div>
      </div>
    </el-card>

    <!-- 编辑用户对话框 -->
    <el-dialog v-model="showEditDialog" title="编辑用户信息" width="450px">
      <el-form :model="editForm" ref="editFormRef">
        <el-form-item label="备注">
          <el-input 
            v-model="editForm.notes" 
            type="textarea" 
            rows="3" 
            placeholder="请输入备注" 
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="标签">
          <div class="tag-selection">
            <div class="selected-tags" v-if="editForm.selectedTags.length > 0">
              <el-tag 
                v-for="tag in editForm.selectedTags" 
                :key="tag.id" 
                :color="tag.color" 
                effect="dark" 
                style="color: white; border: none; margin-right: 8px; margin-bottom: 8px;"
                closable
                @close="removeTag(tag.id)"
              >
                {{ tag.name }}
              </el-tag>
            </div>
            <div class="available-tags">
              <div class="tag-label">可选标签：</div>
              <div class="tag-options">
                <el-tag 
                  v-for="tag in availableTags" 
                  :key="tag.id" 
                  :color="tag.color" 
                  effect="dark"
                  class="tag-option"
                  style="color: white; border: none;"
                  @click="addTag(tag)"
                >
                  {{ tag.name }}
                </el-tag>
              </div>
            </div>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="updateUser" :loading="editLoading">保存</el-button>
      </template>
    </el-dialog>

    <!-- 用户详情抽屉 -->
    <UserDetailDrawer 
      :visible="showUserDrawer"
      :userDetail="selectedUser"
      :currentGroupId="selectedUser?.chat_id"
      @update:visible="showUserDrawer = $event"
      @navigate-to-user-messages="handleNavigateToGroup"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, nextTick, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance } from 'element-plus'
import { Edit, Star, StarFilled, Search } from '@element-plus/icons-vue'
import { tgUsersApi, type TgUser } from '@/api/tg-users'
import { tagsApi, type Tag } from '@/api/tags'
import { useRouter } from 'vue-router'
import { getRelativeTime, formatUTCToLocal } from '@/utils/date'
import UserDetailDrawer from '@/components/UserDetailDrawer.vue'

// Router实例
const router = useRouter()

// 响应式数据
const loading = ref(false)
const editLoading = ref(false)
const focusLoading = ref(false)
const showEditDialog = ref(false)
const userList = ref<TgUser[]>([])
const originalUserList = ref<TgUser[]>([]) // 原始完整用户数据备份
// 移除重点关注用户缓存，使用统一的分页逻辑
const tagList = ref<any[]>([])
const tagColorMap = ref(new Map<string, string>())
// 移除选中用户相关逻辑

// 表格容器引用
// const cardContainerRef = ref<HTMLElement | null>(null)

// 表格高度计算
const tableMaxHeight = ref(400)

// 分页数据
const currentPage = ref(1)
const pageSize = ref(20)  // 每页显示20条数据
const total = ref(0)

// 表单引用
const editFormRef = ref<FormInstance>()

// 搜索表单
const searchForm = reactive({
  keyword: '',
  group_id: '',
  tag_ids: [] as string[]
})

// 群组列表和标签列表
const groupList = ref<any[]>([])
const availableTagsForFilter = ref<any[]>([])

// 排序相关
const sortType = ref('last_active_desc') // 默认按最后发言日期降序

// 重点关注过滤
const showOnlyKeyFocus = ref(false) // 默认关闭

// 用户详情抽屉状态
const showUserDrawer = ref(false)
const selectedUser = ref<any | null>(null)

// 编辑表单
const editForm = reactive({
  id: 0,
  username: '',
  nickname: '',
  notes: '',
  selectedTags: [] as any[]
})


// 获取标签颜色映射
const fetchTagColors = async () => {
  try {
    const response = await tagsApi.getList()
    if (response.err_code === 0) {
      tagList.value = response.payload.data
      availableTagsForFilter.value = response.payload.data
      const colorMap = new Map<string, string>()
      response.payload.data.forEach((tag: Tag) => {
        colorMap.set(tag.name, tag.color)
      })
      tagColorMap.value = colorMap
    }
  } catch (error) {
    console.error('获取标签颜色失败:', error)
  }
}

// 获取群组列表
const fetchGroupList = async () => {
  try {
    const { tgGroupsApi } = await import('@/api/tg-groups')
    const response = await tgGroupsApi.getList()
    
    if (response.data.err_code === 0) {
      // 只获取成功加入的群组
      const joinedGroups = response.data.payload.data.filter(group => group.status === '已加入')
      groupList.value = joinedGroups.map(group => ({
        id: group.chat_id,
        name: group.title || group.name,
        chat_id: group.chat_id
      }))
      console.log('群组列表加载成功:', groupList.value.length, '个群组')
    } else {
      console.error('获取群组列表失败:', response.data.err_msg)
      groupList.value = []
    }
  } catch (error) {
    console.error('获取群组列表失败:', error)
    groupList.value = []
  }
}

// 可选标签（未被选中的标签）
const availableTags = computed(() => {
  return tagList.value.filter(tag => 
    !editForm.selectedTags.some(selected => selected.id === tag.id)
  )
})

// 添加标签
const addTag = (tag: any) => {
  if (!editForm.selectedTags.some(selected => selected.id === tag.id)) {
    editForm.selectedTags.push(tag)
  }
}

// 移除标签
const removeTag = (tagId: number) => {
  const index = editForm.selectedTags.findIndex(tag => tag.id === tagId)
  if (index > -1) {
    editForm.selectedTags.splice(index, 1)
  }
}

// 获取标签颜色
const getTagColor = (tagName: string): string => {
  return tagColorMap.value.get(tagName) || '#409EFF'
}


// 获取数据
const fetchData = async () => {
  loading.value = true
  
  try {
    const response = await tgUsersApi.getList({
      keyword: searchForm.keyword,
      group_id: searchForm.group_id,
      tag_ids: searchForm.tag_ids.join(','),
      page: currentPage.value,
      page_size: pageSize.value
    })
    
    if (response.data.err_code === 0) {
      const newData = response.data.payload.data || []
      const totalCount = response.data.payload.total || 0
      
      userList.value = newData
      originalUserList.value = [...newData] // 保存原始数据
      total.value = totalCount
      
      // 应用过滤和排序
      applyFiltersAndSort()
      
    } else {
      ElMessage.error(response.data.err_msg || '获取数据失败')
      userList.value = []
      total.value = 0
    }
  } catch (error) {
    console.error('获取数据失败:', error)
    ElMessage.error('获取数据失败')
    userList.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

// 分页变化处理
const handlePageChange = (page: number) => {
  currentPage.value = page
  if (showOnlyKeyFocus.value) {
    fetchKeyFocusUsers()
  } else {
    fetchData()
  }
}

// 每页大小变化处理
const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  if (showOnlyKeyFocus.value) {
    fetchKeyFocusUsers()
  } else {
    fetchData()
  }
}


// 搜索
const handleSearch = async () => {
  currentPage.value = 1
  
  if (showOnlyKeyFocus.value) {
    // 如果开启了重点关注过滤，搜索重点关注用户
    await fetchKeyFocusUsers()
  } else {
    // 否则正常搜索
    fetchData()
  }
}


// 处理重点关注过滤开关变更
const handleKeyFocusFilterChange = async () => {
  currentPage.value = 1
  
  if (showOnlyKeyFocus.value) {
    // 如果开关打开，从后端获取所有重点关注用户
    await fetchKeyFocusUsers()
  } else {
    // 如果开关关闭，重新获取完整的用户数据
    await fetchData()
  }
}

// 获取UTC时间的时间戳用于比较
const getUTCTimestamp = (dateTimeString: string): number => {
  if (!dateTimeString) return 0
  // 数据库存储的是UTC时间，添加Z后缀确保正确解析
  const utcString = dateTimeString.endsWith('Z') ? dateTimeString : dateTimeString + 'Z'
  return new Date(utcString).getTime()
}

// 排序用户列表
const sortUserList = () => {
  if (userList.value.length === 0) return
  
  userList.value.sort((a, b) => {
    switch (sortType.value) {
      case 'last_active_desc':
        // 按最后发言日期降序（最新的在前）
        return getUTCTimestamp(b.updated_at || '') - getUTCTimestamp(a.updated_at || '')
      
      case 'last_active_asc':
        // 按最后发言日期升序（最旧的在前）
        return getUTCTimestamp(a.updated_at || '') - getUTCTimestamp(b.updated_at || '')
      
      case 'name_asc':
        // 按首字母升序（A-Z）
        const nameA = (a.nickname || a.first_name || a.username || '').toLowerCase()
        const nameB = (b.nickname || b.first_name || b.username || '').toLowerCase()
        return nameA.localeCompare(nameB, 'zh-CN')
      
      case 'name_desc':
        // 按首字母降序（Z-A）
        const nameA2 = (a.nickname || a.first_name || a.username || '').toLowerCase()
        const nameB2 = (b.nickname || b.first_name || b.username || '').toLowerCase()
        return nameB2.localeCompare(nameA2, 'zh-CN')
      
      default:
        return 0
    }
  })
}

// 获取重点关注用户（使用分页）
const fetchKeyFocusUsers = async () => {
  loading.value = true
  try {
    const response = await tgUsersApi.getKeyFocusList({
      keyword: searchForm.keyword,
      group_id: searchForm.group_id,
      tag_ids: searchForm.tag_ids.join(','),
      page: currentPage.value,
      page_size: pageSize.value
    })
    
    if (response.data.err_code === 0) {
      const keyFocusData = response.data.payload.data || []
      const totalCount = response.data.payload.total || 0
      
      // 设置当前显示列表为重点关注用户
      userList.value = keyFocusData
      originalUserList.value = [...keyFocusData]
      
      // 使用后端返回的总数进行分页
      total.value = totalCount
      
      // 应用排序
      sortUserList()
      
    } else {
      ElMessage.error(response.data.err_msg || '获取重点关注用户失败')
      userList.value = []
      total.value = 0
    }
  } catch (error) {
    console.error('获取重点关注用户失败:', error)
    ElMessage.error('获取重点关注用户失败')
    userList.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

// 应用过滤和排序
const applyFiltersAndSort = () => {
  // 从原始数据开始
  let filteredList = [...originalUserList.value]
  
  // 应用重点关注过滤
  if (showOnlyKeyFocus.value) {
    filteredList = filteredList.filter(user => user.is_key_focus)
  }
  
  // 更新用户列表
  userList.value = filteredList
  
  // 应用排序
  sortUserList()
}

// 编辑用户
const editUser = (user: TgUser) => {
  editForm.id = user.id
  editForm.username = user.username
  editForm.nickname = user.nickname || ''
  editForm.notes = user.notes || ''
  
  // 根据用户的标签ID列表设置已选标签
  editForm.selectedTags = []
  if (user.tag_id_list) {
    const userTagIds = user.tag_id_list.split(',').map(Number)
    editForm.selectedTags = tagList.value.filter(tag => userTagIds.includes(tag.id))
  }
  
  showEditDialog.value = true
}

// 更新用户
const updateUser = async () => {
  editLoading.value = true
  try {
    const tagIds = editForm.selectedTags.map(tag => tag.id).join(',')
    await tgUsersApi.updateUser({
      tg_user_id: editForm.id,
      tag_id_list: tagIds,
      remark: editForm.notes
    })
    ElMessage.success('更新成功')
    showEditDialog.value = false
    // 根据当前模式刷新数据
    if (showOnlyKeyFocus.value) {
      fetchKeyFocusUsers()
    } else {
      fetchData()
    }
  } catch (error) {
    ElMessage.error('更新失败')
  } finally {
    editLoading.value = false
  }
}

// 切换关注状态
const toggleFocus = async (user: TgUser) => {
  try {
    // 如果是取关，显示确认框
    if (user.is_key_focus) {
      await ElMessageBox.confirm('确认取消关注?', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      })
    }
    
    focusLoading.value = true
    const response = await tgUsersApi.toggleFocus(user.id)
    
    if (response.data.err_code === 0) {
      // 更新用户状态
      user.is_key_focus = response.data.payload.is_key_focus
      
      // 同时更新原始数据中对应用户的状态
      const originalUser = originalUserList.value.find(u => u.id === user.id)
      if (originalUser) {
        originalUser.is_key_focus = response.data.payload.is_key_focus
      }
      
      // 如果当前显示重点关注用户且用户被取消关注，需要重新加载数据
      if (showOnlyKeyFocus.value && !response.data.payload.is_key_focus) {
        // 重新获取重点关注用户数据
        await fetchKeyFocusUsers()
      } else {
        // 重新应用过滤和排序
        applyFiltersAndSort()
      }
      
      ElMessage.success(response.data.payload.message)
    } else {
      ElMessage.error(response.data.err_msg || '操作失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败')
    }
  } finally {
    focusLoading.value = false
  }
}

// 移除用户详情相关方法

// 下载数据
const downloadData = async () => {
  try {
    ElMessage.success('下载功能开发中')
  } catch (error) {
    ElMessage.error('下载失败')
  }
}

// 获取状态类型
const getStatusType = (status: string) => {
  switch (status) {
    case 'active':
      return 'success'
    case 'inactive':
      return 'danger'
    default:
      return 'info'
  }
}

// 获取表格行类名
const getRowClassName = ({ row }: { row: TgUser }) => {
  let className = ''
  if (row.is_key_focus) {
    className += 'key-focus-row '
  }
  return className.trim()
}

// 格式化最近活跃时间
const formatLastActiveTime = (dateTime: string): string => {
  if (!dateTime) return '未知'
  
  try {
    return getRelativeTime(dateTime)
  } catch (error) {
    return '未知'
  }
}

// 跳转到聊天历史页面 - 用于特定群组
const navigateToGroupChatHistory = (user: TgUser, group: { chat_id: string; name: string }, event?: Event) => {
  console.log('=== Group Link Click Debug ===')
  console.log('Event:', event)
  console.log('Navigation triggered for user:', user.user_id, 'in group:', group.name)

  if (!group.chat_id || !user.user_id) {
    console.log('Missing data - chat_id:', group.chat_id, 'user_id:', user.user_id)
    ElMessage.warning('缺少必要的群组或用户信息')
    return
  }

  console.log('Navigating with group_id:', group.chat_id, 'user_id:', user.user_id)

  // 构建路由参数
  router.push({
    path: '/chat-history',
    query: {
      group_id: group.chat_id,
      user_id: user.user_id,
      search_type: 'user_id'
    }
  })
}

// 跳转到聊天历史页面 - 旧方法保留以防兼容性问题
const navigateToChatHistory = (user: TgUser, event?: Event) => {
  console.log('=== Group Link Click Debug ===')
  console.log('Event:', event)
  console.log('Navigation triggered for user:', JSON.stringify(user, null, 2))
  console.log('User keys:', Object.keys(user))
  console.log('User chat_id type:', typeof user.chat_id, 'value:', user.chat_id)
  console.log('User user_id type:', typeof user.user_id, 'value:', user.user_id)
  console.log('User group_name:', user.group_name)

  // 如果没有chat_id，尝试使用其他字段
  const groupId = user.chat_id || user.id?.toString()

  if (!groupId || !user.user_id) {
    console.log('Missing data - chat_id/groupId:', groupId, 'user_id:', user.user_id)
    ElMessage.warning('缺少必要的群组或用户信息')
    return
  }

  console.log('Navigating with group_id:', groupId, 'user_id:', user.user_id)

  // 构建路由参数
  router.push({
    path: '/chat-history',
    query: {
      group_id: groupId,
      user_id: user.user_id,
      search_type: 'user_id'
    }
  })
}

// 转换TgUser为UserInfo格式
const convertTgUserToUserInfo = (tgUser: TgUser) => {
  return {
    id: tgUser.id,
    senderName: tgUser.nickname || tgUser.first_name || tgUser.username || '未知',
    nickname: tgUser.nickname || '',
    username: tgUser.username || '',
    user_id: tgUser.user_id,
    avatar: tgUser.avatar ? `/static/${tgUser.avatar}` : '',
    is_key_focus: tgUser.is_key_focus,
    bio: tgUser.bio || '',
    remark: tgUser.notes || '',
    chat_id: tgUser.chat_id // 添加chat_id字段
  }
}

// 处理表格行点击事件
const handleRowClick = (row: TgUser, column: any, event: Event) => {
  console.log('=== Row Click Debug ===')
  console.log('Row click triggered:', row)
  console.log('Column:', column)
  console.log('Event target:', event.target)
  
  // 检查是否点击的是群组链接
  const target = event.target as HTMLElement
  if (target.classList.contains('group-link')) {
    console.log('Clicked on group link, preventing row click')
    return
  }
  
  selectedUser.value = convertTgUserToUserInfo(row)
  showUserDrawer.value = true
}

// 处理从用户详情抽屉导航到群组
const handleNavigateToGroup = (data: { groupId: string, userId: string }) => {
  console.log('=== Drawer Group Navigation Debug ===')
  console.log('Navigation data:', data)
  
  // 关闭抽屉
  showUserDrawer.value = false
  
  // 跳转到聊天历史页面
  router.push({
    path: '/chat-history',
    query: {
      group_id: data.groupId,
      user_id: data.userId,
      search_type: 'user_id'
    }
  })
}

// 计算表格高度
// const calculateTableHeight = () => {
//   nextTick(() => {
//     // 计算可用高度：视窗高度 - 卡片头部 - 搜索区域 - 分页区域 - 边距
//     const cardHeader = 70 // 卡片头部高度
//     const searchArea = 160 // 搜索区域高度（包括边距）
//     const pagination = 80 // 分页区域高度
//     const padding = 60 // 内边距和其他空间
//     const available = window.innerHeight - cardHeader - searchArea - pagination - padding
//     tableHeight.value = Math.max(300, available) // 最小300px
//   })
// }

// 窗口大小变化监听
// const handleResize = () => {
//   calculateTableHeight()
// }

// 计算表格最大高度
const calculateTableMaxHeight = () => {
  nextTick(() => {
    // 计算可用高度：视窗高度 - 卡片头部 - 搜索区域 - 分页区域 - 边距
    const windowHeight = window.innerHeight
    const cardHeaderHeight = 70 // 卡片头部高度
    const searchAreaHeight = 180 // 搜索区域高度（包括边距）
    const paginationHeight = 80 // 分页区域高度
    const padding = 40 // 内边距和其他空间
    
    const availableHeight = windowHeight - cardHeaderHeight - searchAreaHeight - paginationHeight - padding
    tableMaxHeight.value = Math.max(300, availableHeight) // 最小300px
  })
}

// 窗口大小变化监听
const handleResize = () => {
  calculateTableMaxHeight()
}

// 页面加载时获取数据
onMounted(() => {
  // 防止页面滚动，只允许表格内容滚动
  document.body.style.overflow = 'hidden'
  
  fetchTagColors()  // 获取标签颜色和标签列表
  fetchGroupList()  // 获取群组列表
  fetchData()       // 初始加载用户数据
  calculateTableMaxHeight() // 计算表格高度
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  // 恢复页面滚动
  document.body.style.overflow = 'auto'
  window.removeEventListener('resize', handleResize)
})

</script>


<style lang="scss" scoped>
.tg-users {
  height: 100vh;
  padding: 0;
  margin: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.tg-users > .el-card {
  width: 100%;
  flex: 1;
  margin: 0;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.tg-users > .el-card > .el-card__body {
  padding: 20px;
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
}

/* 表格区域布局 */
.table-area {
  margin-top: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

.table-container {
  flex: 1;
  border-radius: 8px 8px 0 0;
  border: 1px solid #e4e7ed;
  border-bottom: none;
  margin-bottom: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* 移除右侧详情面板相关样式 */


.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.search-area {
  margin-bottom: 16px;
  padding: 20px;
  background-color: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  flex-shrink: 0;
  overflow: visible;
}

.search-form {
  .search-row {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: 16px;
    
    .search-keyword {
      flex: 1;
      margin-right: 0;
    }
    
  }
  
  .filter-row {
    display: flex;
    align-items: center;
    gap: 16px;
    flex-wrap: wrap;
    
    .el-form-item {
      margin-right: 0;
      margin-bottom: 8px;
    }
    
    .filter-group,
    .filter-tags {
      margin-right: 16px;
    }
    
    .filter-focus {
      margin-left: auto;
    }
  }
}

/* 搜索输入组样式 */
.search-input-group {
  display: flex;
  align-items: center;
  gap: 0;
}
.search-button {
  margin-left: -1px;
  border-top-left-radius: 0;
  border-bottom-left-radius: 0;
  height: 32px;
  padding: 0 12px;
  z-index: 1;
}
.search-input-group .el-input .el-input__wrapper {
  border-top-right-radius: 0;
  border-bottom-right-radius: 0;
}

.tag-option-item {
  display: flex;
  align-items: center;
}

/* 响应式搜索区域 */
@media (max-width: 1200px) {
  .search-form {
    .search-row {
      flex-wrap: wrap;
    }
    
    .filter-row {
      justify-content: flex-start;
      
      .filter-focus {
        margin-left: 0;
        order: -1;
        width: 100%;
        margin-bottom: 12px;
      }
    }
  }
}


.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 300px;
}

/* 表格样式 */
:deep(.el-table) {
  height: 100%;
  display: flex;
  flex-direction: column;
  
  .el-table__header-wrapper {
    flex-shrink: 0;
    overflow: visible !important;
  }
  
  .el-table__body-wrapper {
    flex: 1;
    overflow-y: auto !important;
    overflow-x: hidden;
  }
  
  .el-table__fixed-header-wrapper {
    overflow: visible !important;
  }
}

/* 表格行样式 */
:deep(.key-focus-row .user-name-cell .key-focus) {
  color: #f56c6c !important;
  font-weight: 700 !important;
}

/* 表格行悬停效果 */
:deep(.el-table__body-wrapper .el-table__row) {
  cursor: pointer;
  transition: background-color 0.2s ease;
}

:deep(.el-table__body-wrapper .el-table__row:hover) {
  background-color: #f5f7fa !important;
}

/* 表格单元格样式 */
.user-name-cell {
  .key-focus {
    color: #f56c6c;
    font-weight: 700;
  }
  
  .username-sub {
    font-size: 12px;
    color: #909399;
    margin-top: 2px;
  }
}

.user-id-text {
  font-family: monospace;
  font-size: 12px;
  color: #606266;
}

.notes-text {
  font-size: 13px;
  color: #606266;
}

.tags-cell {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.groups-cell {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  line-height: 1.6;
}

.group-link {
  color: #1890ff !important;
  cursor: pointer;
  transition: all 0.3s ease;
  text-decoration: underline;
  white-space: nowrap;

  &:hover {
    color: #40a9ff !important;
  }
}

.activity-time {
  font-size: 12px;
  color: #909399;
}




/* 分页组件样式 */
.pagination-container {
  display: flex !important;
  justify-content: center;
  align-items: center;
  padding: 16px 20px;
  border-top: 1px solid #e4e7ed;
  background-color: #fafafa;
  border-radius: 0 0 8px 8px;
  border-left: 1px solid #e4e7ed;
  border-right: 1px solid #e4e7ed;
  border-bottom: 1px solid #e4e7ed;
  min-height: 60px;
  width: 100%;
  flex-shrink: 0;
}

.focus-users-total {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 16px 20px;
  color: #606266;
  font-size: 14px;
  background-color: #f5f7fa;
  border-top: 1px solid #e4e7ed;
  border-left: 1px solid #e4e7ed;
  border-right: 1px solid #e4e7ed;
  border-bottom: 1px solid #e4e7ed;
  border-radius: 0 0 8px 8px;
  flex-shrink: 0; /* 防止容器被压缩 */
  min-height: 60px; /* 确保最小高度 */
}

/* 标签选择样式 */
.tag-selection {
  .selected-tags {
    margin-bottom: 16px;
    padding: 12px;
    background-color: #f8f9fa;
    border-radius: 6px;
    border: 1px solid #e4e7ed;
  }

  .available-tags {
    .tag-label {
      font-size: 14px;
      color: #606266;
      margin-bottom: 8px;
      font-weight: 500;
    }

    .tag-options {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }

    .tag-option {
      cursor: pointer;
      transition: all 0.2s ease;

      &:hover {
        transform: scale(1.05);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
      }
    }
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .search-area .el-form {
    flex-direction: column;
  }
  
  .search-area .el-form-item {
    margin-right: 0;
    margin-bottom: 16px;
  }
}
</style>