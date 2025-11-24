<template>
  <div class="chemical-products">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>化工产品</span>
          <div class="header-actions">
            <el-select
              v-model="searchForm.platform_id"
              placeholder="选择平台"
              clearable
              style="width: 150px; margin-right: 10px;"
            >
              <el-option
                v-for="platform in platformList"
                :key="platform.id"
                :label="platform.name"
                :value="platform.id"
              />
            </el-select>
            <el-button type="primary" @click="startSearch" :loading="searchLoading">开始抓取</el-button>
            <el-button @click="downloadData">导出数据</el-button>
          </div>
        </div>
      </template>
      
      <!-- 搜索区域 -->
      <div class="search-area">
        <el-form :model="searchForm" inline class="search-form">
          <el-form-item label="产品名称:">
            <el-input 
              v-model="searchForm.product_name" 
              placeholder="请输入产品名称"
              clearable
              style="width: 200px;"
            />
          </el-form-item>
          <el-form-item label="化合物名称:">
            <el-input 
              v-model="searchForm.compound_name" 
              placeholder="请输入化合物名称"
              clearable
              style="width: 200px;"
            />
          </el-form-item>
          <el-form-item label="联系方式:">
            <el-input
              v-model="searchForm.contact_number"
              placeholder="请输入联系方式"
              clearable
              style="width: 200px;"
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleSearch">搜索</el-button>
            <el-button @click="resetSearch">重置</el-button>
          </el-form-item>
        </el-form>
      </div>
      
      <!-- 化工产品表格区域 -->
      <div class="table-area">
        <div class="table-container">
          <el-table 
            :data="productList" 
            v-loading="loading"
            :max-height="tableMaxHeight"
            stripe
            highlight-current-row
            empty-text="暂无化工产品数据"
            row-key="id"
            style="width: 100%;"
          >
            <el-table-column type="index" width="60" label="#" />
            
            <el-table-column prop="platform_name" label="平台" width="120" align="center">
              <template #default="{ row }">
                <el-tag size="small" type="info">{{ row.platform_name }}</el-tag>
              </template>
            </el-table-column>
            
            <el-table-column prop="product_name" label="产品名称" min-width="180" show-overflow-tooltip>
              <template #default="{ row }">
                <span class="product-text">{{ row.product_name }}</span>
              </template>
            </el-table-column>
            
            <el-table-column prop="compound_name" label="化合物名称" min-width="180" show-overflow-tooltip>
              <template #default="{ row }">
                <span class="compound-text">{{ row.compound_name }}</span>
              </template>
            </el-table-column>
            
            <el-table-column prop="seller_name" label="商家名称" min-width="150" show-overflow-tooltip>
              <template #default="{ row }">
                <span class="seller-text">{{ row.seller_name }}</span>
              </template>
            </el-table-column>
            
            <el-table-column prop="contact_number" label="联系方式" width="140" show-overflow-tooltip>
              <template #default="{ row }">
                <span class="contact-text">{{ row.contact_number }}</span>
              </template>
            </el-table-column>

            <el-table-column prop="status" label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)" size="small">
                  {{ getStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            
            <el-table-column prop="created_at" label="创建时间" width="150" show-overflow-tooltip>
              <template #default="{ row }">
                <span class="time-text">{{ formatDateTime(row.created_at) }}</span>
              </template>
            </el-table-column>
            
            <el-table-column label="操作" width="120" align="center" fixed="right">
              <template #default="{ row }">
                <el-button 
                  type="danger" 
                  size="small" 
                  @click="deleteProduct(row)"
                  :loading="deleteLoading"
                >
                  删除
                </el-button>
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
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, nextTick, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { chemicalProductsApi, type ChemicalProduct, type ChemicalPlatform } from '@/api/chemical-products'
import { formatUTCToLocal } from '@/utils/date'

// 页面元信息
defineOptions({
  name: 'ChemicalProducts'
})

// 响应式数据
const loading = ref(false)
const searchLoading = ref(false)
const deleteLoading = ref(false)
const productList = ref<ChemicalProduct[]>([])
const platformList = ref<ChemicalPlatform[]>([])

// 表格高度计算
const tableMaxHeight = ref(400)

// 分页数据
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

// 搜索表单
const searchForm = reactive({
  platform_id: undefined as number | undefined,
  product_name: '',
  compound_name: '',
  contact_number: ''
})

// 获取数据
const fetchData = async () => {
  loading.value = true
  
  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value,
      search_product_name: searchForm.product_name || undefined,
      search_compound_name: searchForm.compound_name || undefined,
      search_contact_number: searchForm.contact_number || undefined,
      search_platform_id: searchForm.platform_id ? [searchForm.platform_id] : undefined
    }
    
    const response = await chemicalProductsApi.getList(params)
    
    if (response.data.err_code === 0) {
      productList.value = response.data.payload.data || []
      total.value = response.data.payload.total_records || 0
      platformList.value = response.data.payload.platform_list || []
    } else {
      ElMessage.error(response.data.err_msg || '获取数据失败')
      productList.value = []
      total.value = 0
    }
  } catch (error) {
    console.error('获取数据失败:', error)
    ElMessage.error('获取数据失败')
    productList.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

// 分页变化处理
const handlePageChange = (page: number) => {
  currentPage.value = page
  fetchData()
}

// 每页大小变化处理
const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  fetchData()
}

// 搜索处理
const handleSearch = () => {
  currentPage.value = 1
  fetchData()
}

// 重置搜索
const resetSearch = () => {
  searchForm.platform_id = undefined
  searchForm.product_name = ''
  searchForm.compound_name = ''
  searchForm.contact_number = ''
  currentPage.value = 1
  fetchData()
}

// 开始抓取
const startSearch = async () => {
  if (!searchForm.platform_id) {
    ElMessage.warning('请先选择平台')
    return
  }
  
  try {
    searchLoading.value = true
    
    const response = await chemicalProductsApi.startSearch(searchForm.platform_id)
    
    if (response.data.err_code === 0) {
      ElMessage.success('抓取任务已启动')
    } else {
      ElMessage.error(response.data.err_msg || '启动抓取失败')
    }
  } catch (error) {
    console.error('启动抓取失败:', error)
    ElMessage.error('启动抓取失败')
  } finally {
    searchLoading.value = false
  }
}

// 删除产品
const deleteProduct = async (product: ChemicalProduct) => {
  try {
    await ElMessageBox.confirm(`确认删除产品"${product.product_name}"?`, '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    deleteLoading.value = true
    
    const response = await chemicalProductsApi.delete(product.id)
    
    if (response.data.err_code === 0) {
      ElMessage.success('删除成功')
      fetchData()
    } else {
      ElMessage.error(response.data.err_msg || '删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除产品失败:', error)
      ElMessage.error('删除失败')
    }
  } finally {
    deleteLoading.value = false
  }
}

// 下载数据
const downloadData = async () => {
  try {
    const params = {
      search_product_name: searchForm.product_name || undefined,
      search_compound_name: searchForm.compound_name || undefined,
      search_contact_number: searchForm.contact_number || undefined,
      search_platform_id: searchForm.platform_id || undefined
    }
    
    const response = await chemicalProductsApi.download(params)
    
    // 创建下载链接
    const blob = new Blob([response.data], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = 'chemical_products.csv'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('导出成功')
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败')
  }
}

// 获取状态类型
const getStatusType = (status: number) => {
  switch (status) {
    case 0: return 'warning'  // 待处理
    case 1: return 'primary'  // 处理中
    case 2: return 'success'  // 已处理
    default: return 'info'
  }
}

// 获取状态文本
const getStatusText = (status: number) => {
  switch (status) {
    case 0: return '待处理'
    case 1: return '处理中'
    case 2: return '已处理'
    default: return '未知'
  }
}

// 格式化日期时间
const formatDateTime = (dateTime: string): string => {
  if (!dateTime) return '-'
  try {
    return formatUTCToLocal(dateTime, 'YYYY-MM-DD HH:mm:ss')
  } catch (error) {
    return '-'
  }
}

// 计算表格最大高度
const calculateTableMaxHeight = () => {
  nextTick(() => {
    const windowHeight = window.innerHeight
    const cardHeaderHeight = 70
    const searchAreaHeight = 80
    const paginationHeight = 80
    const padding = 40
    
    const availableHeight = windowHeight - cardHeaderHeight - searchAreaHeight - paginationHeight - padding
    tableMaxHeight.value = Math.max(400, availableHeight)
  })
}

// 窗口大小变化监听
const handleResize = () => {
  calculateTableMaxHeight()
}

// 页面加载时获取数据
onMounted(() => {
  document.body.style.overflow = 'hidden'
  fetchData()
  calculateTableMaxHeight()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  document.body.style.overflow = 'auto'
  window.removeEventListener('resize', handleResize)
})
</script>

<style lang="scss" scoped>
.chemical-products {
  height: 100vh;
  padding: 0;
  margin: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.chemical-products > .el-card {
  width: 100%;
  flex: 1;
  margin: 0;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.chemical-products > .el-card > .el-card__body {
  padding: 20px;
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

/* 搜索区域样式 */
.search-area {
  margin-bottom: 20px;
  padding: 16px;
  background-color: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.search-form {
  margin: 0;
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

/* 表格单元格样式 */
.product-text, .compound-text {
  font-weight: 500;
  color: #303133;
}

.seller-text {
  color: #606266;
}

.contact-text {
  font-family: 'Courier New', monospace;
  font-size: 12px;
  color: #409eff;
}

.time-text {
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

/* 响应式设计 */
@media (max-width: 768px) {
  .header-actions {
    flex-direction: column;
    gap: 8px;
  }
  
  .search-form {
    .el-form-item {
      width: 100%;
      margin-bottom: 10px;
    }
  }
}
</style>