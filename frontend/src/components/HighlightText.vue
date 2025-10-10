<template>
  <span v-html="highlightedText"></span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  text: string
  keywords: string | string[]
  highlightClass?: string
}

const props = withDefaults(defineProps<Props>(), {
  highlightClass: 'keyword-highlight'
})

const highlightedText = computed(() => {
  if (!props.text) return ''

  const keywordArray = Array.isArray(props.keywords)
    ? props.keywords
    : [props.keywords]

  if (keywordArray.length === 0) return escapeHtml(props.text)

  // 过滤空关键词
  const validKeywords = keywordArray.filter(k => k && k.trim())
  if (validKeywords.length === 0) return escapeHtml(props.text)

  // 转义关键词中的正则特殊字符
  const escapedKeywords = validKeywords.map(keyword =>
    keyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  )

  // 创建正则表达式，全局不区分大小写匹配
  const regex = new RegExp(`(${escapedKeywords.join('|')})`, 'gi')

  // 先转义HTML，然后高亮关键词
  const escapedText = escapeHtml(props.text)

  return escapedText.replace(regex, (match) => {
    return `<span class="${props.highlightClass}">${match}</span>`
  })
})

// HTML转义函数
function escapeHtml(text: string): string {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}
</script>

<style scoped>
:deep(.keyword-highlight) {
  background-color: #FFF3CD;
  color: #856404;
  font-weight: bold;
  padding: 2px 4px;
  border-radius: 2px;
}
</style>
