import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { RouteLocationNormalized } from 'vue-router'

export interface TagView extends Partial<RouteLocationNormalized> {
  title?: string
}

export const useTagsViewStore = defineStore('tagsView', () => {
  const visitedViews = ref<TagView[]>([])
  const cachedViews = ref<string[]>([])

  // 添加访问的视图
  const addView = (view: TagView) => {
    addVisitedView(view)
    addCachedView(view)
  }

  // 添加访问的视图
  const addVisitedView = (view: TagView) => {
    if (visitedViews.value.some(v => v.path === view.path)) return
    visitedViews.value.push(
      Object.assign({}, view, {
        title: view.meta?.title || 'no-name'
      })
    )
  }

  // 添加缓存视图
  const addCachedView = (view: TagView) => {
    if (cachedViews.value.includes(view.name as string)) return
    if (view.meta?.noCache) return
    if (view.name) {
      cachedViews.value.push(view.name as string)
    }
  }

  // 删除视图
  const delView = (view: TagView) => {
    delVisitedView(view)
    delCachedView(view)
  }

  // 删除访问的视图
  const delVisitedView = (view: TagView) => {
    for (const [i, v] of visitedViews.value.entries()) {
      if (v.path === view.path) {
        visitedViews.value.splice(i, 1)
        break
      }
    }
  }

  // 删除缓存视图
  const delCachedView = (view: TagView) => {
    const index = cachedViews.value.indexOf(view.name as string)
    index > -1 && cachedViews.value.splice(index, 1)
  }

  // 删除其他视图
  const delOthersViews = (view: TagView) => {
    delOthersVisitedViews(view)
    delOthersCachedViews(view)
  }

  // 删除其他访问的视图
  const delOthersVisitedViews = (view: TagView) => {
    visitedViews.value = visitedViews.value.filter(v => {
      return v.meta?.affix || v.path === view.path
    })
  }

  // 删除其他缓存视图
  const delOthersCachedViews = (view: TagView) => {
    const index = cachedViews.value.indexOf(view.name as string)
    if (index > -1) {
      cachedViews.value = cachedViews.value.slice(index, index + 1)
    } else {
      cachedViews.value = []
    }
  }

  // 删除所有视图
  const delAllViews = () => {
    delAllVisitedViews()
    delAllCachedViews()
  }

  // 删除所有访问的视图
  const delAllVisitedViews = () => {
    visitedViews.value = visitedViews.value.filter(tag => tag.meta?.affix)
  }

  // 删除所有缓存视图
  const delAllCachedViews = () => {
    cachedViews.value = []
  }

  return {
    visitedViews,
    cachedViews,
    addView,
    addVisitedView,
    addCachedView,
    delView,
    delVisitedView,
    delCachedView,
    delOthersViews,
    delOthersVisitedViews,
    delOthersCachedViews,
    delAllViews,
    delAllVisitedViews,
    delAllCachedViews
  }
})