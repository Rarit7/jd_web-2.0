<template>
  <el-dialog
    v-model="visible"
    :title="dialogTitle"
    width="400px"
    @close="resetForm"
  >
    <!-- 添加和编辑模式的表单 -->
    <el-form
      v-if="mode !== 'delete'"
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="80px"
    >
      <el-form-item label="文件夹名" prop="name">
        <el-input
          v-model="formData.name"
          placeholder="请输入文件夹名称"
          clearable
          @keydown.enter="handleSubmit"
        />
      </el-form-item>
    </el-form>

    <!-- 删除模式的确认提示 -->
    <div v-if="mode === 'delete'">
      <el-alert
        type="warning"
        :closable="false"
        show-icon
      >
        <template #default>
          <div>
            <p style="margin: 0 0 8px 0;">
              确认删除文件夹 <strong>{{ formData.name }}</strong> 吗？
            </p>
            <p style="margin: 0 0 8px 0; color: #606266; font-size: 12px;">
              ⚠️ 其下的所有子文件夹也将被删除
            </p>
            <p style="margin: 0; color: #606266; font-size: 12px;">
              💡 提示：文件夹中的档案会自动移至根目录，不会丢失
            </p>
          </div>
        </template>
      </el-alert>
    </div>

    <template #footer>
      <span class="dialog-footer">
        <el-button @click="visible = false">取消</el-button>
        <el-button
          type="danger"
          v-if="mode === 'delete'"
          :loading="loading"
          @click="handleSubmit"
        >
          确认删除
        </el-button>
        <el-button
          type="primary"
          v-else
          :loading="loading"
          @click="handleSubmit"
        >
          {{ mode === 'add' ? '创建' : '保存' }}
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { ElMessage, ElForm } from 'element-plus'
import { profileFolderApi } from '@/api/user-profile'

interface FormDataType {
  name: string
}

type FolderManagerMode = 'add' | 'edit' | 'delete'

const props = defineProps<{
  parentFolderId?: number | null
  currentFolderId?: number
  currentFolderName?: string
  userId: number
}>()

const emit = defineEmits<{
  success: []
}>()

const visible = ref(false)
const mode = ref<FolderManagerMode>('add')
const loading = ref(false)
const formRef = ref<InstanceType<typeof ElForm>>()

const formData = reactive<FormDataType>({
  name: ''
})

const rules = {
  name: [
    { required: true, message: '请输入文件夹名称', trigger: 'blur' },
    { min: 1, max: 100, message: '文件夹名称长度在 1 到 100 个字符之间', trigger: 'blur' }
  ]
}

const dialogTitle = computed(() => {
  const titles = {
    add: '新建文件夹',
    edit: '编辑文件夹',
    delete: '删除文件夹'
  }
  return titles[mode.value]
})

// 打开添加对话框
const openAdd = () => {
  mode.value = 'add'
  formData.name = ''
  visible.value = true
}

// 打开编辑对话框
const openEdit = (_folderId: number, folderName: string) => {
  mode.value = 'edit'
  formData.name = folderName
  visible.value = true
}

// 打开删除确认对话框
const openDelete = (_folderId: number, folderName: string) => {
  mode.value = 'delete'
  formData.name = folderName
  visible.value = true
}

const handleSubmit = async () => {
  if (mode.value === 'delete') {
    // 删除模式不需要表单验证
    await handleDelete()
  } else {
    // 添加和编辑模式需要表单验证
    if (!formRef.value) return
    await formRef.value.validate(async (valid) => {
      if (valid) {
        if (mode.value === 'add') {
          await handleAdd()
        } else {
          await handleEdit()
        }
      }
    })
  }
}

const handleAdd = async () => {
  try {
    loading.value = true
    const response = await profileFolderApi.create({
      name: formData.name,
      user_id: props.userId,
      parent_id: props.parentFolderId || null
    })

    if ((response.data as any).err_code === 0) {
      ElMessage.success('文件夹创建成功')
      visible.value = false
      emit('success')
    } else {
      ElMessage.error((response.data as any).err_msg || '创建文件夹失败')
    }
  } catch (error: any) {
    console.error('创建文件夹失败:', error)
    ElMessage.error('创建文件夹失败')
  } finally {
    loading.value = false
  }
}

const handleEdit = async () => {
  if (!props.currentFolderId) return

  try {
    loading.value = true
    const response = await profileFolderApi.update(props.currentFolderId, {
      name: formData.name
    })

    if ((response.data as any).err_code === 0) {
      ElMessage.success('文件夹更新成功')
      visible.value = false
      emit('success')
    } else {
      ElMessage.error((response.data as any).err_msg || '更新文件夹失败')
    }
  } catch (error: any) {
    console.error('更新文件夹失败:', error)
    ElMessage.error('更新文件夹失败')
  } finally {
    loading.value = false
  }
}

const handleDelete = async () => {
  if (!props.currentFolderId) return

  try {
    loading.value = true
    const response = await profileFolderApi.delete(props.currentFolderId)

    if ((response.data as any).err_code === 0) {
      const movedCount = (response.data as any).payload?.moved_profiles_count || 0
      const message = movedCount > 0
        ? `文件夹删除成功，已将 ${movedCount} 个档案移至根目录`
        : '文件夹删除成功'
      ElMessage.success(message)
      visible.value = false
      emit('success')
    } else {
      ElMessage.error((response.data as any).err_msg || '删除文件夹失败')
    }
  } catch (error: any) {
    console.error('删除文件夹失败:', error)
    ElMessage.error('删除文件夹失败')
  } finally {
    loading.value = false
  }
}

const resetForm = () => {
  if (formRef.value) {
    formRef.value.clearValidate()
  }
  formData.name = ''
}

// 暴露方法供父组件调用
defineExpose({
  openAdd,
  openEdit,
  openDelete,
  visible
})
</script>

<style scoped lang="scss">
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
