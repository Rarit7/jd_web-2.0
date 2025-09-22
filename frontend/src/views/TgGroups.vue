<template>
  <div class="tg-groups">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>Telegram群组管理</span>
          <div class="header-actions">
            <el-button type="primary" @click="showAddDialog = true">添加群组</el-button>
            <el-button @click="downloadData">下载数据</el-button>
          </div>
        </div>
      </template>
      
      <!-- 搜索区域 -->
      <div class="search-area">
        <el-form :model="searchForm" inline>
          <el-form-item label="群组名称">
            <el-input
              v-model="searchForm.group_name"
              placeholder="请输入群组名称"
              clearable
              style="width: 200px;"
              @keydown.enter="fetchData"
              @clear="fetchData"
            />
          </el-form-item>
          <el-form-item label="群组ID">
            <el-input
              v-model="searchForm.chat_id"
              placeholder="请输入数字ID"
              clearable
              style="width: 150px;"
              @keydown.enter="fetchData"
              @clear="fetchData"
            />
          </el-form-item>
          <el-form-item label="群组链接">
            <el-input
              v-model="searchForm.group_link"
              placeholder="请输入群组链接"
              clearable
              style="width: 200px;"
              @keydown.enter="fetchData"
              @clear="fetchData"
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="fetchData">
              <el-icon><Search /></el-icon>
              搜索
            </el-button>
            <el-button @click="resetSearch">重置</el-button>
          </el-form-item>
          <el-form-item label="标签筛选">
            <el-select 
              v-model="searchForm.tag_ids" 
              multiple 
              placeholder="请选择标签" 
              clearable
              style="width: 300px;"
              :max-collapse-tags="2"
              @change="fetchData"
            >
              <el-option
                v-for="tag in tagList"
                :key="tag.id"
                :label="tag.name"
                :value="tag.id"
              >
                <div class="tag-option">
                  <span 
                    class="tag-color" 
                    :style="{ backgroundColor: tag.color }"
                  ></span>
                  <span>{{ tag.name }}</span>
                </div>
              </el-option>
            </el-select>
          </el-form-item>
        </el-form>

        <!-- 活跃度说明 -->
        <div class="activity-legend">
          <span class="legend-title">活跃度：</span>
          <div class="legend-items">
            <div class="legend-item">
              <span class="legend-dot very-active"></span>
              <span>1天内</span>
            </div>
            <div class="legend-item">
              <span class="legend-dot active"></span>
              <span>7天内</span>
            </div>
            <div class="legend-item">
              <span class="legend-dot less-active"></span>
              <span>30天内</span>
            </div>
            <div class="legend-item">
              <span class="legend-dot inactive"></span>
              <span>30天+</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 数据卡片 -->
      <div v-loading="loading" class="card-container">
        <div v-if="tableData.length === 0 && !loading" class="empty-state">
          <el-empty description="暂无群组数据" />
        </div>
        <div v-else class="cards-grid">
          <el-card
            v-for="group in tableData"
            :key="group.id"
            class="group-card"
            :class="getActivityClass(group)"
            shadow="hover"
          >
            <template #header>
              <div class="card-header-content">
                <div class="group-info">
                  <div class="group-title" :class="{ 'overflow-text': isTextOverflowing(group) }">
                    {{ group.title || group.name }}
                    <span v-if="group.remark" class="group-remark">({{ group.remark }})</span>
                  </div>
                  <div class="group-type">
                    <el-tag size="small" :type="group.group_type === 1 ? 'primary' : 'success'">
                      {{ group.group_type === 1 ? '群组' : '频道' }}
                    </el-tag>
                    <el-tag size="small" :type="getStatusType(group.status)" class="status-tag">
                      {{ group.status }}
                    </el-tag>
                    <div v-if="group.tag" class="header-tags">
                      <el-tag 
                        v-for="tag in group.tag.split(',')" 
                        :key="tag" 
                        size="small"
                        class="tag-item"
                        :color="getTagColor(tag.trim())"
                        effect="dark"
                        style="color: white; border: none;"
                      >
                        {{ tag.trim() }}
                      </el-tag>
                    </div>
                  </div>
                </div>
                <div class="group-avatar">
                  <el-avatar 
                    :size="64" 
                    :src="group.photo ? `/static/${group.photo}` : ''" 
                    :icon="group.group_type === 1 ? 'ChatDotRound' : 'Promotion'"
                    shape="square"
                  />
                </div>
              </div>
            </template>
            
            <div class="card-content">
              <!-- 基本信息 -->
              <div class="info-section no-bottom-border">
                <div class="info-row">
                  <span class="label">群组链接:</span>
                  <span class="value link-text">{{ group.name }}</span>
                </div>
                <div class="info-row">
                  <span class="label">群组ID:</span>
                  <span class="value">{{ group.chat_id }}</span>
                </div>
              </div>
              
              <!-- 群组描述 -->
              <div 
                class="group-description" 
                v-if="group.desc" 
                :class="{ clickable: descriptionOverflows(group.id) }"
                @click.stop="descriptionOverflows(group.id) ? toggleDescription(group.id) : null"
              >
                <p 
                  class="desc-text" 
                  :class="{ expanded: expandedDescriptions.has(group.id) }"
                >
                  {{ group.desc }}
                </p>
                <el-icon 
                  class="expand-icon" 
                  :class="{ expanded: expandedDescriptions.has(group.id) }"
                  v-if="descriptionOverflows(group.id)"
                >
                  <ArrowDown />
                </el-icon>
              </div>

              <!-- 时间信息 -->
              <div class="info-section no-bottom-border">
                <div class="info-row time-row">
                  <div class="time-item" v-if="group.latest_postal_time">
                    <span class="label">最新消息:</span>
                    <span class="activity-indicator" :class="getActivityClass(group)"></span>
                    <span class="value" :class="{ 'old-time': group.three_days_ago }">
                      {{ formatUTCToLocal(group.latest_postal_time) }}
                    </span>
                  </div>
                  <div class="time-item">
                    <span class="label">群组人数:</span>
                    <span class="value">
                      {{ group.members_count || 0 }}
                      <span v-if="group.members_increment > 0" style="color: #f56c6c; font-weight: 500;">
                        (+{{ group.members_increment }})
                      </span>
                      <span v-else-if="group.members_increment < 0" style="color: #67c23a; font-weight: 500;">
                        ({{ group.members_increment }})
                      </span>
                    </span>
                  </div>
                </div>
              </div>
              
              <!-- 统计信息 -->
              <div class="info-section">
                <div class="info-row stats-row">
                  <div class="time-item">
                    <span class="label">创建时间:</span>
                    <span class="value">{{ formatUTCToLocal(group.created_at) }}</span>
                  </div>
                  <div class="time-item">
                    <span class="label">对话数量:</span>
                    <span class="value">
                      {{ group.records_count || 0 }}
                      <span v-if="group.records_increment > 0" style="color: #f56c6c; font-weight: 500;">
                        (+{{ group.records_increment }})
                      </span>
                      <span v-else-if="group.records_increment < 0" style="color: #67c23a; font-weight: 500;">
                        ({{ group.records_increment }})
                      </span>
                    </span>
                  </div>
                </div>
              </div>
              
              <!-- 操作按钮 -->
              <div class="card-actions">
                <el-button type="success" size="small" @click="viewChat(group)">
                  <el-icon><ChatDotRound /></el-icon>
                  查看对话
                </el-button>
                <el-button type="primary" size="small" @click="editGroup(group)">
                  <el-icon><Edit /></el-icon>
                  编辑标签
                </el-button>
                <el-button type="warning" size="small" @click="fetchHistory(group)">
                  <el-icon><Download /></el-icon>
                  获取历史
                </el-button>
                <el-button type="danger" size="small" @click="deleteGroup(group)">
                  <el-icon><Delete /></el-icon>
                  删除
                </el-button>
              </div>
            </div>
          </el-card>
        </div>
      </div>
    </el-card>

    <!-- 添加群组对话框 -->
    <el-dialog v-model="showAddDialog" title="添加群组" width="400px">
      <el-form :model="addForm" :rules="addRules" ref="addFormRef">
        <el-form-item label="Telegram账户" prop="account_id">
          <el-select v-model="addForm.account_id" placeholder="请选择账户" style="width: 100%">
            <el-option
              v-for="account in tgAccounts"
              :key="account.id"
              :label="getAccountDisplayName(account)"
              :value="account.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="群组名称" prop="name">
          <el-input 
            v-model="addForm.name" 
            placeholder="请输入群组名称，多个用逗号分隔" 
            type="textarea"
            :rows="3"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="addGroup" :loading="addLoading">确定</el-button>
      </template>
    </el-dialog>

    <!-- 编辑标签对话框 -->
    <el-dialog v-model="showEditDialog" title="编辑群组标签" width="500px">
      <el-form :model="editForm" ref="editFormRef">
        <el-form-item label="群组名称">
          <el-input v-model="editForm.title" readonly />
        </el-form-item>
        <el-form-item label="标签">
          <el-select v-model="editForm.tag_id_list" multiple placeholder="请选择标签">
            <el-option
              v-for="tag in tagList"
              :key="tag.id"
              :label="tag.name"
              :value="tag.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="editForm.remark" placeholder="请输入备注" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="updateGroup" :loading="editLoading">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance } from 'element-plus'
