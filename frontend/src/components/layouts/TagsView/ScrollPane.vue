<template>
  <div ref="scrollContainer" class="scroll-container" @wheel.prevent="handleScroll">
    <div ref="scrollWrapper" class="scroll-wrapper">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'

const emit = defineEmits<{
  scroll: [{ e: WheelEvent; data: any }]
}>()

const scrollContainer = ref<HTMLElement>()
const scrollWrapper = ref<HTMLElement>()

const handleScroll = (e: WheelEvent) => {
  const eventDelta = e.deltaY * 40
  if (scrollContainer.value) {
    scrollContainer.value.scrollLeft = scrollContainer.value.scrollLeft + eventDelta / 4
  }
  emit('scroll', { e, data: {} })
}

const moveToTarget = (currentTag: HTMLElement) => {
  if (!scrollContainer.value || !scrollWrapper.value) return
  
  const containerWidth = scrollContainer.value.offsetWidth
  const wrapperWidth = scrollWrapper.value.offsetWidth

  if (wrapperWidth < containerWidth) {
    scrollContainer.value.scrollLeft = 0
    return
  }

  const tagOffsetLeft = currentTag.offsetLeft
  const tagOffsetWidth = currentTag.offsetWidth
  const currentScrollLeft = scrollContainer.value.scrollLeft

  if (tagOffsetLeft < currentScrollLeft) {
    scrollContainer.value.scrollLeft = tagOffsetLeft
  } else if (tagOffsetLeft + tagOffsetWidth > currentScrollLeft + containerWidth) {
    scrollContainer.value.scrollLeft = tagOffsetLeft + tagOffsetWidth - containerWidth
  }
}

defineExpose({
  scrollContainer,
  moveToTarget
})

onMounted(() => {
  scrollContainer.value?.addEventListener('wheel', handleScroll, { passive: false })
})

onBeforeUnmount(() => {
  scrollContainer.value?.removeEventListener('wheel', handleScroll)
})
</script>

<style lang="scss" scoped>
.scroll-container {
  white-space: nowrap;
  position: relative;
  overflow: hidden;
  width: 100%;

  .scroll-wrapper {
    position: absolute;
  }
}
</style>