<template>
  <el-drawer
    v-model="adTrackingStore.showDetailDrawer"
    title="广告详情"
    size="600px"
    :close-on-click-modal="false"
    @close="adTrackingStore.closeDetailDrawer()"
  >
    <div v-if="detail" v-loading="adTrackingStore.loading.detail" class="detail-content">
      <!-- 基本信息 -->
      <div class="section">
        <h4>基本信息</h4>

        <el-descriptions :column="1" border>
          <el-descriptions-item label="广告内容">
            <div class="content-display">
              <el-text>{{ detail.content }}</el-text>
              <el-button link type="primary" size="small" @click="copyContent(detail.content)">
                复制
              </el-button>
            </div>
          </el-descriptions-item>

          <el-descriptions-item label="标准化内容">
            {{ detail.normalized_content }}
          </el-descriptions-item>

          <el-descriptions-item label="内容类型">
            <el-tag :type="getContentTypeTagType(detail.content_type)" size="small">
              {{ getContentTypeLabel(detail.content_type) }}
            </el-tag>
          </el-descriptions-item>

          <el-descriptions-item label="来源类型">
            {{ getSourceTypeLabel(detail.source_type) }}
          </el-descriptions-item>

          <el-descriptions-item label="首次发现">
            {{ formatDateTime(detail.first_seen) }}
          </el-descriptions-item>

          <el-descriptions-item label="最后发现">
            {{ formatDateTime(detail.last_seen) }}
          </el-descriptions-item>

          <el-descriptions-item label="出现次数">
            <el-tag type="primary">{{ detail.occurrence_count }}</el-tag>
          </el-descriptions-item>
        </el-descriptions>
      </div>

      <!-- 来源信息 -->
      <div class="section">
        <h4>来源信息</h4>

        <!-- 聊天消息来源 -->
        <div v-if="detail.source_type === 'chat'" class="source-content">
          <el-descriptions :column="1" border>
            <el-descriptions-item v-if="detail.group_info" label="群组">
              <div class="entity-info">
                <el-avatar v-if="detail.group_info.avatar_url" :src="detail.group_info.avatar_url" :size="32" />
                <el-avatar v-else :size="32">{{ (detail.group_info.group_name || 'G')[0] }}</el-avatar>
                <div class="entity-details">
                  <div class="entity-name">{{ detail.group_info.group_title || detail.group_info.group_name || '未知群组' }}</div>
                  <div class="entity-id">{{ detail.group_info.chat_id }}</div>
                </div>
              </div>
            </el-descriptions-item>

            <el-descriptions-item v-if="detail.user_info" label="发布者">
              <div class="entity-info">
                <el-avatar v-if="detail.user_info.avatar_url" :src="detail.user_info.avatar_url" :size="32" />
                <el-avatar v-else :size="32">{{ (detail.user_info.nickname || detail.user_info.username || 'U')[0] }}</el-avatar>
                <div class="entity-details">
                  <div class="entity-name">{{ detail.user_info.nickname || detail.user_info.username || '未知用户' }}</div>
                  <div class="entity-id">{{ detail.user_info.user_id }}</div>
                </div>
              </div>
            </el-descriptions-item>

            <el-descriptions-item v-if="detail.source_text" label="聊天原文">
              <div class="source-text" v-html="highlightContent(detail.source_text, detail.content)"></div>
            </el-descriptions-item>

            <el-descriptions-item v-if="detail.source_timestamp" label="发布时间">
              {{ formatDateTime(detail.source_timestamp) }}
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <!-- 用户简介来源 -->
        <div v-else-if="detail.source_type === 'user_desc' && detail.user_info" class="source-content">
          <el-descriptions :column="1" border>
            <el-descriptions-item label="用户">
              <div class="entity-info">
                <el-avatar v-if="detail.user_info.avatar_url" :src="detail.user_info.avatar_url" :size="32" />
                <el-avatar v-else :size="32">{{ (detail.user_info.nickname || detail.user_info.username || 'U')[0] }}</el-avatar>
                <div class="entity-details">
                  <div class="entity-name">{{ detail.user_info.nickname || detail.user_info.username || '未知用户' }}</div>
                  <div class="entity-id">{{ detail.user_info.user_id }}</div>
                </div>
              </div>
            </el-descriptions-item>

            <el-descriptions-item v-if="detail.source_text" label="个人简介">
              <div class="source-text" v-html="highlightContent(detail.source_text, detail.content)"></div>
            </el-descriptions-item>

            <el-descriptions-item v-if="detail.source_timestamp" label="获取时间">
              {{ formatDateTime(detail.source_timestamp) }}
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <!-- 群组简介来源 -->
        <div v-else-if="detail.source_type === 'group_intro' && detail.group_info" class="source-content">
          <el-descriptions :column="1" border>
            <el-descriptions-item label="群组">
              <div class="entity-info">
                <el-avatar v-if="detail.group_info.avatar_url" :src="detail.group_info.avatar_url" :size="32" />
                <el-avatar v-else :size="32">{{ (detail.group_info.group_name || 'G')[0] }}</el-avatar>
                <div class="entity-details">
                  <div class="entity-name">{{ detail.group_info.group_title || detail.group_info.group_name || '未知群组' }}</div>
                  <div class="entity-id">{{ detail.group_info.chat_id }}</div>
                </div>
              </div>
            </el-descriptions-item>

            <el-descriptions-item v-if="detail.source_text" label="群组简介">
              <div class="source-text" v-html="highlightContent(detail.source_text, detail.content)"></div>
            </el-descriptions-item>

            <el-descriptions-item v-if="detail.source_timestamp" label="获取时间">
              {{ formatDateTime(detail.source_timestamp) }}
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <!-- 其他来源类型 -->
        <div v-else class="source-content">
          <el-descriptions :column="1" border>
            <el-descriptions-item v-if="detail.user_info" label="用户">
              {{ detail.user_info.nickname || detail.user_info.username || detail.user_info.user_id }}
            </el-descriptions-item>

            <el-descriptions-item v-if="detail.group_info" label="群组">
              {{ detail.group_info.group_name || detail.group_info.group_title || detail.group_info.chat_id }}
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </div>

      <!-- 额外信息 -->
      <div v-if="detail.extra_info && Object.keys(detail.extra_info).length > 0" class="section">
        <h4>额外信息</h4>

        <el-descriptions :column="1" border>
          <!-- URL 类型的额外信息 -->
          <template v-if="detail.content_type === 'url'">
            <el-descriptions-item v-if="detail.extra_info.normalized_url" label="标准化URL">
              {{ detail.extra_info.normalized_url }}
            </el-descriptions-item>

            <el-descriptions-item v-if="detail.extra_info.website?.domain" label="域名">
              {{ detail.extra_info.website.domain }}
            </el-descriptions-item>

            <el-descriptions-item v-if="detail.extra_info.website?.title" label="网站标题">
              {{ detail.extra_info.website.title }}
            </el-descriptions-item>

            <el-descriptions-item v-if="detail.extra_info.website?.status_code" label="HTTP状态">
              <el-tag :type="detail.extra_info.website.status_code === 200 ? 'success' : 'warning'" size="small">
                {{ detail.extra_info.website.status_code }}
              </el-tag>
            </el-descriptions-item>

            <el-descriptions-item v-if="detail.extra_info.website?.is_short_url !== undefined" label="短链接">
              <el-tag :type="detail.extra_info.website.is_short_url ? 'warning' : 'info'" size="small">
                {{ detail.extra_info.website.is_short_url ? '是' : '否' }}
              </el-tag>
            </el-descriptions-item>

            <el-descriptions-item v-if="detail.extra_info.website?.final_url && detail.extra_info.website.final_url !== detail.extra_info.website.original_url" label="重定向URL">
              {{ detail.extra_info.website.final_url }}
            </el-descriptions-item>

            <el-descriptions-item v-if="detail.extra_info.website?.ip_address" label="IP地址">
              {{ detail.extra_info.website.ip_address }}
            </el-descriptions-item>

            <el-descriptions-item v-if="detail.extra_info.website?.ip_location" label="IP位置">
              {{ formatIpLocation(detail.extra_info.website.ip_location) }}
            </el-descriptions-item>

            <el-descriptions-item v-if="detail.extra_info.phishing?.is_phishing !== undefined" label="钓鱼检测">
              <el-tag :type="detail.extra_info.phishing.is_phishing ? 'danger' : 'success'" size="small">
                {{ detail.extra_info.phishing.is_phishing ? '疑似钓鱼' : '正常' }}
              </el-tag>
            </el-descriptions-item>
          </template>

          <!-- t.me 链接的额外信息 -->
          <template v-else-if="detail.content_type === 't_me_invite' || detail.content_type === 't_me_channel_msg'">
            <el-descriptions-item v-if="detail.extra_info.name" label="名称">
              {{ detail.extra_info.name }}
            </el-descriptions-item>

            <el-descriptions-item v-if="detail.extra_info.username" label="用户名/订阅数">
              {{ detail.extra_info.username }}
            </el-descriptions-item>

            <el-descriptions-item v-if="detail.extra_info.type" label="类型">
              <el-tag size="small">{{ detail.extra_info.type === 'channel' ? '频道' : detail.extra_info.type === 'group' ? '群组' : '用户' }}</el-tag>
            </el-descriptions-item>

            <el-descriptions-item v-if="detail.extra_info.members" label="成员数">
              <el-tag type="primary" size="small">{{ detail.extra_info.members.toLocaleString() }}</el-tag>
            </el-descriptions-item>

            <el-descriptions-item v-if="detail.extra_info.desc" label="描述">
              {{ detail.extra_info.desc }}
            </el-descriptions-item>

            <el-descriptions-item v-if="detail.extra_info.avatar" label="头像">
              <el-image :src="detail.extra_info.avatar" style="width: 50px; height: 50px; border-radius: 4px;" fit="cover" />
            </el-descriptions-item>
          </template>

          <!-- Telegram 账户的额外信息 -->
          <template v-else-if="detail.content_type === 'telegram_account'">
            <el-descriptions-item v-if="detail.extra_info.account_type" label="账户类型">
              <el-tag size="small">{{ detail.extra_info.account_type }}</el-tag>
            </el-descriptions-item>
          </template>

          <!-- Telegraph 的额外信息 -->
          <template v-else-if="detail.content_type === 'telegraph'">
            <el-descriptions-item v-if="detail.extra_info.content?.title" label="文章标题">
              {{ detail.extra_info.content.title }}
            </el-descriptions-item>

            <el-descriptions-item v-if="detail.extra_info.content?.url" label="页面URL">
              <el-link :href="detail.extra_info.content.url" target="_blank" type="primary">
                {{ detail.extra_info.content.url }}
              </el-link>
            </el-descriptions-item>

            <el-descriptions-item v-if="detail.extra_info.content?.images && detail.extra_info.content.images.length > 0" label="图片">
              <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                <el-image
                  v-for="(img, idx) in detail.extra_info.content.images.slice(0, 3)"
                  :key="idx"
                  :src="`https://telegra.ph${img}`"
                  style="width: 60px; height: 60px; border-radius: 4px;"
                  fit="cover"
                  :preview-src-list="detail.extra_info.content.images.map((i: string) => `https://telegra.ph${i}`)"
                />
              </div>
            </el-descriptions-item>

            <el-descriptions-item v-if="detail.extra_info.content?.content" label="文章内容">
              <div class="telegraph-content">
                {{ detail.extra_info.content.content.substring(0, 200) }}{{ detail.extra_info.content.content.length > 200 ? '...' : '' }}
              </div>
            </el-descriptions-item>
          </template>
        </el-descriptions>
      </div>

      <!-- 商家名称 -->
      <div class="section">
        <h4>商家名称</h4>

        <div class="merchant-section">
          <div v-if="!editingMerchant" class="merchant-display">
            <span v-if="detail.merchant_name" class="merchant-value">{{ detail.merchant_name }}</span>
            <el-text v-else type="info">未设置商家名称</el-text>
            <el-button type="primary" link size="small" @click="startEditMerchant">
              {{ detail.merchant_name ? '修改' : '设置' }}
            </el-button>
          </div>
          <div v-else class="merchant-edit">
            <el-input
              v-model="merchantNameInput"
              placeholder="请输入商家名称"
              maxlength="255"
              show-word-limit
              clearable
            />
            <div class="merchant-actions">
              <el-button size="small" @click="cancelEditMerchant">取消</el-button>
              <el-button type="primary" size="small" @click="saveMerchantName">保存</el-button>
            </div>
          </div>
        </div>
      </div>

      <!-- 标签管理 -->
      <div class="section">
        <h4>标签</h4>

        <div class="tags-section">
          <div v-if="detail.tag_ids && detail.tag_ids.length > 0" class="current-tags">
            <el-tag
              v-for="tagId in detail.tag_ids"
              :key="tagId"
              closable
              @close="handleDeleteTag(tagId)"
            >
              标签{{ tagId }}
            </el-tag>
          </div>
          <div v-else class="empty-tags">
            <el-text type="info">暂无标签</el-text>
          </div>

          <div class="add-tags">
            <el-button type="primary" size="small" @click="showAddTagDialog = true">
              添加标签
            </el-button>
          </div>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="action-buttons">
        <el-button type="danger" @click="handleDeleteRecord">删除记录</el-button>
        <el-button @click="adTrackingStore.closeDetailDrawer()">关闭</el-button>
      </div>
    </div>

    <!-- 添加标签对话框 -->
    <el-dialog v-model="showAddTagDialog" title="添加标签" width="400px">
      <el-form>
        <el-form-item label="选择标签">
          <el-select v-model="selectedTagIds" multiple placeholder="请选择" style="width: 100%">
            <el-option
              v-for="tag in availableTags"
              :key="tag.id"
              :label="tag.name"
              :value="tag.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddTagDialog = false">取消</el-button>
        <el-button type="primary" @click="handleAddTags">确定</el-button>
      </template>
    </el-dialog>
  </el-drawer>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAdTrackingStore } from '@/store/modules/adTracking'
