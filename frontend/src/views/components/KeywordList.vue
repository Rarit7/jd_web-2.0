<template>
  <div class="keyword-list">
    <!-- 过滤器 -->
    <div class="filters">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索关键词"
        style="width: 200px"
        clearable
        @input="handleSearch"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>

      <el-select
        v-model="statusFilter"
        placeholder="状态筛选"
        style="width: 120px"
        @change="fetchData"
      >
        <el-option label="全部" :value="undefined" />
        <el-option label="启用" :value="true" />
        <el-option label="禁用" :value="false" />
      </el-select>

      <el-button @click="handleRefresh" :icon="Refresh">刷新</el-button>
    </div>

    <!-- 关键词网格 -->
    <div v-loading="loading" class="keywords-container">
      <div class="keywords-stats">
        <span>共 {{ total }} 个关键词</span>
        <el-button-group class="view-options">
          <el-button
            :type="showOnlyActive ? 'primary' : ''"
            size="small"
            @click="toggleActiveFilter"
          >
            仅显示启用
          </el-button>
        </el-button-group>
      </div>

      <div class="keywords-grid">
        <div
          v-for="keyword in tableData"
          :key="keyword.id"
          :ref="el => setKeywordRef(keyword.id, el)"
          class="keyword-item"
          :class="{
            'keyword-inactive': !keyword.is_active,
            'keyword-focus': keyword.auto_focus,
            'keyword-active': keyword.is_active && !keyword.auto_focus
          }"
          @click="handleKeywordClick(keyword, $event)"
        >
          <div class="keyword-content">
            <span class="keyword-text">{{ keyword.keyword }}</span>
            <div class="keyword-badges">
              <el-tag
                v-if="keyword.auto_focus"
                size="small"
                effect="plain"
                class="focus-badge"
              >
                关注
              </el-tag>
              <el-tag
                v-if="!keyword.is_active"
                size="small"
                effect="plain"
                class="inactive-badge"
              >
                禁用
              </el-tag>
            </div>
          </div>
        </div>

        <!-- 空状态 -->
        <div v-if="tableData.length === 0 && !loading" class="empty-state">
          <el-empty description="暂无关键词" />
        </div>
      </div>

      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          :total="total"
          layout="total, prev, pager, next, jumper"
          @current-change="handleCurrentChange"
        />
      </div>
    </div>

    <!-- 关键词操作弹出框 -->
    <el-popover
      ref="keywordPopover"
      :placement="popoverPlacement"
      :width="280"
      trigger="manual"
      v-model:visible="showKeywordPopover"
      :virtual-ref="virtualRef"
      virtual-triggering
    >
      <div v-if="selectedKeyword" class="keyword-actions">
        <div class="keyword-info">
          <h4>{{ selectedKeyword.keyword }}</h4>
          <p class="keyword-meta">
            创建时间：{{ formatDate(selectedKeyword.created_at) }}
          </p>
        </div>

        <div class="action-buttons">
          <el-button-group>
            <el-button
              :type="selectedKeyword.is_active ? 'success' : 'info'"
              size="small"
              @click="toggleKeywordStatus"
              :loading="selectedKeyword.updating"
            >
              {{ selectedKeyword.is_active ? '已启用' : '已禁用' }}
            </el-button>
            <el-button
              :type="selectedKeyword.auto_focus ? 'warning' : ''"
              size="small"
              @click="toggleAutoFocus"
              :loading="selectedKeyword.updating"
            >
              {{ selectedKeyword.auto_focus ? '已关注' : '不关注' }}
            </el-button>
          </el-button-group>
        </div>

        <div class="action-row">
          <el-button type="primary" size="small" @click="handleEdit(selectedKeyword)">
            编辑
          </el-button>
          <el-button type="danger" size="small" @click="handleDelete(selectedKeyword)">
            删除
          </el-button>
        </div>
      </div>
    </el-popover>

    <!-- 编辑对话框 -->
    <el-dialog v-model="showEditDialog" title="编辑关键词" width="500px">
      <KeywordForm
        :keyword-data="editingKeyword"
        @success="handleEditSuccess"
        @cancel="showEditDialog = false"
      />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh } from '@element-plus/icons-vue'
