<template>
  <div class="change-record">
    <div class="layout-container">
      <!-- 左栏 -->
      <div class="left-column">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>变动筛选</span>
            </div>
          </template>
          
          <div class="filter-content">
            <el-form :model="filterForm" inline>
              <el-form-item label="变动类型">
                <el-select
                  v-model="filterForm.changeType"
                  placeholder="选择变动类型"
                  clearable
                  style="width: 200px"
                  @change="handleFilterChange"
                >
                  <el-option label="全部" :value="0" />
                  <el-option label="显示名称" :value="1" />
                  <el-option label="用户名" :value="2" />
                  <el-option label="头像" :value="3" />
                  <el-option label="个人简介" :value="4" />
                </el-select>
              </el-form-item>
            </el-form>
            <!-- 显示当前筛选的用户ID -->
            <div v-if="urlUserId" class="current-filter">
              <el-tag type="info" size="small">
                筛选用户: {{ urlUserId }}
              </el-tag>
            </div>
            <!-- 去重说明 -->
            <div class="dedup-notice">
              <el-tag type="success" size="small" effect="plain">
                <el-icon><InfoFilled /></el-icon>
                已自动去重：相同变动仅显示最新记录
              </el-tag>
            </div>
          </div>
        </el-card>
      </div>
      
      <!-- 右栏 -->
      <div class="right-column">
        <el-card>
          <div class="tabs-content">
            <el-tabs v-model="activeTab" type="card">
              <el-tab-pane label="用户信息变动" name="user">
                <div class="tab-content">
                  <div class="table-wrapper">
                    <el-table 
                      :data="userChangeData" 
                      style="width: 100%" 
                      stripe
                      :max-height="tableMaxHeight"
                      :header-cell-style="{ backgroundColor: '#f5f7fa', color: '#606266', textAlign: 'center' }"
                      v-loading="userLoading"
                    >
                      <el-table-column prop="user_id" label="用户ID" width="120" align="center" />
                      <el-table-column prop="change_type_text" label="变动类型" width="120" align="center" />
                      <el-table-column label="变动前" min-width="200" align="center">
                        <template #default="scope">
                          <div v-if="scope.row.changed_fields === 3" class="avatar-cell">
                            <div v-if="!scope.row.original_value" class="empty-avatar">
                              <el-icon :size="24" color="#c0c4cc">
                                <Avatar />
                              </el-icon>
                              <span class="empty-text">无头像</span>
                            </div>
                            <img 
                              v-else
                              :src="formatAvatarUrl(scope.row.original_value)" 
                              alt="原头像" 
                              class="avatar-img clickable" 
                              @click="previewImage(formatAvatarUrl(scope.row.original_value))"
                              title="点击查看原图"
                              @error="handleImageError"
                            />
                          </div>
                          <div v-else class="text-cell" :class="{ 'username-cell': scope.row.changed_fields === 2 }">
                            <span v-if="scope.row.changed_fields === 2">@</span>{{ scope.row.original_value || '(空)' }}
                          </div>
                        </template>
                      </el-table-column>
                      <el-table-column label="" width="60" align="center">
                        <template #default>
                          <el-icon color="#409EFF" size="18">
                            <ArrowRight />
                          </el-icon>
                        </template>
                      </el-table-column>
                      <el-table-column label="变动后" min-width="200" align="center">
                        <template #default="scope">
                          <div v-if="scope.row.changed_fields === 3" class="avatar-cell">
                            <div v-if="!scope.row.new_value" class="empty-avatar">
                              <el-icon :size="24" color="#c0c4cc">
                                <Avatar />
                              </el-icon>
                              <span class="empty-text">无头像</span>
                            </div>
                            <img 
                              v-else
                              :src="formatAvatarUrl(scope.row.new_value)" 
                              alt="新头像" 
                              class="avatar-img clickable" 
                              @click="previewImage(formatAvatarUrl(scope.row.new_value))"
                              title="点击查看原图"
                              @error="handleImageError"
                            />
                          </div>
                          <div v-else class="text-cell" :class="{ 'username-cell': scope.row.changed_fields === 2 }">
                            <span v-if="scope.row.changed_fields === 2">@</span>{{ scope.row.new_value || '(空)' }}
                          </div>
                        </template>
                      </el-table-column>
                      <el-table-column prop="update_time" label="变动时间" width="180" align="center">
                        <template #default="scope">
                          {{ formatUTCToLocal(scope.row.update_time) }}
                        </template>
                      </el-table-column>
                    </el-table>
                  </div>
                  
                  <!-- 分页 -->
                  <div class="pagination-wrapper">
                    <el-pagination
                      v-model:current-page="userPagination.page"
                      v-model:page-size="userPagination.size"
                      :page-sizes="[10, 20, 50, 100]"
                      :total="userPagination.total"
                      layout="total, sizes, prev, pager, next, jumper"
                      @size-change="handleUserSizeChange"
                      @current-change="handleUserCurrentChange"
                    />
                  </div>
                </div>
              </el-tab-pane>
              <el-tab-pane label="群组信息变动" name="group">
                <div class="tab-content">
                  <div class="table-wrapper">
                    <el-table 
                      :data="groupChangeData" 
                      style="width: 100%" 
                      stripe
                      :max-height="tableMaxHeight"
                      :header-cell-style="{ backgroundColor: '#f5f7fa', color: '#606266', textAlign: 'center' }"
                      v-loading="groupLoading"
                    >
                      <el-table-column prop="group_id" label="群组ID" width="120" align="center" />
                      <el-table-column prop="change_type_text" label="变动类型" width="120" align="center" />
                      <el-table-column label="变动前" min-width="200" align="center">
                        <template #default="scope">
                          <div v-if="scope.row.changed_fields === 3" class="avatar-cell">
                            <div v-if="!scope.row.original_value" class="empty-avatar">
                              <el-icon :size="24" color="#c0c4cc">
                                <Avatar />
                              </el-icon>
                              <span class="empty-text">无头像</span>
                            </div>
                            <img 
                              v-else
                              :src="formatAvatarUrl(scope.row.original_value)" 
                              alt="原头像" 
                              class="avatar-img clickable" 
                              @click="previewImage(formatAvatarUrl(scope.row.original_value))"
                              title="点击查看原图"
                              @error="handleImageError"
                            />
                          </div>
                          <div v-else class="text-cell">{{ scope.row.original_value || '(空)' }}</div>
                        </template>
                      </el-table-column>
                      <el-table-column label="" width="60" align="center">
                        <template #default>
                          <el-icon color="#409EFF" size="18">
                            <ArrowRight />
                          </el-icon>
                        </template>
                      </el-table-column>
                      <el-table-column label="变动后" min-width="200" align="center">
                        <template #default="scope">
                          <div v-if="scope.row.changed_fields === 3" class="avatar-cell">
                            <div v-if="!scope.row.new_value" class="empty-avatar">
                              <el-icon :size="24" color="#c0c4cc">
                                <Avatar />
                              </el-icon>
                              <span class="empty-text">无头像</span>
                            </div>
                            <img 
                              v-else
                              :src="formatAvatarUrl(scope.row.new_value)" 
                              alt="新头像" 
                              class="avatar-img clickable" 
                              @click="previewImage(formatAvatarUrl(scope.row.new_value))"
                              title="点击查看原图"
                              @error="handleImageError"
                            />
                          </div>
                          <div v-else class="text-cell" :class="{ 'username-cell': scope.row.changed_fields === 2 }">
                            <span v-if="scope.row.changed_fields === 2">@</span>{{ scope.row.new_value || '(空)' }}
                          </div>
                        </template>
                      </el-table-column>
                      <el-table-column prop="update_time" label="变动时间" width="180" align="center">
                        <template #default="scope">
                          {{ formatUTCToLocal(scope.row.update_time) }}
                        </template>
                      </el-table-column>
                    </el-table>
                  </div>
                  
                  <!-- 分页 -->
                  <div class="pagination-wrapper">
                    <el-pagination
                      v-model:current-page="groupPagination.page"
                      v-model:page-size="groupPagination.size"
                      :page-sizes="[10, 20, 50, 100]"
                      :total="groupPagination.total"
                      layout="total, sizes, prev, pager, next, jumper"
                      @size-change="handleGroupSizeChange"
                      @current-change="handleGroupCurrentChange"
                    />
                  </div>
                </div>
              </el-tab-pane>
            </el-tabs>
          </div>
        </el-card>
      </div>
    </div>
    
    <!-- 图片预览 -->
    <el-image-viewer
      v-if="imagePreviewVisible"
      :url-list="[previewImageUrl]"
      @close="imagePreviewVisible = false"
      hide-on-click-modal
      teleported
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { ElMessage, ElImageViewer } from 'element-plus'
import { Avatar, ArrowRight, InfoFilled } from '@element-plus/icons-vue'
import { formatUTCToLocal } from '@/utils/date'
import { useRoute } from 'vue-router'