import { Edit, Download, Delete, ChatDotRound, Promotion, ArrowDown, Search } from '@element-plus/icons-vue'
import { tgGroupsApi, type TgGroup } from '@/api/tg-groups'
import { tagsApi, type Tag } from '@/api/tags'
import { getTgAccountList } from '@/api/tg-accounts'
import { useRouter } from 'vue-router'
import { formatUTCToLocal } from '@/utils/date'

// Router实例
const router = useRouter()

// 响应式数据
const loading = ref(false)
const addLoading = ref(false)
const editLoading = ref(false)
const showAddDialog = ref(false)
const showEditDialog = ref(false)
const tableData = ref<TgGroup[]>([])
const tagList = ref<any[]>([])
const tgAccounts = ref<any[]>([])
const tagColorMap = ref(new Map<string, string>())
const expandedDescriptions = ref(new Set<number>())
const overflowingDescs = ref(new Set<number>())

// 表单引用
const addFormRef = ref<FormInstance>()
const editFormRef = ref<FormInstance>()

// 搜索表单
const searchForm = reactive({
  group_name: '',
  chat_id: '',
  group_link: '',
  tag_ids: [] as number[]
})

// 添加表单
const addForm = reactive({
  name: '',
  account_id: ''
})

const addRules = {
  name: [
    { required: true, message: '请输入群组名称', trigger: 'blur' }
  ],
  account_id: [
    { required: true, message: '请选择Telegram账户', trigger: 'change' }
  ]
}

