<template>
  <div id="tags-view-container" class="tags-view-container">
    <scroll-pane ref="scrollPaneRef" class="tags-view-wrapper" @scroll="handleScroll">
      <router-link
        v-for="tag in visitedViews"
        :key="tag.path"
        :class="isActive(tag) ? 'active' : ''"
        :to="{ path: tag.path!, query: tag.query }"
        class="tags-view-item"
        @click.middle="!isAffix(tag) ? closeSelectedTag(tag) : ''"
        @contextmenu.prevent="openMenu(tag, $event)"
      >
        {{ tag.title }}
        <el-icon
          v-if="!isAffix(tag)"
          class="el-icon-close"
          @click.prevent.stop="closeSelectedTag(tag)"
        >
          <Close />
        </el-icon>
      </router-link>
    </scroll-pane>
    <ul v-show="visible" :style="{ left: left + 'px', top: top + 'px' }" class="contextmenu">
      <li @click="refreshSelectedTag(selectedTag)">刷新</li>
      <li v-if="!isAffix(selectedTag)" @click="closeSelectedTag(selectedTag)">关闭</li>
      <li @click="closeOthersTags">关闭其他</li>
      <li @click="closeAllTags(selectedTag)">关闭所有</li>
    </ul>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, reactive, watch, nextTick, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Close } from '@element-plus/icons-vue'
import ScrollPane from './ScrollPane.vue'
import { useTagsViewStore, type TagView } from '@/store/modules/tagsView'

const route = useRoute()
const router = useRouter()
const tagsViewStore = useTagsViewStore()

const visible = ref(false)
const top = ref(0)
const left = ref(0)
const selectedTag = ref<TagView>({})
const affixTags = ref<TagView[]>([])
const scrollPaneRef = ref()

const visitedViews = computed(() => tagsViewStore.visitedViews)

const isActive = (tag: TagView) => {
  return tag.path === route.path
}

const isAffix = (tag: TagView) => {
  return tag.meta && tag.meta.affix
}

const filterAffixTags = (routes: TagView[], basePath = '/') => {
  let tags: TagView[] = []
  routes.forEach(route => {
    if (route.meta && route.meta.affix) {
      const tagPath = resolve(basePath, route.path!)
      tags.push({
        fullPath: tagPath,
        path: tagPath,
        name: route.name,
        meta: { ...route.meta }
      })
    }
    if (route.children) {
      const tempTags = filterAffixTags(route.children, route.path)
      if (tempTags.length >= 1) {
        tags = [...tags, ...tempTags]
      }
    }
  })
  return tags
}

const initTags = () => {
  const affixTagsValue = affixTags.value = filterAffixTags([
    {
      path: '/dashboard',
      name: 'Dashboard',
      meta: { title: '首页', affix: true }
    }
  ])
  for (const tag of affixTagsValue) {
    if (tag.name) {
      tagsViewStore.addVisitedView(tag)
    }
  }
}

const addTags = () => {
  const { name } = route
  if (name) {
    tagsViewStore.addView({
      ...route,
      title: route.meta?.title || 'no-name'
    } as TagView)
  }
  return false
}

const moveToCurrentTag = () => {
  const tags = Array.from(document.querySelectorAll('.tags-view-item'))
  nextTick(() => {
    for (const [idx, tag] of tags.entries()) {
      if ((tag as HTMLElement).classList.contains('active')) {
        scrollPaneRef.value.moveToTarget(tag)
        if (idx > 0) {
          const prevTag = tags[idx - 1] as HTMLElement
          if (prevTag.offsetLeft < scrollPaneRef.value.scrollContainer.scrollLeft) {
            scrollPaneRef.value.scrollContainer.scrollLeft = prevTag.offsetLeft
          }
        }
        break
      }
    }
  })
}

const refreshSelectedTag = (view: TagView) => {
  tagsViewStore.delCachedView(view)
  const { fullPath } = view
  nextTick(() => {
    router.replace({
      path: '/redirect' + fullPath
    })
  })
}

const closeSelectedTag = (view: TagView) => {
  tagsViewStore.delView(view)
  if (isActive(view)) {
    toLastView(tagsViewStore.visitedViews, view)
  }
}

