<template>
  <div class="dark-keyword-management">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>黑词管理</span>
          <el-button type="primary" @click="showAddCategoryDialog = true">添加分类</el-button>
        </div>
      </template>

      <div v-loading="loading" class="content">
        <!-- 分类表 -->
        <el-table
          :data="categories"
          style="width: 100%"
          stripe
          @row-click="handleCategoryRowClick"
          :row-class-name="() => 'clickable-row'"
        >
          <!-- 分类名称 -->
          <el-table-column prop="name" label="分类" width="200">
            <template #default="{ row }">
              <div class="category-badge">
                <span class="category-name">{{ row.display_name || row.name }}</span>
                <el-tag v-if="!row.is_active" type="info" size="small">已禁用</el-tag>
              </div>
            </template>
          </el-table-column>

          <!-- 毒品数量 -->
          <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />

          <el-table-column label="毒品数量" width="100" align="center">
            <template #default="{ row }">
              <el-tag effect="light" type="info">
                {{ row.drugsCount || 0 }} 个
              </el-tag>
            </template>
          </el-table-column>

          <!-- 优先级 -->
          <el-table-column prop="priority" label="优先级" width="100" align="center" />

          <!-- 操作 -->
          <el-table-column label="操作" width="200" align="center">
            <template #default="{ row }">
              <div class="action-buttons">
                <el-button size="small" type="primary" @click.stop="editCategory(row)">
                  编辑
                </el-button>
                <el-button
                  size="small"
                  type="danger"
                  :disabled="row.drugsCount > 0"
                  @click.stop="deleteCategory(row.id)"
                >
                  删除
                </el-button>
              </div>
            </template>
          </el-table-column>

          <!-- 状态切换 -->
          <el-table-column label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-switch v-model="row.is_active" @change="handleCategoryStatusChange(row)" />
            </template>
          </el-table-column>
        </el-table>

        <!-- 分类展开面板 -->
        <el-collapse-transition>
          <div v-if="expandedCategoryId" class="detail-panel">
            <!-- 毒品列表 -->
            <div class="panel-header">
              <h3>
                <span>毒品管理 - </span>
                <span class="category-title">{{ expandedCategory?.display_name || expandedCategory?.name }}</span>
              </h3>
              <div class="panel-actions">
                <el-button type="primary" size="small" @click="showAddDrugDialog = true">
                  添加毒品
                </el-button>
                <el-button size="small" @click="expandedCategoryId = null">
                  收起
                </el-button>
              </div>
            </div>

            <el-table
              :data="expandedCategory?.drugs || []"
              style="width: 100%; margin-top: 16px"
              stripe
              @row-click="handleDrugRowClick"
              :row-class-name="() => 'clickable-row nested-row'"
            >
              <!-- 毒品名称 -->
              <el-table-column prop="name" label="毒品" width="200">
                <template #default="{ row }">
                  <div class="drug-badge">
                    <span class="drug-name">{{ row.display_name || row.name }}</span>
                    <el-tag v-if="!row.is_active" type="info" size="small">已禁用</el-tag>
                  </div>
                </template>
              </el-table-column>

              <!-- 描述 -->
              <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />

              <!-- 关键词数量 -->
              <el-table-column label="关键词数" width="100" align="center">
                <template #default="{ row }">
                  <el-tag effect="light" type="success">
                    {{ row.keywordsCount || 0 }} 个
                  </el-tag>
                </template>
              </el-table-column>

              <!-- 优先级 -->
              <el-table-column prop="priority" label="优先级" width="100" align="center" />

              <!-- 操作 -->
              <el-table-column label="操作" width="200" align="center">
                <template #default="{ row }">
                  <div class="action-buttons">
                    <el-button size="small" type="primary" @click.stop="editDrug(row)">
                      编辑
                    </el-button>
                    <el-button
                      size="small"
                      type="danger"
                      :disabled="row.keywordsCount > 0"
                      @click.stop="deleteDrug(row.id)"
                    >
                      删除
                    </el-button>
                  </div>
                </template>
              </el-table-column>

              <!-- 状态 -->
              <el-table-column label="状态" width="100" align="center">
                <template #default="{ row }">
                  <el-switch v-model="row.is_active" @change="handleDrugStatusChange(row)" />
                </template>
              </el-table-column>
            </el-table>

            <!-- 关键词展开面板 -->
            <el-collapse-transition>
              <div v-if="expandedDrugId && expandedDrug" class="detail-panel nested-panel">
                <div class="panel-header">
                  <h3>
                    <span>关键词管理 - </span>
                    <span class="drug-title">{{ expandedDrug.display_name || expandedDrug.name }}</span>
                  </h3>
                  <div class="panel-actions">
                    <el-button type="primary" size="small" @click="showAddKeywordDialog = true">
                      添加关键词
                    </el-button>
                    <el-button size="small" @click="expandedDrugId = null">
                      收起
                    </el-button>
                  </div>
                </div>

                <div class="keywords-panel">
                  <template v-if="expandedDrug.keywords && expandedDrug.keywords.length > 0">
                    <div class="keywords-list">
                      <div
                        v-for="kw in expandedDrug.keywords"
                        :key="kw.id"
                        class="keyword-item"
                      >
                        <div class="keyword-chip">
                          <span class="keyword-text">{{ kw.keyword }}</span>
                          <span class="keyword-weight">权重: {{ kw.weight }}</span>
                        </div>
                        <div class="keyword-actions">
                          <el-switch
                            v-model="kw.is_active"
                            @change="handleKeywordStatusChange(kw)"
                            size="small"
                          />
                          <el-button
                            size="small"
                            type="primary"
                            text
                            @click="editKeyword(kw)"
                          >
                            编辑
                          </el-button>
                          <el-button
                            size="small"
                            type="danger"
                            text
                            @click="deleteKeyword(kw.id)"
                          >
                            删除
                          </el-button>
                        </div>
                      </div>
                    </div>
                  </template>
                  <el-empty v-else description="暂无关键词" />
                </div>
              </div>
            </el-collapse-transition>
          </div>
        </el-collapse-transition>
      </div>
    </el-card>

    <!-- 分类对话框 -->
    <el-dialog
      v-model="showAddCategoryDialog"
      :title="editingCategory ? '编辑分类' : '添加分类'"
      width="500px"
    >
      <el-form :model="categoryForm" label-width="100px">
        <el-form-item label="分类名称">
          <el-input v-model="categoryForm.name" placeholder="请输入分类名称" />
        </el-form-item>
        <el-form-item label="显示名称">
          <el-input v-model="categoryForm.display_name" placeholder="请输入显示名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="categoryForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入描述"
          />
        </el-form-item>
        <el-form-item label="优先级">
          <el-input-number v-model="categoryForm.priority" :min="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddCategoryDialog = false">取消</el-button>
        <el-button type="primary" @click="saveCategory">确定</el-button>
      </template>
    </el-dialog>

    <!-- 毒品对话框 -->
    <el-dialog
      v-model="showAddDrugDialog"
      :title="editingDrug ? '编辑毒品' : '添加毒品'"
      width="500px"
    >
      <el-form :model="drugForm" label-width="100px">
        <el-form-item label="毒品名称">
          <el-input v-model="drugForm.name" placeholder="请输入毒品名称" />
        </el-form-item>
        <el-form-item label="显示名称">
          <el-input v-model="drugForm.display_name" placeholder="请输入显示名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="drugForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入描述"
          />
        </el-form-item>
        <el-form-item label="优先级">
          <el-input-number v-model="drugForm.priority" :min="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDrugDialog = false">取消</el-button>
        <el-button type="primary" @click="saveDrug">确定</el-button>
      </template>
    </el-dialog>

    <!-- 关键词对话框 -->
    <el-dialog
      v-model="showAddKeywordDialog"
      :title="editingKeyword ? '编辑关键词' : '添加关键词'"
      width="500px"
    >
      <el-form :model="keywordForm" label-width="100px">
        <el-form-item label="关键词">
          <el-input v-model="keywordForm.keyword" placeholder="请输入关键词" />
        </el-form-item>
        <el-form-item label="权重">
          <el-input-number v-model="keywordForm.weight" :min="1" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddKeywordDialog = false">取消</el-button>
        <el-button type="primary" @click="saveKeyword">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  apiGetDarkKeywordCategoriesConfig,
  apiGetDarkKeywordDrugs,
  apiGetDarkKeywordsByDrug,
  apiCreateDarkKeywordCategory,
  apiUpdateDarkKeywordCategory,
  apiDeleteDarkKeywordCategory,
  apiCreateDarkKeywordDrug,
  apiUpdateDarkKeywordDrug,
  apiDeleteDarkKeywordDrug,
  apiCreateDarkKeyword,
  apiUpdateDarkKeyword,
  apiDeleteDarkKeywordConfig
} from '@/api/adAnalysis'