import { tagsApi, type TagKeywordMapping } from '@/api/tags'
import KeywordForm from '@/views/components/KeywordForm.vue'

interface Props {
  tagId: number
}

interface Emits {
  (e: 'refresh'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 响应式数据
const loading = ref(false)
const tableData = ref<TagKeywordMapping[]>([])
const searchKeyword = ref('')
const statusFilter = ref<boolean | undefined>(undefined)
const showOnlyActive = ref(false)
const currentPage = ref(1)
const pageSize = ref(200)
const total = ref(0)
const showEditDialog = ref(false)
const showKeywordPopover = ref(false)
const editingKeyword = ref<TagKeywordMapping>()
const selectedKeyword = ref<TagKeywordMapping>()
const keywordPopover = ref()
const keywordRefs = ref<Map<number, HTMLElement>>(new Map())
const virtualRef = ref()
const popoverPlacement = ref<'top' | 'bottom' | 'left' | 'right'>('bottom')

// 获取数据
const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value,
      is_active: statusFilter.value
    }

    const response = await tagsApi.getKeywordMappings(props.tagId, params)
    if (response.err_code === 0) {
      tableData.value = response.payload.data.map((item: TagKeywordMapping) => ({
        ...item,
        updating: false
      }))
      total.value = response.payload.total
    } else {
      ElMessage.error(response.err_msg || '获取关键词列表失败')
    }
  } catch (error) {
    console.error('获取关键词列表失败:', error)
    ElMessage.error('获取关键词列表失败')
  } finally {
    loading.value = false
  }
}

// 搜索处理
const handleSearch = () => {
  if (searchKeyword.value) {
    const filtered = tableData.value.filter(item =>
      item.keyword.toLowerCase().includes(searchKeyword.value.toLowerCase())
    )
    // 这里可以添加客户端过滤逻辑，或者发送到服务器进行搜索
  } else {
    fetchData()
  }
}

// 刷新
const handleRefresh = () => {
  fetchData()
}

// 状态变更
const handleStatusChange = async (row: TagKeywordMapping & { updating?: boolean }) => {
  row.updating = true
  try {
    const response = await tagsApi.updateKeywordMapping(row.id, {
      is_active: row.is_active
    })

    if (response.err_code === 0) {
      ElMessage.success('状态更新成功')
    } else {
      // 回滚状态
      row.is_active = !row.is_active
      ElMessage.error(response.err_msg || '状态更新失败')
    }
  } catch (error) {
    // 回滚状态
    row.is_active = !row.is_active
    console.error('状态更新失败:', error)
    ElMessage.error('状态更新失败')
  } finally {
    row.updating = false
  }
}

// 自动关注变更
const handleAutoFocusChange = async (row: TagKeywordMapping & { updating?: boolean }) => {
  row.updating = true
  try {
    const response = await tagsApi.updateKeywordMapping(row.id, {
      auto_focus: row.auto_focus
    })

    if (response.err_code === 0) {
      ElMessage.success('自动关注设置更新成功')
    } else {
      // 回滚状态
      row.auto_focus = !row.auto_focus
      ElMessage.error(response.err_msg || '自动关注设置更新失败')
    }
  } catch (error) {
    // 回滚状态
    row.auto_focus = !row.auto_focus
    console.error('自动关注设置更新失败:', error)
    ElMessage.error('自动关注设置更新失败')
  } finally {
    row.updating = false
  }
}

// 编辑
const handleEdit = (row: TagKeywordMapping) => {
  editingKeyword.value = { ...row }
  showEditDialog.value = true
}