const closeOthersTags = () => {
  router.push(selectedTag.value.path!)
  tagsViewStore.delOthersViews(selectedTag.value)
  moveToCurrentTag()
}

const closeAllTags = (view: TagView) => {
  tagsViewStore.delAllViews()
  if (affixTags.value.some(tag => tag.path === route.path)) {
    return
  }
  toLastView(tagsViewStore.visitedViews, view)
}

const toLastView = (visitedViews: TagView[], view: TagView) => {
  const latestView = visitedViews.slice(-1)[0]
  if (latestView && latestView.fullPath) {
    router.push(latestView.fullPath)
  } else {
    if (view.name === 'Dashboard') {
      router.replace({ path: '/redirect/dashboard' })
    } else {
      router.push('/')
    }
  }
}

const openMenu = (tag: TagView, e: MouseEvent) => {
  const menuMinWidth = 105
  const offsetLeft = (e.target as HTMLElement).getBoundingClientRect().left
  const offsetWidth = (e.target as HTMLElement).offsetWidth
  const maxLeft = window.innerWidth - menuMinWidth

  if (offsetLeft + offsetWidth + menuMinWidth > window.innerWidth) {
    left.value = maxLeft
  } else {
    left.value = offsetLeft + offsetWidth / 2
  }

  top.value = e.clientY
  visible.value = true
  selectedTag.value = tag
}

const closeMenu = () => {
  visible.value = false
}

const handleScroll = () => {
  closeMenu()
}

const resolve = (basePath: string, path: string) => {
  if (path.startsWith('/')) {
    return path
  }
  return `${basePath}/${path}`.replace(/\/+/g, '/')
}

watch(
  route,
  () => {
    addTags()
    moveToCurrentTag()
  },
  { immediate: true }
)

watch(visible, (value) => {
  if (value) {
    document.body.addEventListener('click', closeMenu)
  } else {
    document.body.removeEventListener('click', closeMenu)
  }
})

onMounted(() => {
  initTags()
  addTags()
})
</script>

<style lang="scss" scoped>
.tags-view-container {
  height: var(--layout-tagsview-height);
  width: 100%;
  background: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color-light);
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.12), 0 0 3px 0 rgba(0, 0, 0, 0.04);

  .tags-view-wrapper {
    .tags-view-item {
      display: inline-block;
      position: relative;
      cursor: pointer;
      height: 26px;
      line-height: 26px;
      border: 1px solid var(--el-border-color-light);
      color: var(--el-text-color-primary);
      background: var(--el-bg-color);
      padding: 0 8px;
      font-size: 12px;
      margin-left: 5px;
      margin-top: 4px;
      text-decoration: none;

      &:first-of-type {
        margin-left: 15px;
      }

      &:last-of-type {
        margin-right: 15px;
      }

      &.active {
        background-color: var(--el-color-primary);
        color: #fff;
        border-color: var(--el-color-primary);

        &::before {
          content: '';
          background: #fff;
          display: inline-block;
          width: 8px;
          height: 8px;
          border-radius: 50%;
          position: relative;
          margin-right: 2px;
        }
      }
    }
  }

  .contextmenu {
    margin: 0;
    background: var(--el-bg-color-overlay);
    z-index: 3000;
    position: absolute;
    list-style-type: none;
    padding: 5px 0;
    border-radius: 4px;
    font-size: 12px;
    font-weight: 400;
    color: var(--el-text-color-primary);
    box-shadow: 2px 2px 3px 0 rgba(0, 0, 0, 0.3);

    li {
      margin: 0;
      padding: 7px 16px;
      cursor: pointer;

      &:hover {
        background: var(--el-color-primary-light-9);
      }
    }
  }
}

.el-icon-close {
  width: 16px;
  height: 16px;
  vertical-align: 2px;
  border-radius: 50%;
  text-align: center;
  transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
  transform-origin: 100% 50%;

  &:before {
    transform: scale(0.6);
    display: inline-block;
    vertical-align: -3px;
  }

  &:hover {
    background-color: #b4bccc;
    color: #fff;
  }
}
</style>