import { tagsApi, type Tag } from '@/api/tags'
import type { IpLocation } from '@/types/adTracking'
import dayjs from 'dayjs'

const adTrackingStore = useAdTrackingStore()

const detail = computed(() => adTrackingStore.currentDetail)

const showAddTagDialog = ref(false)
const selectedTagIds = ref<number[]>([])
const availableTags = ref<Tag[]>([])

// 商家名称编辑
const editingMerchant = ref(false)
const merchantNameInput = ref('')

// 标签映射
const contentTypeLabels: Record<string, string> = {
  url: 'URL',
  telegram_account: '@账户',
  t_me_invite: 't.me邀请',
  t_me_channel_msg: 't.me频道',
  t_me_private_invite: 't.me私聊',
  telegraph: 'Telegraph'
}

const sourceTypeLabels: Record<string, string> = {
  chat: '聊天消息',
  user_desc: '用户简介',
  username: '用户名',
  nickname: '昵称',
  group_intro: '群组简介'
}

function getContentTypeLabel(type: string): string {
  return contentTypeLabels[type] || type
}

function getContentTypeTagType(type: string): string {
  const typeMap: Record<string, string> = {
    url: '',
    telegram_account: 'success',
    t_me_invite: 'warning',
    t_me_channel_msg: 'info',
    t_me_private_invite: 'danger',
    telegraph: 'primary'
  }
  return typeMap[type] || ''
}

