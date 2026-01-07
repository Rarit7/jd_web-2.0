<template>
  <div class="table-container">
    <el-table
      :data="data"
      :default-sort="{ prop: 'count', order: 'descending' }"
      stripe
      style="width: 100%"
      v-loading="loading"
    >
      <el-table-column
        prop="id"
        label="ID"
        width="80"
        align="center"
      />
      <el-table-column
        prop="keyword"
        label="关键词"
        min-width="150"
      />
      <el-table-column
        prop="category"
        label="分类"
        width="120"
      />
      <el-table-column
        prop="drug_name"
        label="毒品名称"
        width="150"
      />
      <el-table-column
        prop="count"
        label="捕获次数"
        width="120"
        align="right"
        sortable
      />
      <el-table-column
        label="操作"
        width="120"
        align="center"
      >
        <template #default="{ row }">
          <el-popconfirm
            title="确定删除该黑词吗？"
            @confirm="handleDelete(row.id)"
          >
            <template #reference>
              <el-button link type="danger" size="small">
                删除
              </el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div class="pagination-container">
      <el-pagination
        v-model:current-page="currentPageLocal"
        v-model:page-size="pageSizeLocal"
        :page-sizes="[20, 50, 100]"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        @current-page-change="handlePageChange"
        @page-size-change="handlePageChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import type { DarkKeywordData } from '@/types/adAnalysis'

interface Props {
  data: DarkKeywordData[]
  loading: boolean
  total: number
  page: number
  pageSize: number
}

interface Emits {
  'page-change': [page: number]
  'delete': [id: number]
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const currentPageLocal = ref(props.page)
const pageSizeLocal = ref(props.pageSize)

watch(() => props.page, (newPage) => {
  currentPageLocal.value = newPage
})

watch(() => props.pageSize, (newSize) => {
  pageSizeLocal.value = newSize
})

function handlePageChange() {
  emit('page-change', currentPageLocal.value)
}

function handleDelete(id: number) {
  emit('delete', id)
}
</script>

<style scoped lang="scss">
.table-container {
  padding: 20px;

  .pagination-container {
    display: flex;
    justify-content: flex-end;
    margin-top: 20px;
    padding-top: 20px;
    border-top: 1px solid #ebeef5;
  }
}
</style>