// 类型定义
interface Keyword {
  id: number
  keyword: string
  weight: number
  is_active: boolean
}

interface Drug {
  id: number
  category_id: number
  name: string
  display_name?: string
  description?: string
  priority: number
  is_active: boolean
  keywords?: Keyword[]
  keywordsCount: number
}

interface Category {
  id: number
  name: string
  display_name?: string
  description?: string
  priority: number
  is_active: boolean
  drugs?: Drug[]
  drugsCount: number
}

// 状态
const loading = ref(false)
const categories = ref<Category[]>([])
const expandedCategoryId = ref<number | null>(null)
const expandedDrugId = ref<number | null>(null)

// 对话框
const showAddCategoryDialog = ref(false)
const showAddDrugDialog = ref(false)
const showAddKeywordDialog = ref(false)

// 编辑状态标记
const editingCategory = ref(false)
const editingDrug = ref(false)
const editingKeyword = ref(false)

// 分类表单
const categoryForm = ref({
  id: null as number | null,
  name: '',
  display_name: '',
  description: '',
  priority: 0
})

// 毒品表单
const drugForm = ref({
  id: null as number | null,
  category_id: null as number | null,
  name: '',
  display_name: '',
  description: '',
  priority: 0
})

// 关键词表单
const keywordForm = ref({
  id: null as number | null,
  drug_id: null as number | null,
  keyword: '',
  weight: 1
})