function getSourceTypeLabel(type: string): string {
  return sourceTypeLabels[type] || type
}

function formatDateTime(dateStr: string): string {
  if (!dateStr) return '-'
  return dayjs(dateStr).format('YYYY-MM-DD HH:mm:ss')
}

function formatIpLocation(location: IpLocation): string {
  if (!location) return '-'
  const parts = []
  if (location.country) parts.push(location.country)
  if (location.region) parts.push(location.region)
  if (location.city) parts.push(location.city)
  return parts.join(' / ') || '-'
}

function highlightContent(text: string, keyword: string): string {
  if (!text || !keyword) return text || ''

  // 转义HTML特殊字符
  const escapeHtml = (str: string) => {
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;')
  }

  const escapedText = escapeHtml(text)
  const escapedKeyword = escapeHtml(keyword)

  // 转义正则表达式特殊字符
  const escapeRegex = (str: string) => {
    return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  }

  const regex = new RegExp(`(${escapeRegex(escapedKeyword)})`, 'gi')
  return escapedText.replace(regex, '<span class="highlight">$1</span>')
}

async function copyContent(content: string) {
  try {
    await navigator.clipboard.writeText(content)
    ElMessage.success('已复制到剪贴板')
  } catch {
    ElMessage.error('复制失败')
  }
}

