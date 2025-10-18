import request from './request'

// ==================== 类型定义 ====================

/**
 * 文件夹树节点
 */
export interface FolderTreeNode {
  id: string                    // 如 'folder_1'
  label: string                 // 文件夹名称
  type: 'folder' | 'resource'   // 节点类型
  icon?: string                 // 图标名称
  description?: string          // 描述
  tg_user_id?: string          // 档案节点的TG用户ID
  status?: string              // 档案状态
  folder_id?: number | null    // 档案所属文件夹ID（resource节点专用）
  children?: FolderTreeNode[]  // 子节点
}

/**
 * 文件夹信息
 */
export interface ProfileFolder {
  id: number
  name: string
  parent_id: number | null
  user_id: number
  sort_order: number
  icon?: string
  description?: string
  is_deleted: boolean
  created_at: string
  updated_at: string
}

/**
 * 用户档案
 */
export interface UserProfile {
  id: number
  tg_user_id: string
  folder_id: number | null
  profile_name: string
  created_by: number
  status: 'draft' | 'generated' | 'archived'
  sort_order: number
  config: Record<string, any> | null
  last_refreshed_at: string | null
  is_deleted: boolean
  created_at: string
  updated_at: string
  folder?: {
    id: number
    name: string
    parent_id: number | null
  }
}

// ==================== 请求参数接口 ====================

export interface FolderListParams {
  parent_id?: number | null
  user_id?: number
  page?: number
  page_size?: number
}

export interface CreateFolderParams {
  name: string
  user_id: number
  parent_id?: number | null
}

export interface UpdateFolderParams {
  name?: string
}

export interface MoveFolderParams {
  new_parent_id: number | null
}

export interface ProfileListParams {
  folder_id?: number | null
  status?: 'draft' | 'generated' | 'archived'
  search_name?: string
  tg_user_id?: string
  page?: number
  page_size?: number
}

export interface CreateProfileParams {
  tg_user_id: string
  profile_name: string
  created_by: number
  folder_id?: number | null
  status?: 'draft' | 'generated' | 'archived'
}

export interface UpdateProfileParams {
  profile_name?: string
  status?: 'draft' | 'generated' | 'archived'
  folder_id?: number | null
  config?: Record<string, any>
}

export interface MoveProfileParams {
  new_folder_id: number | null
}

// ==================== API 客户端 ====================

/**
 * 用户档案 - 文件夹管理 API
 */
export const profileFolderApi = {
  /**
   * 获取文件夹树形结构
   */
  getTree(user_id?: number) {
    return request.get<{ tree_data: FolderTreeNode[] }>('/user-profile/folders/tree', {
      params: { user_id }
    })
  },

  /**
   * 获取文件夹列表(扁平结构)
   */
  getList(params: FolderListParams = {}) {
    return request.get<{ data: ProfileFolder[]; total: number; page: number; page_size: number }>(
      '/user-profile/folders',
      { params }
    )
  },

  /**
   * 创建文件夹
   */
  create(data: CreateFolderParams) {
    return request.post<{ folder: ProfileFolder }>('/user-profile/folders', data)
  },

  /**
   * 更新文件夹
   */
  update(folderId: number, data: UpdateFolderParams) {
    return request.put<{ folder: ProfileFolder }>(`/user-profile/folders/${folderId}`, data)
  },

  /**
   * 删除文件夹(软删除)
   */
  delete(folderId: number) {
    return request.delete(`/user-profile/folders/${folderId}`)
  },

  /**
   * 移动文件夹
   */
  move(folderId: number, data: MoveFolderParams) {
    return request.post<{ folder: ProfileFolder }>(`/user-profile/folders/${folderId}/move`, data)
  }
}

/**
 * 用户档案管理 API
 */
export const userProfileApi = {
  /**
   * 获取档案列表
   */
  getList(params: ProfileListParams = {}) {
    return request.get<{ data: UserProfile[]; total: number; page: number; page_size: number }>(
      '/user-profile/profiles',
      { params }
    )
  },

  /**
   * 获取单个档案详情
   */
  getDetail(profileId: number) {
    return request.get<{ profile: UserProfile; tg_user_info: any }>(
      `/user-profile/profiles/${profileId}`
    )
  },

  /**
   * 根据TG用户ID获取档案
   */
  getByTgUser(tgUserId: string) {
    return request.get<{ profile: UserProfile; tg_user_info: any }>(
      `/user-profile/profiles/by-tg-user/${tgUserId}`
    )
  },

  /**
   * 创建档案
   */
  create(data: CreateProfileParams) {
    return request.post<{ profile: UserProfile }>('/user-profile/profiles', data)
  },

  /**
   * 更新档案
   */
  update(profileId: number, data: UpdateProfileParams) {
    return request.put<{ profile: UserProfile }>(`/user-profile/profiles/${profileId}`, data)
  },

  /**
   * 删除档案(软删除)
   */
  delete(profileId: number) {
    return request.delete(`/user-profile/profiles/${profileId}`)
  },

  /**
   * 移动档案到新文件夹
   */
  move(profileId: number, data: MoveProfileParams) {
    return request.post<{ profile: UserProfile }>(`/user-profile/profiles/${profileId}/move`, data)
  },

  /**
   * 刷新档案数据
   */
  refresh(profileId: number) {
    return request.post<{ profile: UserProfile }>(`/user-profile/profiles/${profileId}/refresh`)
  }
}
