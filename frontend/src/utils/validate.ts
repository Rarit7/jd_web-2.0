/**
 * 验证工具函数
 */

/**
 * 判断是否是外链
 * @param path 
 * @returns 
 */
export function isExternal(path: string): boolean {
  return /^(https?:|mailto:|tel:)/.test(path)
}

/**
 * 判断是否是有效的URL
 * @param url 
 * @returns 
 */
export function isValidURL(url: string): boolean {
  const reg = /^(https?|ftp):\/\/([a-zA-Z0-9.-]+(:[a-zA-Z0-9.&%$-]+)*@)*((25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9][0-9]?)(\.(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])){3}|([a-zA-Z0-9-]+\.)*[a-zA-Z0-9-]+\.(com|edu|gov|int|mil|net|org|biz|arpa|info|name|pro|aero|coop|museum|[a-zA-Z]{2}))(:[0-9]+)*(\/($|[a-zA-Z0-9.,?'\\+&%$#=~_-]+))*$/
  return reg.test(url)
}

/**
 * 判断是否是小写字母
 * @param str 
 * @returns 
 */
export function isLowerCase(str: string): boolean {
  const reg = /^[a-z]+$/
  return reg.test(str)
}

/**
 * 判断是否是大写字母
 * @param str 
 * @returns 
 */
export function isUpperCase(str: string): boolean {
  const reg = /^[A-Z]+$/
  return reg.test(str)
}

/**
 * 判断是否是字母
 * @param str 
 * @returns 
 */
export function isAlphabets(str: string): boolean {
  const reg = /^[A-Za-z]+$/
  return reg.test(str)
}

/**
 * 判断是否是邮箱
 * @param email 
 * @returns 
 */
export function isEmail(email: string): boolean {
  const reg = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/
  return reg.test(email)
}

/**
 * 判断是否是数字字符串
 * @param str 
 * @returns 
 */
export function isNumeric(str: string): boolean {
  const reg = /^[0-9]+$/
  return reg.test(str)
}

/**
 * 判断是否是手机号
 * @param phone 
 * @returns 
 */
export function isMobile(phone: string): boolean {
  const reg = /^1[3-9]\d{9}$/
  return reg.test(phone)
}

/**
 * 判断是否是中文
 * @param str 
 * @returns 
 */
export function isChinese(str: string): boolean {
  const reg = /^[\u4e00-\u9fa5]+$/
  return reg.test(str)
}

/**
 * 判断是否是身份证号
 * @param idCard 
 * @returns 
 */
export function isIdCard(idCard: string): boolean {
  const reg = /(^\d{15}$)|(^\d{18}$)|(^\d{17}(\d|X|x)$)/
  return reg.test(idCard)
}

/**
 * 判断是否是JSON字符串
 * @param str 
 * @returns 
 */
export function isJSON(str: string): boolean {
  if (typeof str === 'string') {
    try {
      const obj = JSON.parse(str)
      if (typeof obj === 'object' && obj) {
        return true
      } else {
        return false
      }
    } catch (e) {
      return false
    }
  }
  return false
}