// 编辑表单
const editForm = reactive({
  id: 0,
  title: '',
  tag_id_list: [] as number[],
  remark: ''
})

// 获取标签颜色映射
const fetchTagColors = async () => {
  try {
    const response = await tagsApi.getList()
    if (response.err_code === 0) {
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

// 获取标签颜色
const getTagColor = (tagName: string): string => {
  return tagColorMap.value.get(tagName) || '#409EFF'
}

// 获取账户显示名称
const getAccountDisplayName = (account: any): string => {
  // 优先显示昵称，其次用户名，最后显示连接名称
  let displayName = account.nickname || account.username || account.name
  // 添加手机号作为标识
  return `${displayName} (${account.phone})`
}

// 获取数据
const fetchData = async () => {
  loading.value = true
  try {
    // Prepare search parameters
    const params: any = {}
    if (searchForm.group_name) {
      params.group_name = searchForm.group_name
    }
    if (searchForm.chat_id) {
      params.chat_id = searchForm.chat_id
    }
    if (searchForm.group_link) {
      params.group_link = searchForm.group_link
    }
    if (searchForm.tag_ids.length > 0) {
      params.tag_ids = searchForm.tag_ids.join(',')
    }
    
    const response = await tgGroupsApi.getList(params)
    // 后端返回格式为 { err_code: 0, payload: { data: [], tag_list: [] } }
    if (response.data.err_code === 0) {
      tableData.value = response.data.payload.data
      tagList.value = response.data.payload.tag_list
      
      
      // 等待DOM更新后检查描述是否溢出
      nextTick(() => {
        checkDescriptionOverflow()
      })
    } else {
      ElMessage.error(response.data.err_msg || '获取数据失败')
    }
  } catch (error) {
    ElMessage.error('获取数据失败')
  } finally {
    loading.value = false
  }
}

// 重置搜索
const resetSearch = () => {
  searchForm.group_name = ''
  searchForm.chat_id = ''
  searchForm.group_link = ''
  searchForm.tag_ids = []
  fetchData()
}

// 获取TG账户列表
const fetchTgAccounts = async () => {
  try {
    const response = await getTgAccountList()
    if (response.err_code === 0) {
      // 只获取已登录的账户
      tgAccounts.value = Array.isArray(response.payload) ? response.payload.filter(account => account.status === 1) : []
    } else {
      ElMessage.error('获取账户列表失败')
    }
  } catch (error) {
    console.error('获取账户列表失败:', error)
  }
}

// 添加群组
const addGroup = async () => {
  if (!addFormRef.value) return
  
  try {
    await addFormRef.value.validate()
    addLoading.value = true
    
    // 根据选择的账户ID找到对应的session_name
    const selectedAccount = tgAccounts.value.find(account => account.id === addForm.account_id)
    if (!selectedAccount) {
      ElMessage.error('请选择有效的Telegram账户')
      return
    }
    
    await tgGroupsApi.add({ 
      name: addForm.name,
      session_name: selectedAccount.name
    })
    ElMessage.success('群组添加成功')
    showAddDialog.value = false
    addForm.name = ''
    addForm.account_id = ''
    fetchData()
  } catch (error) {
    ElMessage.error('添加失败')
  } finally {
    addLoading.value = false
  }
}

// 编辑群组
const editGroup = (row: TgGroup) => {
  editForm.id = row.id
  editForm.title = row.title
  editForm.tag_id_list = row.tag_id_list ? row.tag_id_list.split(',').map(Number) : []
  editForm.remark = row.remark
  showEditDialog.value = true
}

// 更新群组
const updateGroup = async () => {
  editLoading.value = true
  try {
    await tgGroupsApi.updateTag({
      group_id: editForm.id,
      tag_id_list: editForm.tag_id_list.join(','),
      remark: editForm.remark
    })
    ElMessage.success('更新成功')
    showEditDialog.value = false
    fetchTagColors()  // 刷新标签颜色
    fetchData()
  } catch (error) {
    ElMessage.error('更新失败')
  } finally {
    editLoading.value = false
  }
}

// 删除群组
const deleteGroup = async (row: TgGroup) => {
  try {
    await ElMessageBox.confirm('确定要删除这个群组吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await tgGroupsApi.delete(row.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 获取历史
const fetchHistory = async (row: TgGroup) => {
  try {
    await ElMessageBox.confirm('确定要获取这个群组的历史消息吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'info'
    })
    
    await tgGroupsApi.fetchHistory({
      group_name: row.name,
      chat_id: parseInt(row.chat_id)
    })
    ElMessage.success('历史获取任务已启动')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('获取历史失败')
    }
  }
}

// 下载数据
const downloadData = async () => {
  try {
    // Prepare search parameters for download
    const params: any = {}
    if (searchForm.group_name) {
      params.group_name = searchForm.group_name
    }
    if (searchForm.chat_id) {
      params.chat_id = searchForm.chat_id
    }
    if (searchForm.group_link) {
      params.group_link = searchForm.group_link
    }
    if (searchForm.tag_ids.length > 0) {
      params.tag_ids = searchForm.tag_ids.join(',')
    }
    
    const response = await tgGroupsApi.download(params)
    const blob = new Blob([response.data], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    })
    
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = 'groups.xlsx'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('下载成功')
  } catch (error) {
    ElMessage.error('下载失败')
  }
}

// 获取状态类型
const getStatusType = (status: string) => {
  switch (status) {
    case '加入成功':
      return 'success'
    case '加入失败':
      return 'danger'
    case '加入中':
      return 'warning'
    default:
      return 'info'
  }
}

// 获取群组活跃度样式类
const getActivityClass = (group: any) => {
  if (!group.latest_postal_time) {
    return 'inactive-group'
  }

  const now = new Date()
  const lastTime = new Date(group.latest_postal_time)
  const diffDays = Math.floor((now.getTime() - lastTime.getTime()) / (1000 * 60 * 60 * 24))

  if (diffDays <= 1) {
    return 'very-active-group'  // 1天内
  } else if (diffDays <= 7) {
    return 'active-group'       // 7天内
  } else if (diffDays <= 30) {
    return 'less-active-group'  // 30天内
  } else {
    return 'inactive-group'     // 超过30天
  }
}

// 检查描述是否溢出
const checkDescriptionOverflow = () => {
  const newOverflowingDescs = new Set<number>()
  
  tableData.value.forEach((group) => {
    if (group.desc) {
      // 简单的字符长度检查 - 如果描述超过60个字符，认为会溢出
      // 或者检查是否包含换行符
      const hasLineBreak = group.desc.includes('\n') || group.desc.includes('\r')
      const isLong = group.desc.length > 60
      
      if (hasLineBreak || isLong) {
        newOverflowingDescs.add(group.id)
      }
    }
  })
  
  overflowingDescs.value = newOverflowingDescs
  console.log('Overflowing descriptions:', overflowingDescs.value)
}

// 判断描述是否溢出
const descriptionOverflows = (groupId: number) => {
  return overflowingDescs.value.has(groupId)
}

// 判断文本是否溢出（群组名+备注）
const isTextOverflowing = (group: TgGroup) => {
  const title = group.title || group.name || ''
  const remark = group.remark || ''
  const fullText = title + (remark ? `(${remark})` : '')
  // 假设每个字符平均宽度为8px，容器宽度约为240px
  return fullText.length * 8 > 240
}

// 切换描述展开状态
const toggleDescription = (groupId: number) => {
  console.log('Toggling description for group:', groupId)
  const newSet = new Set(expandedDescriptions.value)
  if (newSet.has(groupId)) {
    newSet.delete(groupId)
    console.log('Collapsing description')
  } else {
    newSet.add(groupId)
    console.log('Expanding description')
  }
  expandedDescriptions.value = newSet
  console.log('Expanded descriptions:', expandedDescriptions.value)
}

// 格式化计数显示（带增量）
const formatCount = (count: number | undefined, increment: number | undefined): string => {
  const baseCount = count || 0
  const inc = increment || 0
  
  // 如果数据为0且没有增量，显示 "-"
  if (baseCount === 0 && inc === 0) {
    return '-'
  }
  
  let result = baseCount.toString()
  
  // 添加增量显示
  if (inc > 0) {
    result += `(+${inc})`
  } else if (inc < 0) {
    result += `(${inc})`
  }
  
  return result
}

// 格式化计数显示（带增量和颜色）
const formatCountWithColor = (count: number | undefined, increment: number | undefined): string => {
  const baseCount = count || 0
  const inc = increment || 0
  
  // 如果数据为0且没有增量，显示 "-"
  if (baseCount === 0 && inc === 0) {
    return '-'
  }
  
  let result = baseCount.toString()
  
  // 添加带颜色的增量显示
  if (inc > 0) {
    result += ` <span style="color: #f56c6c; font-weight: 500;">(+${inc})</span>`
  } else if (inc < 0) {
    result += ` <span style="color: #67c23a; font-weight: 500;">(${inc})</span>`
  }
  
  return result
}

// 查看对话
const viewChat = (row: TgGroup) => {
  // 使用Vue Router进行页面跳转，传递群组信息作为查询参数
  router.push({
    path: '/chat-history',
    query: {
      group_id: row.chat_id,
      group_name: row.title || row.name
    }
  })
}

// 页面加载时获取数据
onMounted(() => {
  fetchTagColors()  // 先获取标签颜色
  fetchData()
  fetchTgAccounts()  // 获取TG账户列表
})
</script>

<style scoped>
.tg-groups {
  height: 100%;
}

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
  margin-bottom: 20px;
  padding: 20px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.activity-legend {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  gap: 15px;
}

.legend-title {
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}

.legend-items {
  display: flex;
  gap: 15px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  color: #909399;
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}

.legend-dot.very-active {
  background-color: #67c23a;
  box-shadow: 0 0 4px rgba(103, 194, 58, 0.5);
}

.legend-dot.active {
  background-color: #409eff;
  box-shadow: 0 0 4px rgba(64, 158, 255, 0.5);
}

.legend-dot.less-active {
  background-color: #e6a23c;
}

.legend-dot.inactive {
  background-color: #909399;
}

.card-container {
  min-height: 400px;
  background-image: url('/bg.webp');
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  border-radius: 8px;
  padding: 16px;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 300px;
}

.cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(480px, 1fr));
  gap: 24px;
  margin-top: 20px;
}

.group-card {
  transition: transform 0.2s, box-shadow 0.2s;
  border-radius: 12px;
  overflow: hidden;
}

.group-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
}

