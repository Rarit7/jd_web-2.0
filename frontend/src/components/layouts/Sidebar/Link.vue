<template>
  <!-- eslint-disable vue/require-component-is -->
  <component :is="linkProps(to).tag" v-bind="linkProps(to).props">
    <slot />
  </component>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { isExternal } from '@/utils/validate'

interface Props {
  to: string
}

const props = defineProps<Props>()

const linkProps = (url: string) => {
  if (isExternal(url)) {
    return {
      tag: 'a',
      props: {
        href: url,
        target: '_blank',
        rel: 'noopener'
      }
    }
  }
  
  return {
    tag: 'router-link',
    props: {
      to: url
    }
  }
}
</script>

<style scoped>
a, :deep(a) {
  text-decoration: none !important;
}

:deep(.router-link-active),
:deep(.router-link-exact-active) {
  text-decoration: none !important;
}
</style>