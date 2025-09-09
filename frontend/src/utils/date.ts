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
 * Format UTC datetime from database to UTC+8 display
 * @param utcDateTime UTC datetime string from database
 * @returns Formatted date time string in UTC+8
 */
export const formatUTCToLocal = (utcDateTime: string | Date): string => {
  if (!utcDateTime) return ''
  
  // 创建Date对象时，如果字符串不带时区信息，JavaScript会假设它是本地时间
  // 但数据库存储的是UTC时间，所以需要明确指定为UTC
  let date: Date
  if (typeof utcDateTime === 'string') {
    // 如果字符串不以Z结尾，添加Z来明确表示这是UTC时间
    const utcString = utcDateTime.endsWith('Z') ? utcDateTime : utcDateTime + 'Z'
    date = new Date(utcString)
  } else {
    date = utcDateTime
  }
  
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