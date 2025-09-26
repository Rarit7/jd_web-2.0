/**
 * 中文简繁转换工具
 * 用于实现群组搜索的简繁体互搜功能
 */
import { s2t, t2s } from 'chinese-s2t'

/**
 * 获取搜索关键词的所有变体（简体、繁体）
 * @param {string} keyword - 原始搜索关键词
 * @returns {Array} 包含所有变体的数组，去重后返回
 */
export function getSearchVariants(keyword) {
  if (!keyword || typeof keyword !== 'string') {
    return []
  }

  const trimmedKeyword = keyword.trim()
  if (!trimmedKeyword) {
    return []
  }

  const variants = [trimmedKeyword]

  try {
    // 简体转繁体
    const traditional = s2t(trimmedKeyword)
    if (traditional && traditional !== trimmedKeyword) {
      variants.push(traditional)
    }

    // 繁体转简体（防止用户输入繁体）
    const simplified = t2s(trimmedKeyword)
    if (simplified && simplified !== trimmedKeyword && !variants.includes(simplified)) {
      variants.push(simplified)
    }
  } catch (error) {
    console.warn('简繁转换失败:', error)
    // 转换失败时返回原关键词
    return [trimmedKeyword]
  }

  return variants
}

/**
 * 检查文本是否包含中文字符
 * @param {string} text - 要检查的文本
 * @returns {boolean} 是否包含中文
 */
export function containsChinese(text) {
  if (!text || typeof text !== 'string') {
    return false
  }
  return /[\u4e00-\u9fff]/.test(text)
}

/**
 * 获取搜索建议（包含简繁变体）
 * @param {string} queryString - 查询字符串
 * @returns {Array} 建议列表
 */
export function getSearchSuggestions(queryString) {
  if (!queryString) {
    return []
  }

  const suggestions = [{ value: queryString, type: 'original' }]

  // 如果包含中文，添加转换建议
  if (containsChinese(queryString)) {
    try {
      const variants = getSearchVariants(queryString)
      variants.forEach(variant => {
        if (variant !== queryString) {
          const traditional = s2t(queryString)
          const isTraditional = variant === traditional

          suggestions.push({
            value: variant,
            type: 'variant',
            originalType: isTraditional ? '繁体' : '简体',
            isVariant: true
          })
        }
      })
    } catch (error) {
      console.warn('获取搜索建议失败:', error)
    }
  }

  return suggestions
}

/**
 * 测试转换功能（开发调试用）
 */
export function testConversion() {
  const testCases = [
    '台湾',
    '網絡',
    'bitcoin',
    '中国',
    '資訊',
    'hello world',
    '数据库',
    '資料庫'
  ]

  console.log('=== 简繁转换测试 ===')
  testCases.forEach(text => {
    const variants = getSearchVariants(text)
    console.log(`"${text}" -> [${variants.join(', ')}]`)
  })
}

// 导出默认对象（兼容不同导入方式）
export default {
  getSearchVariants,
  containsChinese,
  getSearchSuggestions,
  testConversion
}