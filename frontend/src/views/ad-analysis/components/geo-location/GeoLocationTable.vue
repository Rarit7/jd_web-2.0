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
        prop="province"
        label="省份"
        min-width="120"
      />
      <el-table-column
        prop="city"
        label="城市"
        width="150"
      >
        <template #default="{ row }">
          {{ row.city || '-' }}
        </template>
      </el-table-column>
      <el-table-column
        prop="count"
        label="热度"
        width="100"
        align="right"
        sortable
      />
      <el-table-column
        prop="percentage"
        label="占比"
        width="100"
        align="right"
      >
        <template #default="{ row }">
          {{ row.percentage ? row.percentage.toFixed(2) : 0 }}%
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
import type { GeoLocationData } from '@/types/adAnalysis'

interface Props {
  data: GeoLocationData[]
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