// 变动分析页面
const activeTab = ref('user')
const route = useRoute()

// 筛选表单
const filterForm = ref({
  changeType: 0
})

// URL参数中的用户ID（用于筛选特定用户的变动记录）
const urlUserId = ref('')

// 用户变动数据
const userChangeData = ref([])
const userLoading = ref(false)
const userPagination = ref({
  page: 1,
  size: 20,
  total: 0
})

// 群组变动数据
const groupChangeData = ref([])
const groupLoading = ref(false)
const groupPagination = ref({
  page: 1,
  size: 20,
  total: 0
})

// 变动类型映射
const changeTypeMap = {
  1: '显示名称',
  2: '用户名',
  3: '头像',
  4: '个人简介'
}

// 获取用户变动数据
const fetchUserChangeData = async () => {
  userLoading.value = true
  try {
    const params = new URLSearchParams({
      page: userPagination.value.page.toString(),
      size: userPagination.value.size.toString()
    })

    // 添加变动类型筛选
    if (filterForm.value.changeType > 0) {
      params.append('change_type', filterForm.value.changeType.toString())
    }

    // 添加用户ID筛选（如果URL中有user_id参数）
    if (urlUserId.value) {
      params.append('user_id', urlUserId.value)
    }

    const response = await fetch(`/api/change_record/user?${params}`)
    const result = await response.json()
    
    if (result.err_code === 0) {
      userChangeData.value = result.payload.items
      userPagination.value.total = result.payload.pagination.total
    } else {
      ElMessage.error(result.err_msg || '获取用户变动数据失败')
    }
    
  } catch (error) {
    ElMessage.error('获取用户变动数据失败')
    console.error(error)
  } finally {
    userLoading.value = false
  }
}