// 计算属性
const expandedCategory = computed(() => {
  return categories.value.find(c => c.id === expandedCategoryId.value)
})

const expandedDrug = computed(() => {
  return expandedCategory.value?.drugs?.find(d => d.id === expandedDrugId.value)
})

// 加载数据
async function loadData() {
  loading.value = true
  try {
    const response = await apiGetDarkKeywordCategoriesConfig()
    const result = response.payload.categories

    for (const category of result) {
      const drugsResponse = await apiGetDarkKeywordDrugs({ category_id: category.id })
      const drugs = drugsResponse.payload.drugs || []

      for (const drug of drugs) {
        const keywordsResponse = await apiGetDarkKeywordsByDrug(drug.id)
        const keywords = keywordsResponse.payload.keywords || []
        drug.keywords = keywords
        drug.keywordsCount = keywords.length
      }

      category.drugs = drugs
      category.drugsCount = drugs.length
    }

    categories.value = result
  } catch (error) {
    console.error('加载黑词配置失败:', error)
    ElMessage.error('加载黑词配置失败')
  } finally {
    loading.value = false
  }
}

// 行点击处理
function handleCategoryRowClick(row: Category) {
  if (expandedCategoryId.value === row.id) {
    expandedCategoryId.value = null
    expandedDrugId.value = null
  } else {
    expandedCategoryId.value = row.id
    expandedDrugId.value = null
  }
}

function handleDrugRowClick(row: Drug) {
  if (expandedDrugId.value === row.id) {
    expandedDrugId.value = null
  } else {
    expandedDrugId.value = row.id
  }
}

