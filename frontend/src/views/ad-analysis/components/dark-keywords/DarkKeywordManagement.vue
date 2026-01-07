<template>
  <div class="dark-keyword-management">
    <!-- 三级展开表格 -->
    <el-table
      :data="categories"
      v-loading="loading"
      row-key="id"
      :tree-props="{ children: 'children', hasChildren: 'hasChildren' }"
      default-expand-all
      border
      stripe
    >
      <el-table-column prop="name" label="名称" min-width="200">
        <template #default="{ row }">
          <span v-if="row.__type === 'category'" class="category-name">
            {{ row.display_name || row.name }}
          </span>
          <span v-else-if="row.__type === 'drug'" class="drug-name">
            {{ row.display_name || row.name }}
          </span>
          <span v-else class="keyword-name">
            {{ row.keyword }}
          </span>
          <el-tag v-if="!row.is_active" type="info" size="small" style="margin-left: 8px">
            已禁用
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />

      <el-table-column prop="priority" label="优先级" width="100" align="center">
        <template #default="{ row }">
          <span v-if="row.__type === 'keyword'">{{ row.weight }}</span>
          <span v-else>{{ row.priority }}</span>
        </template>
      </el-table-column>

      <el-table-column label="操作" width="280" align="center">
        <template #default="{ row }">
          <!-- 分类操作 -->
          <template v-if="row.__type === 'category'">
            <el-button size="small" @click="handleEditCategory(row)">编辑</el-button>
            <el-button size="small" type="primary" @click="handleAddDrug(row)">添加毒品</el-button>
            <el-button
              size="small"
              type="danger"
              :disabled="row.children && row.children.length > 0"
              @click="handleDeleteCategory(row.id)"
            >
              删除
            </el-button>
          </template>

          <!-- 毒品操作 -->
          <template v-else-if="row.__type === 'drug'">
            <el-button size="small" @click="handleEditDrug(row)">编辑</el-button>
            <el-button size="small" type="primary" @click="handleAddKeyword(row)">添加关键词</el-button>
            <el-button
              size="small"
              type="danger"
              :disabled="row.children && row.children.length > 0"
              @click="handleDeleteDrug(row.id)"
            >
              删除
            </el-button>
          </template>

          <!-- 关键词操作 -->
          <template v-else-if="row.__type === 'keyword'">
            <el-button size="small" @click="handleEditKeyword(row)">编辑</el-button>
            <el-button
              size="small"
              type="danger"
              @click="handleDeleteKeyword(row.id)"
            >
              删除
            </el-button>
          </template>
        </template>
      </el-table-column>

      <el-table-column label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-switch
            v-model="row.is_active"
            @change="handleToggleStatus(row)"
          />
        </template>
      </el-table-column>
    </el-table>

    <!-- 添加分类按钮 -->
    <div class="add-category-btn">
      <el-button type="primary" @click="handleAddCategory">
        添加分类
      </el-button>
    </div>

    <!-- 分类编辑对话框 -->
    <el-dialog
      v-model="categoryDialogVisible"
      :title="categoryForm.id ? '编辑分类' : '添加分类'"
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
        <el-button @click="categoryDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveCategory">确定</el-button>
      </template>
    </el-dialog>

    <!-- 毒品编辑对话框 -->
    <el-dialog
      v-model="drugDialogVisible"
      :title="drugForm.id ? '编辑毒品' : '添加毒品'"
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
        <el-button @click="drugDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveDrug">确定</el-button>
      </template>
    </el-dialog>

    <!-- 关键词编辑对话框 -->
    <el-dialog
      v-model="keywordDialogVisible"
      :title="keywordForm.id ? '编辑关键词' : '添加关键词'"
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
        <el-button @click="keywordDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveKeyword">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
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
  __type: 'keyword'
}

interface Drug {
  id: number
  category_id: number
  name: string
  display_name?: string
  description?: string
  priority: number
  is_active: boolean
  children?: Keyword[]
  __type: 'drug'
}

