<template>
  <div class="table-container">
    <el-table
      :data="data"
      :default-sort="{ prop: 'created_at', order: 'descending' }"
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
        prop="product_name"
        label="产品名称"
        min-width="150"
      />
      <el-table-column
        prop="unit"
        label="单位"
        width="100"
      />
      <el-table-column
        prop="price"
        label="价格"
        width="120"
        align="right"
        sortable
      >
        <template #default="{ row }">
          ¥{{ row.price !== undefined && row.price !== null ? Number(row.price).toFixed(2) : '-' }}
        </template>
      </el-table-column>
      <el-table-column
        prop="created_at"
        label="记录时间"
        width="180"
        align="center"
        sortable
      >
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
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
import type { PriceHistoryRecord } from '@/types/adAnalysis'

interface Props {
  data: PriceHistoryRecord[]
  loading: boolean
  total: number
  page: number
  pageSize: number
}

interface Emits {
  'page-change': [page: number]
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

function formatDate(dateStr: string | undefined) {
  if (!dateStr) return '-'
  try {
    const date = new Date(dateStr)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return dateStr
  }
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