// 分类操作
function editCategory(row: Category) {
  editingCategory.value = true
  categoryForm.value = {
    id: row.id,
    name: row.name,
    display_name: row.display_name || '',
    description: row.description || '',
    priority: row.priority
  }
  showAddCategoryDialog.value = true
}

async function saveCategory() {
  if (!categoryForm.value.name.trim()) {
    ElMessage.warning('请输入分类名称')
    return
  }

  try {
    if (categoryForm.value.id) {
      await apiUpdateDarkKeywordCategory(categoryForm.value.id, {
        display_name: categoryForm.value.display_name,
        description: categoryForm.value.description,
        priority: categoryForm.value.priority
      })
      ElMessage.success('更新成功')
    } else {
      await apiCreateDarkKeywordCategory(categoryForm.value)
      ElMessage.success('添加成功')
    }
    showAddCategoryDialog.value = false
    editingCategory.value = false
    resetCategoryForm()
    loadData()
  } catch (error: any) {
    ElMessage.error(error.message || '操作失败')
  }
}

async function deleteCategory(id: number) {
  try {
    await ElMessageBox.confirm('确定要删除该分类吗？', '警告', { type: 'warning' })
    await apiDeleteDarkKeywordCategory(id)
    ElMessage.success('删除成功')
    loadData()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除失败')
    }
  }
}

async function handleCategoryStatusChange(row: Category) {
  try {
    await apiUpdateDarkKeywordCategory(row.id, { is_active: row.is_active })
    ElMessage.success('状态更新成功')
  } catch (error: any) {
    row.is_active = !row.is_active
    ElMessage.error(error.message || '状态更新失败')
  }
}

function resetCategoryForm() {
  categoryForm.value = {
    id: null,
    name: '',
    display_name: '',
    description: '',
    priority: 0
  }
}

// 毒品操作
function editDrug(row: Drug) {
  editingDrug.value = true
  drugForm.value = {
    id: row.id,
    category_id: row.category_id,
    name: row.name,
    display_name: row.display_name || '',
    description: row.description || '',
    priority: row.priority
  }
  showAddDrugDialog.value = true
}

async function saveDrug() {
  if (!drugForm.value.name.trim()) {
    ElMessage.warning('请输入毒品名称')
    return
  }

  try {
    if (drugForm.value.id) {
      await apiUpdateDarkKeywordDrug(drugForm.value.id, {
        display_name: drugForm.value.display_name,
        description: drugForm.value.description,
        priority: drugForm.value.priority
      })
      ElMessage.success('更新成功')
    } else {
      await apiCreateDarkKeywordDrug({
        category_id: drugForm.value.category_id!,
        name: drugForm.value.name,
        display_name: drugForm.value.display_name,
        description: drugForm.value.description,
        priority: drugForm.value.priority
      })
      ElMessage.success('添加成功')
    }
    showAddDrugDialog.value = false
    editingDrug.value = false
    resetDrugForm()
    loadData()
  } catch (error: any) {
    ElMessage.error(error.message || '操作失败')
  }
}

async function deleteDrug(id: number) {
  try {
    await ElMessageBox.confirm('确定要删除该毒品吗？', '警告', { type: 'warning' })
    await apiDeleteDarkKeywordDrug(id)
    ElMessage.success('删除成功')
    loadData()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除失败')
    }
  }
}

async function handleDrugStatusChange(row: Drug) {
  try {
    await apiUpdateDarkKeywordDrug(row.id, { is_active: row.is_active })
    ElMessage.success('状态更新成功')
  } catch (error: any) {
    row.is_active = !row.is_active
    ElMessage.error(error.message || '状态更新失败')
  }
}

function resetDrugForm() {
  drugForm.value = {
    id: null,
    category_id: expandedCategoryId.value,
    name: '',
    display_name: '',
    description: '',
    priority: 0
  }
}

// 关键词操作
function editKeyword(row: Keyword) {
  editingKeyword.value = true
  keywordForm.value = {
    id: row.id,
    drug_id: expandedDrugId.value,
    keyword: row.keyword,
    weight: row.weight
  }
  showAddKeywordDialog.value = true
}