interface Category {
  id: number
  name: string
  display_name?: string
  description?: string
  priority: number
  is_active: boolean
  children?: Drug[]
  __type: 'category'
}

// 状态
const loading = ref(false)
const categories = ref<Category[]>([])

// 分类表单
const categoryDialogVisible = ref(false)
const categoryForm = ref({
  id: null as number | null,
  name: '',
  display_name: '',
  description: '',
  priority: 0,
  is_active: true
})

// 毒品表单
const drugDialogVisible = ref(false)
const drugForm = ref({
  id: null as number | null,
  category_id: null as number | null,
  name: '',
  display_name: '',
  description: '',
  priority: 0,
  is_active: true
})

// 关键词表单
const keywordDialogVisible = ref(false)
const keywordForm = ref({
  id: null as number | null,
  drug_id: null as number | null,
  keyword: '',
  weight: 1,
  is_active: true
})

// 加载数据
async function loadData() {
  loading.value = true
  try {
    const response = await apiGetDarkKeywordCategoriesConfig()
    const result = response.payload.categories

    // 为每个分类加载毒品和关键词
    for (const category of result) {
      category.__type = 'category' as const
      const drugsResponse = await apiGetDarkKeywordDrugs({ category_id: category.id })
      const drugs = drugsResponse.payload.drugs

      for (const drug of drugs) {
        drug.__type = 'drug' as const
        const keywordsResponse = await apiGetDarkKeywordsByDrug(drug.id)
        const keywords = keywordsResponse.payload.keywords.map((kw: any) => ({
          ...kw,
          __type: 'keyword' as const
        }))
        // 使用 children 作为子节点属性名
        drug.children = keywords
      }
      // 使用 children 作为子节点属性名
      category.children = drugs
    }

    categories.value = result
  } catch (error) {
    console.error('加载黑词配置失败:', error)
    ElMessage.error('加载黑词配置失败')
  } finally {
    loading.value = false
  }
}

// 分类操作
function handleAddCategory() {
  categoryForm.value = {
    id: null,
    name: '',
    display_name: '',
    description: '',
    priority: 0,
    is_active: true
  }
  categoryDialogVisible.value = true
}

function handleEditCategory(row: Category) {
  categoryForm.value = {
    id: row.id,
    name: row.name,
    display_name: row.display_name || '',
    description: row.description || '',
    priority: row.priority,
    is_active: row.is_active
  }
  categoryDialogVisible.value = true
}

async function handleSaveCategory() {
  if (!categoryForm.value.name.trim()) {
    ElMessage.warning('请输入分类名称')
    return
  }

  try {
    if (categoryForm.value.id) {
      await apiUpdateDarkKeywordCategory(categoryForm.value.id, categoryForm.value)
      ElMessage.success('更新成功')
    } else {
      await apiCreateDarkKeywordCategory(categoryForm.value)
      ElMessage.success('添加成功')
    }
    categoryDialogVisible.value = false
    loadData()
  } catch (error: any) {
    ElMessage.error(error.message || '操作失败')
  }
}

async function handleDeleteCategory(id: number) {
  try {
    await ElMessageBox.confirm('确定要删除该分类吗？删除后无法恢复！', '警告', {
      type: 'warning'
    })
    await apiDeleteDarkKeywordCategory(id)
    ElMessage.success('删除成功')
    loadData()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除失败')
    }
  }
}

// 毒品操作
function handleAddDrug(row: Category) {
  drugForm.value = {
    id: null,
    category_id: row.id,
    name: '',
    display_name: '',
    description: '',
    priority: 0,
    is_active: true
  }
  drugDialogVisible.value = true
}

function handleEditDrug(row: Drug) {
  drugForm.value = {
    id: row.id,
    category_id: row.category_id,
    name: row.name,
    display_name: row.display_name || '',
    description: row.description || '',
    priority: row.priority,
    is_active: row.is_active
  }
  drugDialogVisible.value = true
}