// 获取群组变动数据
const fetchGroupChangeData = async () => {
  groupLoading.value = true
  try {
    const params = new URLSearchParams({
      page: groupPagination.value.page.toString(),
      size: groupPagination.value.size.toString()
    })
    
    // 添加变动类型筛选
    if (filterForm.value.changeType > 0) {
      params.append('change_type', filterForm.value.changeType.toString())
    }
    
    const response = await fetch(`/api/change_record/group?${params}`)
    const result = await response.json()
    
    if (result.err_code === 0) {
      groupChangeData.value = result.payload.items
      groupPagination.value.total = result.payload.pagination.total
    } else {
      ElMessage.error(result.err_msg || '获取群组变动数据失败')
    }
    
  } catch (error) {
    ElMessage.error('获取群组变动数据失败')
    console.error(error)
  } finally {
    groupLoading.value = false
  }
}

// 用户分页处理
const handleUserSizeChange = (newSize: number) => {
  userPagination.value.size = newSize
  userPagination.value.page = 1
  fetchUserChangeData()
}

const handleUserCurrentChange = (newPage: number) => {
  userPagination.value.page = newPage
  fetchUserChangeData()
}

// 群组分页处理
const handleGroupSizeChange = (newSize: number) => {
  groupPagination.value.size = newSize
  groupPagination.value.page = 1
  fetchGroupChangeData()
}

const handleGroupCurrentChange = (newPage: number) => {
  groupPagination.value.page = newPage
  fetchGroupChangeData()
}

// 监听标签切换
watch(activeTab, (newTab) => {
  if (newTab === 'user') {
    fetchUserChangeData()
  } else if (newTab === 'group') {
    fetchGroupChangeData()
  }
})

// 图片预览状态
const imagePreviewVisible = ref(false)
const previewImageUrl = ref('')

// 格式化头像URL
const formatAvatarUrl = (url: string) => {
  if (!url) return ''
  // 如果已经是完整URL，直接返回
  if (url.startsWith('http') || url.startsWith('/static')) return url
  // 标准头像路径：images/avatar/xxx.jpg → /static/images/avatar/xxx.jpg
  if (url.startsWith('images/')) return `/static/${url}`
  // 其他情况，添加前缀
  return url.startsWith('/') ? url : `/${url}`
}

// 预览图片
const previewImage = (url: string) => {
  if (!url) return
  previewImageUrl.value = url
  imagePreviewVisible.value = true
}

// 图片加载错误处理
const handleImageError = (event: Event) => {
  const img = event.target as HTMLImageElement
  if (img) {
    img.style.display = 'none'
    // 可以在这里添加错误提示或替换为默认图片
    console.warn('头像加载失败:', img.src)
  }
}

// 筛选条件变更处理
const handleFilterChange = () => {
  // 重置分页到第一页
  userPagination.value.page = 1
  groupPagination.value.page = 1
  
  // 根据当前标签页重新加载数据
  if (activeTab.value === 'user') {
    fetchUserChangeData()
  } else {
    fetchGroupChangeData()
  }
}

