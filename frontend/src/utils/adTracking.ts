/**
 * Ad Tracking 模块的共享工具函数
 */

/**
 * 格式化日期时间为可读的本地化字符串
 * @param dateString ISO 格式的日期字符串或 null
 * @returns 格式化的日期时间字符串，如 "2024-01-15 14:30"
 */
export const formatDateTime = (dateString: string | null): string => {
  if (!dateString) return '未知时间'

  const date = new Date(dateString)
  if (isNaN(date.getTime())) return '未知时间'

  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
    timeZone: 'Asia/Shanghai'
  })
}

/**
 * 截断文本并添加省略号
 * @param text 原始文本
 * @param maxLength 最大长度（默认 60）
 * @returns 截断后的文本
 */
export const truncateText = (text: string | null, maxLength: number = 60): string => {
  if (!text) return ''
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

/**
 * 格式化相对时间（如"2小时前"）
 * @param dateString ISO 格式的日期字符串或 null
 * @returns 相对时间字符串
 */
export const formatRelativeTime = (dateString: string | null): string => {
  if (!dateString) return '未知'

  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()

  const diffMinutes = Math.floor(diffMs / (1000 * 60))
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  if (diffMinutes < 1) return '刚刚'
  if (diffMinutes < 60) return `${diffMinutes}分钟前`
  if (diffHours < 24) return `${diffHours}小时前`
  if (diffDays < 7) return `${diffDays}天前`

  return formatDateTime(dateString)
}

/**
 * 下载 Blob 为文件
 * @param blob 文件 Blob 对象
 * @param filename 文件名
 */
export const downloadBlob = (blob: Blob, filename: string): void => {
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', filename)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
}

/**
 * 生成导出文件名（带时间戳）
 * @param prefix 文件前缀（默认 'ad_records'）
 * @param extension 文件扩展名（默认 'xlsx'）
 * @returns 完整文件名，如 "ad_records_1705324800000.xlsx"
 */
export const generateExportFilename = (
  prefix: string = 'ad_records',
  extension: string = 'xlsx'
): string => {
  const timestamp = new Date().getTime()
  return `${prefix}_${timestamp}.${extension}`
}

/**
 * 验证图片 URL 是否有效
 * @param url 图片 URL
 * @returns 是否有效
 */
export const isValidImageUrl = (url: string | null): boolean => {
  if (!url) return false
  try {
    new URL(url)
    return /\.(jpg|jpeg|png|gif|webp|svg)$/i.test(url)
  } catch {
    return false
  }
}

/**
 * 获取处理状态对应的颜色
 * @param isProcessed 是否已处理
 * @returns 颜色值，如 "#67C23A" 或 "#F56C6C"
 */
export const getProcessedStatusColor = (isProcessed: boolean): string => {
  return isProcessed ? '#67C23A' : '#F56C6C'
}

/**
 * 获取处理状态对应的文本
 * @param isProcessed 是否已处理
 * @returns 状态文本，如 "已处理" 或 "未处理"
 */
export const getProcessedStatusText = (isProcessed: boolean): string => {
  return isProcessed ? '已处理' : '未处理'
}