async function handleSaveDrug() {
  if (!drugForm.value.name.trim()) {
    ElMessage.warning('请输入毒品名称')
    return
  }

  try {
    if (drugForm.value.id) {
      await apiUpdateDarkKeywordDrug(drugForm.value.id, drugForm.value)
      ElMessage.success('更新成功')
    } else {
      await apiCreateDarkKeywordDrug(drugForm.value)
      ElMessage.success('添加成功')
    }
    drugDialogVisible.value = false
    loadData()
  } catch (error: any) {
    ElMessage.error(error.message || '操作失败')
  }
}

async function handleDeleteDrug(id: number) {
  try {
    await ElMessageBox.confirm('确定要删除该毒品吗？删除后无法恢复！', '警告', {
      type: 'warning'
    })
    await apiDeleteDarkKeywordDrug(id)
    ElMessage.success('删除成功')
    loadData()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除失败')
    }
  }
}

// 关键词操作
function handleAddKeyword(row: Drug) {
  keywordForm.value = {
    id: null,
    drug_id: row.id,
    keyword: '',
    weight: 1,
    is_active: true
  }
  keywordDialogVisible.value = true
}

function handleEditKeyword(row: Keyword) {
  keywordForm.value = {
    id: row.id,
    drug_id: null,
    keyword: row.keyword,
    weight: row.weight,
    is_active: row.is_active
  }
  keywordDialogVisible.value = true
}

async function handleSaveKeyword() {
  if (!keywordForm.value.keyword.trim()) {
    ElMessage.warning('请输入关键词')
    return
  }

  try {
    if (keywordForm.value.id) {
      await apiUpdateDarkKeyword(keywordForm.value.id, {
        weight: keywordForm.value.weight,
        is_active: keywordForm.value.is_active
      })
      ElMessage.success('更新成功')
    } else {
      await apiCreateDarkKeyword({
        drug_id: keywordForm.value.drug_id!,
        keyword: keywordForm.value.keyword,
        weight: keywordForm.value.weight,
        is_active: keywordForm.value.is_active
      })
      ElMessage.success('添加成功')
    }
    keywordDialogVisible.value = false
    loadData()
  } catch (error: any) {
    ElMessage.error(error.message || '操作失败')
  }
}

async function handleDeleteKeyword(id: number) {
  try {
    await ElMessageBox.confirm('确定要删除该关键词吗？', '警告', {
      type: 'warning'
    })
    await apiDeleteDarkKeywordConfig(id)
    ElMessage.success('删除成功')
    loadData()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除失败')
    }
  }
}

// 切换状态
async function handleToggleStatus(row: any) {
  try {
    if (row.__type === 'category') {
      await apiUpdateDarkKeywordCategory(row.id, { is_active: row.is_active })
    } else if (row.__type === 'drug') {
      await apiUpdateDarkKeywordDrug(row.id, { is_active: row.is_active })
    } else if (row.__type === 'keyword') {
      await apiUpdateDarkKeyword(row.id, { is_active: row.is_active })
    }
    ElMessage.success('状态更新成功')
  } catch (error: any) {
    row.is_active = !row.is_active
    ElMessage.error(error.message || '状态更新失败')
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped lang="scss">
.dark-keyword-management {
  .category-name {
    font-weight: 600;
    color: #303133;
  }

  .drug-name {
    color: #409eff;
    padding-left: 20px;
  }

  .keyword-name {
    color: #67c23a;
    padding-left: 40px;
  }

  .add-category-btn {
    margin-top: 20px;
    text-align: center;
  }

  :deep(.el-table) {
    .el-table__row--level-1 .el-table__cell {
      background-color: #f5f7fa;
    }

    .el-table__row--level-2 .el-table__cell {
      background-color: #fafafa;
    }
  }
}
</style>