/* 群组活跃度样式 */
.very-active-group {
  border-left: 4px solid #67c23a;
  background: linear-gradient(135deg, #f0f9ff 0%, #e6fffa 100%);
}

.active-group {
  border-left: 4px solid #409eff;
  background: linear-gradient(135deg, #f0f9ff 0%, #f5f7fa 100%);
}

.less-active-group {
  border-left: 4px solid #e6a23c;
}

.inactive-group {
  border-left: 4px solid #909399;
  opacity: 0.7;
}

/* 活跃度指示器 */
.activity-indicator {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 6px;
  vertical-align: middle;
}

.activity-indicator.very-active-group {
  background-color: #67c23a;
  box-shadow: 0 0 6px rgba(103, 194, 58, 0.5);
}

.activity-indicator.active-group {
  background-color: #409eff;
  box-shadow: 0 0 6px rgba(64, 158, 255, 0.5);
}

.activity-indicator.less-active-group {
  background-color: #e6a23c;
}

.activity-indicator.inactive-group {
  background-color: #909399;
}

.card-header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0;
}

.group-info {
  flex: 1;
  min-width: 0;
  overflow: hidden;
}

.group-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
  overflow: hidden;
  position: relative;
  display: block;
  white-space: nowrap;
  width: 100%;
  text-overflow: ellipsis;
}