// 编辑成功
const handleEditSuccess = () => {
  showEditDialog.value = false
  fetchData()
  ElMessage.success('编辑成功')
}

// 删除
const handleDelete = async (row: TagKeywordMapping) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除关键词"${row.keyword}"吗？`,
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const response = await tagsApi.deleteKeywordMapping(row.id)
    if (response.err_code === 0) {
      ElMessage.success('删除成功')
      fetchData()
    } else {
      ElMessage.error(response.err_msg || '删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除关键词失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

// 设置关键词元素引用
const setKeywordRef = (keywordId: number, el: HTMLElement | null) => {
  if (el) {
    keywordRefs.value.set(keywordId, el)
  } else {
    keywordRefs.value.delete(keywordId)
  }
}

// 关键词点击处理
const handleKeywordClick = (keyword: TagKeywordMapping, event: MouseEvent) => {
  selectedKeyword.value = keyword

  // 设置虚拟引用元素
  const targetElement = keywordRefs.value.get(keyword.id)
  if (targetElement) {
    virtualRef.value = targetElement

    // 根据点击位置智能调整弹出框位置
    const rect = targetElement.getBoundingClientRect()
    const windowHeight = window.innerHeight
    const windowWidth = window.innerWidth

    // 如果元素在屏幕下半部分，弹出框显示在上方
    if (rect.bottom > windowHeight / 2) {
      popoverPlacement.value = 'top'
    } else {
      popoverPlacement.value = 'bottom'
    }

    // 如果元素在屏幕右侧，弹出框显示在左侧
    if (rect.right > windowWidth * 0.7) {
      popoverPlacement.value = rect.top < windowHeight / 2 ? 'bottom-start' : 'top-start'
    }
  }

  showKeywordPopover.value = true
}

// 切换仅显示启用状态
const toggleActiveFilter = () => {
  showOnlyActive.value = !showOnlyActive.value
  statusFilter.value = showOnlyActive.value ? true : undefined
  currentPage.value = 1
  fetchData()
}

// 切换关键词状态
const toggleKeywordStatus = async () => {
  if (!selectedKeyword.value) return

  selectedKeyword.value.updating = true
  try {
    const response = await tagsApi.updateKeywordMapping(selectedKeyword.value.id, {
      is_active: !selectedKeyword.value.is_active
    })

    if (response.err_code === 0) {
      selectedKeyword.value.is_active = !selectedKeyword.value.is_active
      ElMessage.success('状态更新成功')
      // 更新列表中的数据
      const index = tableData.value.findIndex(item => item.id === selectedKeyword.value!.id)
      if (index > -1) {
        tableData.value[index].is_active = selectedKeyword.value.is_active
      }
    } else {
      ElMessage.error(response.err_msg || '状态更新失败')
    }
  } catch (error) {
    console.error('状态更新失败:', error)
    ElMessage.error('状态更新失败')
  } finally {
    selectedKeyword.value.updating = false
  }
}

// 切换自动关注
const toggleAutoFocus = async () => {
  if (!selectedKeyword.value) return

  selectedKeyword.value.updating = true
  try {
    const response = await tagsApi.updateKeywordMapping(selectedKeyword.value.id, {
      auto_focus: !selectedKeyword.value.auto_focus
    })

    if (response.err_code === 0) {
      selectedKeyword.value.auto_focus = !selectedKeyword.value.auto_focus
      ElMessage.success('自动关注设置更新成功')
      // 更新列表中的数据
      const index = tableData.value.findIndex(item => item.id === selectedKeyword.value!.id)
      if (index > -1) {
        tableData.value[index].auto_focus = selectedKeyword.value.auto_focus
      }
    } else {
      ElMessage.error(response.err_msg || '自动关注设置更新失败')
    }
  } catch (error) {
    console.error('自动关注设置更新失败:', error)
    ElMessage.error('自动关注设置更新失败')
  } finally {
    selectedKeyword.value.updating = false
  }
}


// 当前页变更
const handleCurrentChange = (newPage: number) => {
  currentPage.value = newPage
  fetchData()
}

// 格式化日期
const formatDate = (dateString: string) => {
  if (!dateString) return ''
  return new Date(dateString).toLocaleString('zh-CN')
}

// 监听标签ID变化
watch(() => props.tagId, () => {
  if (props.tagId) {
    currentPage.value = 1
    fetchData()
  }
}, { immediate: true })

// 页面加载时获取数据
onMounted(() => {
  if (props.tagId) {
    fetchData()
  }
})
</script>

<style scoped>
.keyword-list {
  margin-top: 16px;
}

.filters {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  align-items: center;
}

.table-container {
  background: white;
  border-radius: 8px;
  min-height: 400px;
}

.keywords-container {
  background: white;
  border-radius: 8px;
  padding: 16px;
  min-height: 400px;
}

.keywords-stats {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.view-options {
  margin-left: auto;
}

.keywords-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 20px;
  align-items: flex-start;
  align-content: flex-start;
}

.keyword-item {
  display: inline-flex;
  align-items: center;
  border: 1px solid #dcdfe6;
  border-radius: 20px;
  padding: 8px 16px;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
  font-size: 14px;
  line-height: 1.4;
  max-width: 300px;
  min-width: fit-content;
}

.keyword-item:hover {
  border-color: #409eff;
  background: linear-gradient(135deg, #ecf5ff 0%, #d9ecff 100%);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.2);
  transform: translateY(-2px) scale(1.02);
}

.keyword-item.keyword-inactive {
  background: linear-gradient(135deg, #f5f7fa 0%, #e9ecef 100%);
  border-color: #c0c4cc;
  color: #909399;
}

.keyword-item.keyword-inactive:hover {
  border-color: #909399;
  background: linear-gradient(135deg, #f0f2f5 0%, #d3d4d6 100%);
  box-shadow: 0 2px 8px rgba(144, 147, 153, 0.15);
}

.keyword-item.keyword-focus {
  border-color: #f56c6c;
  background: linear-gradient(135deg, #fef0f0 0%, #fde2e2 100%);
  color: #f56c6c;
}

.keyword-item.keyword-focus:hover {
  border-color: #f56c6c;
  background: linear-gradient(135deg, #fde2e2 0%, #fccfcf 100%);
  box-shadow: 0 4px 12px rgba(245, 108, 108, 0.25);
}

.keyword-item.keyword-active {
  border-color: #67c23a;
  background: linear-gradient(135deg, #f0f9ff 0%, #e1f5fe 100%);
  color: #67c23a;
}

.keyword-item.keyword-active:hover {
  border-color: #67c23a;
  background: linear-gradient(135deg, #e1f5fe 0%, #b9f6ca 100%);
  box-shadow: 0 4px 12px rgba(103, 194, 58, 0.25);
}

.keyword-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
}

.keyword-text {
  font-weight: 500;
  color: inherit;
  word-break: break-word;
  line-height: 1.4;
  text-align: center;
}

.keyword-badges {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}

.focus-badge {
  background: #f56c6c !important;
  color: white !important;
  border: none !important;
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 10px;
  font-weight: 500;
}

.inactive-badge {
  background: #909399 !important;
  color: white !important;
  border: none !important;
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 10px;
  font-weight: 500;
}

.empty-state {
  width: 100%;
  text-align: center;
  padding: 40px 20px;
}

.keyword-actions {
  padding: 16px;
}

.keyword-info {
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.keyword-info h4 {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 16px;
}

.keyword-meta {
  margin: 0;
  color: #909399;
  font-size: 12px;
}

.action-buttons {
  margin-bottom: 12px;
}

.action-row {
  display: flex;
  gap: 8px;
}

.pagination {
  display: flex;
  justify-content: center;
  margin-top: 20px;
  padding: 20px 0;
}
</style>