async function saveKeyword() {
  if (!keywordForm.value.keyword.trim()) {
    ElMessage.warning('请输入关键词')
    return
  }

  try {
    if (keywordForm.value.id) {
      await apiUpdateDarkKeyword(keywordForm.value.id, {
        weight: keywordForm.value.weight
      })
      ElMessage.success('更新成功')
    } else {
      await apiCreateDarkKeyword({
        drug_id: keywordForm.value.drug_id!,
        keyword: keywordForm.value.keyword,
        weight: keywordForm.value.weight
      })
      ElMessage.success('添加成功')
    }
    showAddKeywordDialog.value = false
    editingKeyword.value = false
    resetKeywordForm()
    loadData()
  } catch (error: any) {
    ElMessage.error(error.message || '操作失败')
  }
}

async function deleteKeyword(id: number) {
  try {
    await ElMessageBox.confirm('确定要删除该关键词吗？', '警告', { type: 'warning' })
    await apiDeleteDarkKeywordConfig(id)
    ElMessage.success('删除成功')
    loadData()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除失败')
    }
  }
}

async function handleKeywordStatusChange(row: Keyword) {
  try {
    await apiUpdateDarkKeyword(row.id, { is_active: row.is_active })
    ElMessage.success('状态更新成功')
  } catch (error: any) {
    row.is_active = !row.is_active
    ElMessage.error(error.message || '状态更新失败')
  }
}

function resetKeywordForm() {
  keywordForm.value = {
    id: null,
    drug_id: expandedDrugId.value,
    keyword: '',
    weight: 1
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped lang="scss">
.dark-keyword-management {
  height: 100%;

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .content {
    min-height: 400px;
  }

  /* 可点击的表格行 */
  :deep(.clickable-row) {
    cursor: pointer;
    transition: background-color 0.2s;
  }

  :deep(.clickable-row:hover) {
    background-color: #f5f7fa !important;
  }

  :deep(.nested-row:hover) {
    background-color: #ecf5ff !important;
  }

  /* 分类和毒品名称样式 */
  .category-badge,
  .drug-badge {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .category-name {
    font-weight: 600;
    color: #303133;
  }

  .drug-name {
    color: #409eff;
    font-weight: 500;
  }

  .category-title {
    font-weight: 600;
    color: #303133;
    margin-left: 4px;
  }

  .drug-title {
    color: #409eff;
    font-weight: 600;
    margin-left: 4px;
  }

  /* 操作按钮 */
  .action-buttons {
    display: flex;
    gap: 6px;
    justify-content: center;
  }

  /* 详情面板 */
  .detail-panel {
    margin-top: 20px;
    padding: 20px;
    background: #f5f7fa;
    border-radius: 8px;
    border-left: 4px solid #409eff;
  }

  .detail-panel.nested-panel {
    margin-top: 20px;
    background: #ecf5ff;
    border-left-color: #67c23a;
  }

  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid #dcdfe6;
  }

  .panel-header h3 {
    margin: 0;
    font-size: 16px;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 4px;
  }

  .panel-actions {
    display: flex;
    gap: 8px;
  }

  /* 关键词面板 */
  .keywords-panel {
    padding: 16px 0;
  }

  .keywords-list {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    align-items: flex-start;
  }

  .keyword-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 8px 12px;
    background: white;
    border-radius: 6px;
    border: 1px solid #dcdfe6;
    transition: all 0.3s ease;
  }

  .keyword-item:hover {
    border-color: #67c23a;
    box-shadow: 0 2px 8px rgba(103, 194, 58, 0.15);
  }

  .keyword-chip {
    display: flex;
    flex-direction: column;
    gap: 4px;
    flex: 1;
  }

  .keyword-text {
    font-size: 14px;
    font-weight: 500;
    color: #303133;
    word-break: break-word;
  }

  .keyword-weight {
    font-size: 12px;
    color: #909399;
  }

  .keyword-actions {
    display: flex;
    align-items: center;
    gap: 8px;
    white-space: nowrap;
  }
}
</style>