// 计算表格最大高度
const calculateTableMaxHeight = () => {
  nextTick(() => {
    const windowHeight = window.innerHeight
    const cardHeaderHeight = 70 // 卡片头部高度
    const filterAreaHeight = 180 // 筛选区域高度（增加）
    const tabsHeaderHeight = 76 // 标签页头部高度
    const paginationHeight = 60 // 分页区域高度
    const padding = 40 // 内边距和其他空间
    
    const availableHeight = windowHeight - cardHeaderHeight - filterAreaHeight - tabsHeaderHeight - paginationHeight - padding
    tableMaxHeight.value = Math.max(300, availableHeight) // 最小300px
  })
}

// 表格最大高度
const tableMaxHeight = ref(400)

// 窗口大小变化监听
const handleResize = () => {
  calculateTableMaxHeight()
}

// 页面加载时获取数据
onMounted(() => {
  // 防止页面滚动，只允许表格内容滚动
  document.body.style.overflow = 'hidden'

  // 从URL参数中获取user_id
  urlUserId.value = route.query.user_id as string || ''

  fetchUserChangeData()
  calculateTableMaxHeight()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  // 恢复页面滚动
  document.body.style.overflow = 'auto'
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.change-record {
  height: 100vh;
  padding: 0;
  margin: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.layout-container {
  width: 100%;
  flex: 1;
  margin: 0;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.left-column {
  height: 160px;
  flex-shrink: 0;
  padding: 16px;
}

.right-column {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  padding: 0 16px 16px 16px;
}

.left-column .el-card,
.right-column .el-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.left-column .el-card > .el-card__body {
  padding: 20px;
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  overflow: hidden;
  min-height: 0;
}

.right-column .el-card > .el-card__body {
  padding: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 500;
  margin-bottom: 0;
}

.filter-content {
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  flex: 1;
  flex-direction: column;
  gap: 12px;
}

.current-filter {
  align-self: flex-start;
}

.dedup-notice {
  align-self: flex-start;

  .el-tag {
    display: inline-flex;
    align-items: center;
    gap: 4px;
  }
}

.tabs-content {
  height: 100%;
  overflow: hidden;
  padding: 0;
}

.tabs-content :deep(.el-tabs) {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.tabs-content :deep(.el-tabs__header) {
  margin: 0;
  padding: 20px 20px 16px 20px;
  min-height: 60px;
}

.tabs-content :deep(.el-tabs__nav-wrap) {
  padding: 0;
}

.tabs-content :deep(.el-tabs__item) {
  height: 40px;
  line-height: 40px;
  padding: 0 20px;
  font-size: 14px;
}

.tabs-content :deep(.el-tabs__content) {
  flex: 1;
  padding: 0;
  min-height: 0;
  overflow: hidden;
}

.tabs-content :deep(.el-tab-pane) {
  height: 100%;
  overflow: hidden;
}

.tab-content {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 20px;
}

.table-wrapper {
  flex: 1;
  border-radius: 8px 8px 0 0;
  border: 1px solid #e4e7ed;
  border-bottom: none;
  margin-bottom: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
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

.avatar-cell {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 8px 0;
}

.avatar-img {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid #f0f0f0;
  transition: all 0.3s ease;
}

.avatar-img.clickable {
  cursor: pointer;
}

.avatar-img.clickable:hover {
  border-color: #409eff;
  transform: scale(1.1);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
}

.empty-avatar {
  width: 50px;
  height: 50px;
  border: 2px dashed #e4e7ed;
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background-color: #f5f7fa;
  color: #909399;
}

.empty-text {
  font-size: 10px;
  margin-top: 2px;
  line-height: 1;
}

.text-cell {
  padding: 8px 0;
  word-break: break-word;
  line-height: 1.4;
  max-height: 150px;
  overflow-y: auto;
  white-space: pre-wrap;
  font-size: 13px;
  text-align: center;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 40px;
}

.text-cell::-webkit-scrollbar {
  width: 4px;
}

.text-cell::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 2px;
}

.text-cell::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 2px;
}

.text-cell::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

.username-cell {
  color: #409eff !important;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', 'source-code-pro', monospace !important;
}

.pagination-wrapper {
  display: flex !important;
  justify-content: center;
  align-items: center;
  padding: 12px 20px;
  border-top: 1px solid #e4e7ed;
  background-color: #fafafa;
  border-radius: 0 0 8px 8px;
  border-left: 1px solid #e4e7ed;
  border-right: 1px solid #e4e7ed;
  border-bottom: 1px solid #e4e7ed;
  min-height: 50px;
  width: 100%;
  flex-shrink: 0;
  margin: 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .left-column {
    height: 180px;
    padding: 12px;
  }
  
  .right-column {
    padding: 0 12px 12px 12px;
  }
}
</style>