.group-title.overflow-text {
  animation: scrollText 15s linear infinite;
  text-overflow: unset;
  width: max-content;
}

.group-title.overflow-text:hover {
  animation-play-state: paused;
}

.group-remark {
  color: #909399;
  font-weight: normal;
  margin-left: 4px;
}

@keyframes scrollText {
  0%, 30% {
    transform: translateX(0);
  }
  70%, 100% {
    transform: translateX(calc(-100% + 240px));
  }
}

.group-type {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  align-items: center;
}

.header-tags {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
  margin-left: 8px;
}

.status-tag {
  margin-left: 4px;
}

.group-avatar {
  flex-shrink: 0;
  margin-left: 20px;
}

.group-avatar .el-avatar {
  border: 2px solid #e4e7ed;
  transition: border-color 0.3s;
}

.group-card:hover .group-avatar .el-avatar {
  border-color: #409eff;
}

.card-content {
  padding-top: 16px;
}

.group-description {
  margin-bottom: 16px;
  padding: 12px;
  background-color: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #409eff;
  position: relative;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

.group-description.clickable {
  cursor: pointer;
}

.group-description.clickable:hover {
  background-color: #eef5ff;
  border-left-color: #337ecc;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
}

.group-description.with-bottom-border {
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.desc-text {
  margin: 0;
  color: #606266;
  font-size: 14px;
  line-height: 1.6;
  word-wrap: break-word;
  padding-right: 20px;
  transition: max-height 0.3s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.3s ease;
  overflow: hidden;
  max-height: 1.6em; /* 默认一行的高度 */
}

.desc-text.expanded {
  max-height: 500px; /* 足够大的值以容纳完整内容 */
  white-space: pre-wrap;
  opacity: 1;
}

.desc-text:not(.expanded) {
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.expand-icon {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 14px;
  color: #409eff;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  opacity: 0.7;
}

.expand-icon:hover {
  opacity: 1;
  color: #337ecc;
  transform: translateY(-50%) scale(1.1);
}

.expand-icon.expanded {
  transform: translateY(-50%) rotate(180deg);
  color: #337ecc;
  opacity: 1;
}

.expand-icon.expanded:hover {
  transform: translateY(-50%) rotate(180deg) scale(1.1);
}

.info-section {
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.info-section.no-bottom-border {
  border-bottom: none;
  padding-bottom: 8px;
}

.info-section:last-of-type {
  border-bottom: none;
  margin-bottom: 0;
}

.info-row {
  display: flex;
  align-items: flex-start;
  margin-bottom: 12px;
  font-size: 14px;
}

.info-row:last-child {
  margin-bottom: 0;
}

.label {
  min-width: 80px;
  color: #606266;
  font-weight: 500;
  flex-shrink: 0;
}

.value {
  color: #303133;
  word-break: break-all;
  flex: 1;
}

.link-text {
  color: #409eff;
  cursor: pointer;
  font-family: monospace;
  background-color: #f0f2f5;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
}

.time-text {
  font-family: monospace;
  font-size: 13px;
  color: #909399;
}


.old-time {
  color: #f56c6c;
  font-weight: 500;
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  flex: 1;
}

.tag-item {
  margin: 0;
}

.time-row,
.stats-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 12px;
}

.stats-row {
  margin-bottom: 0;
}

.time-item {
  display: flex;
  align-items: center;
  font-size: 14px;
  flex: 1;
  min-width: 0;
}

.time-item .label {
  min-width: 80px;
  color: #606266;
  font-weight: 500;
  flex-shrink: 0;
}

.time-item .value {
  color: #303133;
  word-break: break-all;
  flex: 1;
}

.card-actions {
  margin-top: 16px;
  padding-top: 16px;
  display: flex;
  justify-content: space-between;
  gap: 6px;
}

.card-actions .el-button {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  min-width: 0;
}

.card-actions .el-button .el-icon {
  font-size: 14px;
}

/* 响应式设计 */
@media (max-width: 1400px) {
  .cards-grid {
    grid-template-columns: repeat(auto-fill, minmax(420px, 1fr));
  }
}

@media (max-width: 1200px) {
  .cards-grid {
    grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
    gap: 20px;
  }
}

@media (max-width: 900px) {
  .cards-grid {
    grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
    gap: 16px;
  }
}

@media (max-width: 768px) {
  .cards-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .card-header-content {
    flex-direction: column;
    text-align: center;
  }
  
  .group-avatar {
    margin: 12px 0 0 0;
  }
  
  .card-actions {
    flex-direction: column;
    gap: 8px;
  }
  
  .search-area .el-form {
    flex-direction: column;
  }
  
  .search-area .el-form-item {
    margin-right: 0;
    margin-bottom: 16px;
  }
  
  .group-description {
    margin-bottom: 12px;
    padding: 10px;
  }
  
  .info-section {
    margin-bottom: 12px;
    padding-bottom: 10px;
  }
  
  .time-row,
  .stats-row {
    flex-direction: column;
    gap: 12px;
  }
  
  .time-item {
    margin-bottom: 0;
  }
}

/* 增量颜色样式 */
.increment-positive {
  color: #f56c6c;
  font-weight: 500;
}

.increment-negative {
  color: #67c23a;
  font-weight: 500;
}

/* 标签选择器样式 */
.tag-option {
  display: flex;
  align-items: center;
  gap: 8px;
}

.tag-color {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  flex-shrink: 0;
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
</style>