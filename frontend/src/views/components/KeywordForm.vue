<template>
  <div class="keyword-form">
    <el-form :model="form" :rules="rules" ref="formRef" label-width="120px">
      <el-form-item label="选择标签" prop="tag_id" v-if="!tagId">
        <el-select
          v-model="form.tag_id"
          placeholder="请选择标签"
          style="width: 100%"
        >
          <el-option
            v-for="tag in tags"
            :key="tag.id"
            :label="tag.name"
            :value="tag.id"
          >
            <div style="display: flex; align-items: center;">
              <el-tag :color="tag.color" effect="dark" size="small" style="margin-right: 8px; color: white; border: none;">
                {{ tag.name }}
              </el-tag>
            </div>
          </el-option>
        </el-select>
      </el-form-item>

      <el-form-item label="关键词" prop="keyword">
        <el-input
          v-model="form.keyword"
          placeholder="请输入关键词"
          maxlength="255"
          show-word-limit
        />
        <div class="form-tip">
          输入关键词后，当用户对话、昵称或描述中包含此关键词时，将自动为用户添加对应标签
        </div>
      </el-form-item>

      <el-form-item label="自动关注">
        <el-switch
          v-model="form.auto_focus"
          active-text="是"
          inactive-text="否"
        />
        <div class="form-tip">
          开启后，匹配到此关键词的用户将自动加入特别关注列表
        </div>
      </el-form-item>

      <el-form-item label="状态">
        <el-switch
          v-model="form.is_active"
          active-text="启用"
          inactive-text="禁用"
        />
        <div class="form-tip">
          只有启用状态的关键词才会参与自动标签匹配
        </div>
      </el-form-item>

      <!-- 预览功能 -->
      <el-form-item label="效果预览" v-if="form.keyword">
        <el-input
          v-model="previewText"
          type="textarea"
          :rows="3"
          placeholder="输入文本来预览关键词匹配效果"
        />
        <div class="preview-actions">
          <el-button size="small" @click="handlePreview" :loading="previewLoading">
            预览效果
          </el-button>
        </div>
        <div v-if="previewResult" class="preview-result">
          <div class="preview-title">预览结果：</div>
          <div v-if="previewResult.matched_count > 0" class="preview-match">
            <el-icon class="success-icon"><SuccessFilled /></el-icon>
            找到匹配！将为用户添加标签
          </div>
          <div v-else class="preview-no-match">
            <el-icon class="warning-icon"><WarningFilled /></el-icon>
            未找到匹配
          </div>
        </div>
      </el-form-item>
    </el-form>

    <div class="form-actions">
      <el-button @click="handleCancel">取消</el-button>
      <el-button type="primary" @click="handleSubmit" :loading="loading">
        {{ isEdit ? '保存' : '添加' }}
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { SuccessFilled, WarningFilled } from '@element-plus/icons-vue'
import type { FormInstance } from 'element-plus'
import { tagsApi, type Tag } from '@/api/tags'

interface Props {
  tagId?: number
  keywordData?: any
}

interface Emits {
  (e: 'success'): void
  (e: 'cancel'): void
}

const props = withDefaults(defineProps<Props>(), {
  tagId: undefined,
  keywordData: undefined
})

const emit = defineEmits<Emits>()

// 响应式数据
const loading = ref(false)
const previewLoading = ref(false)
const tags = ref<Tag[]>([])
const formRef = ref<FormInstance>()
const previewText = ref('')
const previewResult = ref<any>()

// 表单数据
const form = reactive({
  tag_id: props.tagId || 0,
  keyword: '',
  auto_focus: false,
  is_active: true
})

// 表单验证规则
const rules = {
  tag_id: [
    { required: true, message: '请选择标签', trigger: 'change' }
  ],
  keyword: [
    { required: true, message: '请输入关键词', trigger: 'blur' },
    { min: 1, max: 255, message: '关键词长度在1到255个字符之间', trigger: 'blur' }
  ]
}

// 计算属性
const isEdit = computed(() => !!props.keywordData)

// 获取标签列表
const fetchTags = async () => {
  if (props.tagId) return // 如果已指定标签ID，无需获取列表

  try {
    const response = await tagsApi.getList()
    if (response.err_code === 0) {
      tags.value = response.payload.data
    }
  } catch (error) {
    console.error('获取标签列表失败:', error)
  }
}

// 预览效果
const handlePreview = async () => {
  if (!previewText.value.trim()) {
    ElMessage.warning('请输入预览文本')
    return
  }

  previewLoading.value = true
  try {
    const response = await tagsApi.previewAutoTagging({
      text: previewText.value
    })

    if (response.err_code === 0) {
      previewResult.value = response.payload
    } else {
      ElMessage.error(response.err_msg || '预览失败')
    }
  } catch (error) {
    console.error('预览失败:', error)
    ElMessage.error('预览失败')
  } finally {
    previewLoading.value = false
  }
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    loading.value = true

    const data = {
      tag_id: form.tag_id,
      keyword: form.keyword.trim(),
      auto_focus: form.auto_focus,
      is_active: form.is_active
    }

    let response
    if (isEdit.value) {
      response = await tagsApi.updateKeywordMapping(props.keywordData.id, data)
    } else {
      response = await tagsApi.createKeywordMapping(data)
    }

    if (response.err_code === 0) {
      emit('success')
    } else {
      ElMessage.error(response.err_msg || `${isEdit.value ? '更新' : '添加'}失败`)
    }
  } catch (error) {
    console.error(`${isEdit.value ? '更新' : '添加'}关键词失败:`, error)
    ElMessage.error(`${isEdit.value ? '更新' : '添加'}失败`)
  } finally {
    loading.value = false
  }
}

// 取消操作
const handleCancel = () => {
  emit('cancel')
}

// 初始化数据
const initializeData = () => {
  if (props.keywordData) {
    form.tag_id = props.keywordData.tag_id
    form.keyword = props.keywordData.keyword
    form.auto_focus = props.keywordData.auto_focus
    form.is_active = props.keywordData.is_active
  } else if (props.tagId) {
    form.tag_id = props.tagId
  }
}

// 页面加载时初始化
onMounted(() => {
  fetchTags()
  initializeData()
})
</script>

<style scoped>
.keyword-form {
  padding: 20px 0;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  line-height: 1.4;
}

.preview-actions {
  margin-top: 8px;
}

.preview-result {
  margin-top: 12px;
  padding: 12px;
  border-radius: 4px;
  background-color: #f5f7fa;
}

.preview-title {
  font-weight: 500;
  margin-bottom: 8px;
  color: #606266;
}

.preview-match {
  display: flex;
  align-items: center;
  color: #67c23a;
  font-size: 14px;
}

.preview-no-match {
  display: flex;
  align-items: center;
  color: #e6a23c;
  font-size: 14px;
}

.success-icon,
.warning-icon {
  margin-right: 6px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #e4e7ed;
}
</style>