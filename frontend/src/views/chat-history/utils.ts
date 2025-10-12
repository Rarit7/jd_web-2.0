/**
 * ChatHistory页面工具函数
 * 这些函数不涉及响应式状态，可以安全地独立使用
 */

import type { ChatMessage } from '@/api/chat-history'
import { formatUTCToLocal } from '@/utils/date'

export interface DocumentInfo {
  path: string
  ext: string
  mime_type: string
  is_sticker?: boolean
  sticker_type?: string
  display_text?: string
  display_icon?: string
  filename_origin?: string
  file_size?: number
  video_thumb_path?: string
}

/**
 * 构建头像URL
 */
export const buildAvatarUrl = (avatarPath: string): string => {
  if (!avatarPath) return ''

  // 如果已经是完整URL，直接返回
  if (avatarPath.startsWith('http://') || avatarPath.startsWith('https://')) {
    return avatarPath
  }

  // 如果是相对路径，构建完整路径
  if (avatarPath.startsWith('images/')) {
    return `/static/${avatarPath}`
  }

  // 否则假设是文件名，添加avatar目录前缀
  return `/static/images/avatar/${avatarPath}`
}

/**
 * 构建图片URL
 */
export const buildImageUrl = (imagePath: string): string => {
  if (!imagePath) return ''

  // 如果已经是完整URL，直接返回
  if (imagePath.startsWith('http://') || imagePath.startsWith('https://')) {
    return imagePath
  }

  // 如果是相对路径，构建完整路径
  if (imagePath.startsWith('images/') || imagePath.startsWith('document/')) {
    return `/static/${imagePath}`
  }

  // 如果是视频缩略图路径，添加document前缀
  if (imagePath.startsWith('thumbs/')) {
    return `/static/document/${imagePath}`
  }

  // 如果只是文件名，添加images目录前缀
  return `/static/images/${imagePath}`
}

/**
 * 检查消息是否有文本内容
 */
export const hasTextContent = (msg: ChatMessage): boolean => {
  return !!msg.message && msg.message.trim() !== ''
}

/**
 * 判断文档是否为图片文件
 */
export const isImageFile = (doc: DocumentInfo): boolean => {
  if (!doc) return false

  const imageMimeTypes = [
    'image/jpeg',
    'image/jpg',
    'image/png',
    'image/gif',
    'image/webp',
    'image/bmp',
    'image/svg+xml'
  ]

  return imageMimeTypes.includes(doc.mime_type)
}

/**
 * 获取文件类型显示文本
 */
export const getFileType = (doc: DocumentInfo): string => {
  if (doc.is_sticker) {
    return 'sticker'
  }

  // 从mime_type提取主类型
  if (doc.mime_type) {
    const mainType = doc.mime_type.split('/')[0]

    // 特殊处理
    if (doc.mime_type.includes('pdf')) return 'pdf'
    if (doc.mime_type.includes('zip') || doc.mime_type.includes('rar') || doc.mime_type.includes('7z')) return 'archive'
    if (doc.mime_type.includes('word') || doc.mime_type.includes('document')) return 'document'
    if (doc.mime_type.includes('sheet') || doc.mime_type.includes('excel')) return 'spreadsheet'
    if (doc.mime_type.includes('presentation') || doc.mime_type.includes('powerpoint')) return 'presentation'

    // 按主类型返回
    switch (mainType) {
      case 'video': return 'video'
      case 'audio': return 'audio'
      case 'image': return 'image'
      case 'text': return 'text'
      case 'application': return doc.ext || 'file'
      default: return 'file'
    }
  }

  // 如果没有mime_type，尝试从扩展名判断
  if (doc.ext) {
    return doc.ext
  }

  return 'file'
}

/**
 * 格式化文件大小
 */
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

/**
 * 从遗留数据结构中获取图片文档（photo_paths和document_paths）
 */
export const getImageDocumentsFromLegacy = (msg: ChatMessage): DocumentInfo[] => {
  const images: DocumentInfo[] = []

  // 处理photo_paths（通常是图片）
  if (msg.photo_paths && msg.photo_paths.length > 0) {
    images.push(...msg.photo_paths.map(path => ({
      path,
      ext: 'jpg',
      mime_type: 'image/jpeg'
    })))
  }

  return images
}

/**
 * 从documents数组中获取图片文档
 */
export const getImageDocuments = (msg: ChatMessage): DocumentInfo[] => {
  if (!msg.documents || msg.documents.length === 0) return []
  return msg.documents.filter(isImageFile)
}

/**
 * 从遗留数据结构中获取非图片文档
 */
export const getNonImageDocumentsFromLegacy = (msg: ChatMessage): DocumentInfo[] => {
  const files: DocumentInfo[] = []

  // 处理document_paths（可能是各种文件）
  if (msg.document_paths && msg.document_paths.length > 0) {
    files.push(...msg.document_paths.map(path => ({
      path,
      ext: path.split('.').pop() || 'file',
      mime_type: 'application/octet-stream'
    })))
  }

  return files
}

/**
 * 从documents数组中获取非图片文档
 */
export const getNonImageDocuments = (msg: ChatMessage): DocumentInfo[] => {
  if (!msg.documents || msg.documents.length === 0) return []
  return msg.documents.filter(doc => !isImageFile(doc))
}

/**
 * 检查消息是否有图片内容
 */
export const hasImageContent = (msg: ChatMessage): boolean => {
  return getImageDocumentsFromLegacy(msg).length > 0 || getImageDocuments(msg).length > 0
}

/**
 * 检查消息是否有文件内容
 */
export const hasFileContent = (msg: ChatMessage): boolean => {
  return getNonImageDocumentsFromLegacy(msg).length > 0 || getNonImageDocuments(msg).length > 0
}

/**
 * 判断消息的主要类型
 */
export const determineMainMessageType = (msg: ChatMessage): 'text' | 'image' | 'file' | 'mixed' => {
  const hasText = hasTextContent(msg)
  const hasImages = hasImageContent(msg)
  const hasFiles = hasFileContent(msg)

  // 同时有文本和媒体内容
  if ((hasText && hasImages) || (hasText && hasFiles) || (hasImages && hasFiles)) {
    return 'mixed'
  }

  if (hasImages) return 'image'
  if (hasFiles) return 'file'
  return 'text'
}

/**
 * 从文件路径数组中获取文件名
 */
export const getFileName = (documentPaths: string[]): string => {
  if (!documentPaths || documentPaths.length === 0) return ''
  const path = documentPaths[0]
  return path.split('/').pop() || path
}

/**
 * 字符串哈希函数，用于生成头像颜色
 */
export const stringHashCode = (str: string): number => {
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i)
    hash = ((hash << 5) - hash) + char
    hash = hash & hash
  }
  return Math.abs(hash)
}

/**
 * 高亮搜索关键词
 */
export const highlightKeyword = (content: string, keyword: string) => {
  if (!keyword || !content) return content

  const regex = new RegExp(`(${keyword})`, 'gi')
  return content.replace(regex, '<mark class="highlight">$1</mark>')
}

/**
 * 格式化搜索时间显示
 */
export const formatSearchTime = (timeString: string): string => {
  if (!timeString) return ''

  // 使用统一的UTC+8时间格式化函数，但只显示到分钟
  const formatted = formatUTCToLocal(timeString)
  // 截取前16位：YYYY/MM/DD HH:mm
  return formatted.substring(0, 16)
}
