<template>
  <div class="website-settings">
    <!-- Telegram设置卡片 -->
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <span>Telegram设置</span>
        </div>
      </template>
      <div class="settings-content">
        <el-form :model="telegramForm" label-width="140px" :rules="telegramRules" ref="telegramFormRef">
          <div class="settings-section">
            <h4>API配置</h4>
            <el-form-item label="API ID" prop="api_id">
              <el-input v-model="telegramForm.api_id" placeholder="请输入Telegram API ID" />
            </el-form-item>
            <el-form-item label="API Hash" prop="api_hash">
              <el-input v-model="telegramForm.api_hash" placeholder="请输入Telegram API Hash" />
              <div class="form-tip">从 https://my.telegram.org/auth 获取，一般情况下请勿改动此两项</div>
            </el-form-item>
          </div>

          <div class="settings-section">
            <h4>Session配置</h4>
            <el-form-item label="SQLite数据库" prop="sqlite_db_name">
              <el-input v-model="telegramForm.sqlite_db_name" placeholder="jd_tg.db" />
            </el-form-item>
          </div>

          <div class="settings-section">
            <h4>代理配置</h4>
            <el-form-item label="启用代理">
              <el-switch v-model="telegramForm.proxy.enabled" />
              <div class="form-tip">关闭时将不使用代理连接</div>
            </el-form-item>
            <el-form-item label="协议类型">
              <el-select v-model="telegramForm.proxy.protocal" :disabled="!telegramForm.proxy.enabled">
                <el-option label="SOCKS5" value="socks5" />
                <el-option label="HTTP" value="http" />
              </el-select>
            </el-form-item>
            <el-form-item label="代理IP">
              <el-input v-model="telegramForm.proxy.ip" placeholder="127.0.0.1" :disabled="!telegramForm.proxy.enabled" />
            </el-form-item>
            <el-form-item label="端口">
              <el-input v-model="telegramForm.proxy.port" placeholder="7890" :disabled="!telegramForm.proxy.enabled" />
            </el-form-item>
          </div>

          <div class="settings-section">
            <h4>历史消息设置</h4>
            <el-form-item label="历史回溯天数" prop="history_days">
              <el-input-number v-model="telegramForm.history_days" :min="1" :max="365" />
              <div class="form-tip">Telegram群组历史回溯功能回溯历史消息的天数，加大此数值会加大服务器负担，建议不超过90天</div>
            </el-form-item>
          </div>

          <div class="settings-section">
            <h4>文件默认下载设置</h4>
            <div class="download-options-container">
              <div class="download-option">
                <el-checkbox v-model="telegramForm.download_settings.download_all" @change="handleDownloadAllChange">
                  下载所有文件
                </el-checkbox>
              </div>
              
              <div class="download-option">
                <el-checkbox 
                  v-model="telegramForm.download_settings.download_images"
                  :disabled="telegramForm.download_settings.download_all"
                >
                  图片文件
                </el-checkbox>
                <span class="file-types">（jpg, bmp, png, webp, tiff, gif）</span>
              </div>
              
              <div class="download-option">
                <el-checkbox 
                  v-model="telegramForm.download_settings.download_audio"
                  :disabled="telegramForm.download_settings.download_all"
                >
                  音频文件
                </el-checkbox>
                <span class="file-types">（mp3, flac, wav, ogg）</span>
              </div>
              
              <div class="download-option">
                <el-checkbox 
                  v-model="telegramForm.download_settings.download_videos"
                  :disabled="telegramForm.download_settings.download_all"
                >
                  视频文件
                </el-checkbox>
                <span class="file-types">（mp4, mkv, webm, mov）</span>
              </div>
              
              <div class="download-option">
                <el-checkbox 
                  v-model="telegramForm.download_settings.download_archives"
                  :disabled="telegramForm.download_settings.download_all"
                >
                  压缩包
                </el-checkbox>
                <span class="file-types">（zip, rar, 7z, gz, bz2）</span>
              </div>
              
              <div class="download-option">
                <el-checkbox 
                  v-model="telegramForm.download_settings.download_documents"
                  :disabled="telegramForm.download_settings.download_all"
                >
                  文档
                </el-checkbox>
                <span class="file-types">（pdf, doc(x), xls(x), ppt(x), txt）</span>
              </div>
              
              <div class="download-option">
                <el-checkbox 
                  v-model="telegramForm.download_settings.download_programs"
                  :disabled="telegramForm.download_settings.download_all"
                >
                  程序
                </el-checkbox>
                <span class="file-types">（apk, exe, elf）</span>
              </div>
            </div>
          </div>

          <div class="button-group">
            <el-button type="primary" @click="saveTelegramSettings" :loading="saving">保存设置</el-button>
            <el-button @click="resetTelegramForm">重置</el-button>
          </div>
        </el-form>
      </div>
    </el-card>

  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { systemApi, type TelegramSettings } from '@/api/system'

// 页面元信息
defineOptions({
  name: 'WebsiteSettings'
})