// 商家名称编辑功能
function startEditMerchant() {
  if (!detail.value) return
  merchantNameInput.value = detail.value.merchant_name || ''
  editingMerchant.value = true
}

function cancelEditMerchant() {
  editingMerchant.value = false
  merchantNameInput.value = ''
}

async function saveMerchantName() {
  if (!detail.value) return

  const success = await adTrackingStore.updateMerchantName(detail.value.id, merchantNameInput.value.trim())

  if (success) {
    editingMerchant.value = false
    ElMessage.success('商家名称已更新')
  }
}

async function handleDeleteTag(tagId: number) {
  if (!detail.value) return

  try {
    await ElMessageBox.confirm('确定要删除这个标签吗？', '删除确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await adTrackingStore.deleteTag(detail.value.id, tagId)
  } catch {
    // 用户取消
  }
}

async function handleDeleteRecord() {
  if (!detail.value) return

  try {
    await ElMessageBox.confirm(
      '确定要删除这条广告追踪记录吗？此操作不可恢复。',
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await adTrackingStore.deleteTracking(detail.value.id)
  } catch {
    // 用户取消
  }
}

async function fetchTags() {
  try {
    const response = await tagsApi.getList()
    if (response.err_code === 0) {
      availableTags.value = response.payload.data
    }
  } catch (error) {
    console.error('获取标签列表失败:', error)
  }
}

async function handleAddTags() {
  if (!detail.value || selectedTagIds.value.length === 0) {
    ElMessage.warning('请选择至少一个标签')
    return
  }

  const success = await adTrackingStore.addTags(detail.value.id, selectedTagIds.value)

  if (success) {
    showAddTagDialog.value = false
    selectedTagIds.value = []
  }
}

watch(showAddTagDialog, (val) => {
  if (val) {
    fetchTags()
  }
})
</script>

<style scoped lang="scss">
.detail-content {
  padding: 20px;
  padding-bottom: 20px;

  // 使用与 UserDetailDrawer 相同的卡片样式
  .section {
    background: #fff;
    padding: 16px;
    border-radius: 6px;
    border: 1px solid #f0f0f0;
    margin-bottom: 20px;

    h4 {
      margin: 0 0 12px 0;
      font-size: 14px;
      font-weight: 600;
      color: #333;
      border-bottom: 1px solid #f0f0f0;
      padding-bottom: 8px;
    }
  }

  .content-display {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;

    .el-text {
      flex: 1;
      word-break: break-all;
    }
  }

  .tags-section {
    .current-tags {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 16px;
    }

    .empty-tags {
      margin-bottom: 16px;
    }

    .add-tags {
      display: flex;
      justify-content: flex-start;
    }
  }

  .merchant-section {
    .merchant-display {
      display: flex;
      align-items: center;
      gap: 12px;

      .merchant-value {
        flex: 1;
        font-weight: 500;
      }
    }

    .merchant-edit {
      .merchant-actions {
        display: flex;
        justify-content: flex-end;
        gap: 8px;
        margin-top: 12px;
      }
    }
  }

  .action-buttons {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
    padding-top: 20px;
    border-top: 1px solid #ebeef5;
  }

  .source-content {
    .entity-info {
      display: flex;
      align-items: center;
      gap: 12px;

      .entity-details {
        flex: 1;

        .entity-name {
          font-weight: 500;
          font-size: 14px;
          color: #303133;
          margin-bottom: 2px;
        }

        .entity-id {
          font-size: 12px;
          color: #909399;
        }
      }
    }

    .source-text {
      line-height: 1.6;
      white-space: pre-wrap;
      word-break: break-word;

      :deep(.highlight) {
        background-color: #ffeb3b;
        padding: 2px 4px;
        border-radius: 2px;
        font-weight: 500;
      }
    }
  }

  .telegraph-content {
    max-height: 150px;
    overflow-y: auto;
    line-height: 1.6;
    color: #606266;
    background: #f5f7fa;
    padding: 8px 12px;
    border-radius: 4px;
    font-size: 13px;
  }
}
</style>
