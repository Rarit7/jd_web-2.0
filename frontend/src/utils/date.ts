/**
 * Date utility functions with UTC+8 timezone support
 */

/**
 * Convert any date to UTC+8 timezone display
 * @param date Date string, Date object, or timestamp
 * @returns Date object for UTC+8 timezone display
 */
export const toUTC8 = (date: string | Date | number): Date => {
  return new Date(date)
}

/**
 * Format time for display with UTC+8 timezone
 * @param timeString Date string or Date object
 * @returns Formatted time string
 */
export const formatTime = (timeString: string | Date): string => {
  if (!timeString) return ''
  
  const time = new Date(timeString)
  const now = new Date()
  
  // 转换为UTC+8时区进行比较
  const timeUTC8 = new Date(time.toLocaleString('en-US', { timeZone: 'Asia/Shanghai' }))
  const nowUTC8 = new Date(now.toLocaleString('en-US', { timeZone: 'Asia/Shanghai' }))
  
  const diffMs = nowUTC8.getTime() - timeUTC8.getTime()
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))
  
  if (diffDays === 0) {
    return time.toLocaleTimeString('zh-CN', { 
      hour: '2-digit', 
      minute: '2-digit',
      hour12: false,
      timeZone: 'Asia/Shanghai'
    })
  } else if (diffDays === 1) {
    return '昨天'
  } else if (diffDays < 7) {
    return `${diffDays}天前`
  } else {
    return time.toLocaleDateString('zh-CN', { 
      month: 'short', 
      day: 'numeric',
      timeZone: 'Asia/Shanghai'
    })
  }
}

/**
 * Format date and time for display with UTC+8 timezone
 * @param dateTime Date string or Date object
 * @returns Formatted date time string
 */
export const formatDateTime = (dateTime: string | Date): string => {
  if (!dateTime) return ''
  
  const date = new Date(dateTime)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    timeZone: 'Asia/Shanghai',
    hour12: false
  })
}

/**
 * Format datetime from database to local display
 * 注意：数据库中存储的时间已经是北京时间（UTC+8），不需要时区转换
 * @param dateTime DateTime string from database (already in Beijing time)
 * @returns Formatted date time string
 */
export const formatUTCToLocal = (dateTime: string | Date): string => {
  if (!dateTime) return ''

  let date: Date
  if (typeof dateTime === 'string') {
    // 后端返回的是ISO格式的时间字符串，但这个时间已经是北京时间
    // 不添加Z后缀，让JavaScript按本地时间解析
    date = new Date(dateTime)
  } else {
    date = dateTime
  }

  // 验证日期是否有效
  if (isNaN(date.getTime())) {
    console.warn('Invalid date:', dateTime)
    return String(dateTime)
  }

  // 直接格式化，不进行时区转换（因为时间已经是北京时间）
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  })
}

/**
 * Format date for display with UTC+8 timezone
 * @param date Date string or Date object
 * @returns Formatted date string
 */
export const formatDate = (date: string | Date): string => {
  if (!date) return ''
  
  const dateObj = new Date(date)
  return dateObj.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    timeZone: 'Asia/Shanghai'
  })
}

/**
 * Format date for API requests (YYYY-MM-DD format in UTC+8)
 * @param date Date object
 * @returns Formatted date string for API
 */
export const formatDateForApi = (date: Date): string => {
  // 使用Asia/Shanghai时区格式化日期
  const utc8String = date.toLocaleDateString('sv-SE', { timeZone: 'Asia/Shanghai' })
  return utc8String
}

/**
 * Get relative time description in Chinese
 * @param dateTime Date string or Date object
 * @returns Relative time string
 */
export const getRelativeTime = (dateTime: string | Date): string => {
  if (!dateTime) return ''
  
  const date = new Date(dateTime)
  const now = new Date()
  
  // 转换为UTC+8时区进行比较
  const dateUTC8 = new Date(date.toLocaleString('en-US', { timeZone: 'Asia/Shanghai' }))
  const nowUTC8 = new Date(now.toLocaleString('en-US', { timeZone: 'Asia/Shanghai' }))
  
  const diffMs = nowUTC8.getTime() - dateUTC8.getTime()
  
  const diffMinutes = Math.floor(diffMs / (1000 * 60))
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))
  
  if (diffMinutes < 1) {
    return '刚刚'
  } else if (diffMinutes < 60) {
    return `${diffMinutes}分钟前`
  } else if (diffHours < 24) {
    return `${diffHours}小时前`
  } else if (diffDays < 30) {
    return `${diffDays}天前`
  } else {
    return formatDate(date)
  }
}

/**
 * Check if date is today in UTC+8 timezone
 * @param date Date string or Date object
 * @returns Boolean indicating if date is today
 */
export const isToday = (date: string | Date): boolean => {
  const targetDate = new Date(date)
  const today = new Date()
  
  // 转换为UTC+8时区进行比较
  const targetUTC8 = new Date(targetDate.toLocaleString('en-US', { timeZone: 'Asia/Shanghai' }))
  const todayUTC8 = new Date(today.toLocaleString('en-US', { timeZone: 'Asia/Shanghai' }))
  
  return targetUTC8.getFullYear() === todayUTC8.getFullYear() &&
         targetUTC8.getMonth() === todayUTC8.getMonth() &&
         targetUTC8.getDate() === todayUTC8.getDate()
}