// 表单引用
const telegramFormRef = ref<FormInstance>()
const saving = ref(false)

// Telegram表单数据 - 不设置默认值，完全从后端加载
const telegramForm = reactive<TelegramSettings>({
  api_id: '',
  api_hash: '',
  sqlite_db_name: '',
  proxy: {
    enabled: false,
    protocal: '',
    ip: '',
    port: 0
  },
  history_days: 0,
  download_settings: {
    download_all: false,
    download_images: false,
    download_audio: false,
    download_videos: false,
    download_archives: false,
    download_documents: false,
    download_programs: false
  }
})

// 备份原始数据，用于重置
const originalTelegramForm = ref<TelegramSettings>()

// 表单验证规则
const telegramRules: FormRules = {
  api_id: [
    { required: true, message: '请输入API ID', trigger: 'blur' }
  ],
  api_hash: [
    { required: true, message: '请输入API Hash', trigger: 'blur' }
  ],
  history_days: [
    { required: true, message: '请输入历史回溯天数', trigger: 'blur' },
    { type: 'number', min: 1, max: 365, message: '天数必须在1-365之间', trigger: 'blur' }
  ]
}

// 获取Telegram设置
const loadTelegramSettings = async () => {
  try {
    const response = await systemApi.getTelegramSettings()
    if (response.data.err_code === 0) {
      const settings = response.data.payload
      // 直接使用后端返回的数据，不设置任何默认值
      Object.assign(telegramForm, settings)
      // 备份原始数据
      originalTelegramForm.value = JSON.parse(JSON.stringify(settings))
    } else {
      ElMessage.error(response.data.err_msg || '加载设置失败')
    }
  } catch (error) {
    console.error('加载Telegram设置失败:', error)
    ElMessage.error('加载设置失败')
  }
}

// 保存Telegram设置
const saveTelegramSettings = async () => {
  if (!telegramFormRef.value) return
  
  try {
    await telegramFormRef.value.validate()
    
    // 确认对话框
    await ElMessageBox.confirm(
      '保存设置会修改config.py文件，确定要保存吗？',
      '确认保存',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    saving.value = true
    
    const response = await systemApi.updateTelegramSettings(telegramForm)
    if (response.data.err_code === 0) {
      ElMessage.success('设置保存成功')
      // 更新备份数据
      originalTelegramForm.value = JSON.parse(JSON.stringify(telegramForm))
    } else {
      ElMessage.error(response.data.err_msg || '保存失败')
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('保存Telegram设置失败:', error)
      ElMessage.error('保存设置失败')
    }
  } finally {
    saving.value = false
  }
}

// 处理"下载所有文件"选择框变化
const handleDownloadAllChange = (value: boolean) => {
  if (value) {
    // 选中时，将所有其他选项设为true
    telegramForm.download_settings.download_images = true
    telegramForm.download_settings.download_audio = true
    telegramForm.download_settings.download_videos = true
    telegramForm.download_settings.download_archives = true
    telegramForm.download_settings.download_documents = true
    telegramForm.download_settings.download_programs = true
  }
}

// 重置表单
const resetTelegramForm = () => {
  if (originalTelegramForm.value) {
    Object.assign(telegramForm, JSON.parse(JSON.stringify(originalTelegramForm.value)))
  }
  telegramFormRef.value?.clearValidate()
}

// 页面加载时获取设置
onMounted(() => {
  loadTelegramSettings()
})
</script>

<style lang="scss" scoped>
.website-settings {
  padding: 20px;
  
  .box-card {
    max-width: 800px;
    margin-bottom: 20px;
  }
}

.card-header {
  display: flex;
  align-items: center;
  font-weight: bold;
  font-size: 16px;
}

.settings-content {
  .settings-section {
    margin-bottom: 30px;
    
    h4 {
      margin-bottom: 16px;
      color: #303133;
      font-weight: 600;
      font-size: 14px;
      border-bottom: 1px solid #ebeef5;
      padding-bottom: 8px;
    }
  }


  .button-group {
    text-align: right;
    margin-top: 40px;
    padding-top: 20px;
    border-top: 1px solid #ebeef5;
  }

  .form-tip {
    color: #909399;
    font-size: 12px;
    margin-top: 4px;
  }

  .download-options-container {
    .download-option {
      display: flex;
      align-items: flex-start;
      margin-bottom: 12px;
      
      .el-checkbox {
        min-width: 120px;
        margin-right: 8px;
      }
      
      .file-types {
        color: #909399;
        font-size: 12px;
        line-height: 32px; // 与checkbox高度对齐
      }
      
      .form-tip {
        color: #909399;
        font-size: 12px;
        margin-left: 128px; // 与文件类型说明对齐
        margin-top: 4px;
      }
    }
    
    .download-option:first-child {
      margin-bottom: 16px;
      padding-bottom: 12px;
      border-bottom: 1px solid #ebeef5;
    }
  }
}

:deep(.el-alert) {
  margin-bottom: 20px;
}

:deep(.el-form-item__label) {
  font-weight: 500;
}
</style>