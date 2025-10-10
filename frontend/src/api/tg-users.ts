import request from './request'

export interface TgUser {
  id: number
  user_id: string
  username: string
  first_name: string
  last_name?: string
  nickname?: string
  avatar?: string
  phone?: string
  bio?: string
  notes?: string
  tags?: string
  tag_id_list?: string
  status: string
  last_seen?: string
  created_at: string
  updated_at: string
  is_key_focus?: boolean
  chat_id?: string
  group_name?: string
}

export interface UserListParams {
  page?: number
  page_size?: number
  username?: string
  user_id?: string
  notes?: string
  keyword?: string
  group_id?: string
  tag_ids?: string
  search_nickname?: string
  search_desc?: string
  search_group_id?: string
  search_username?: string
  remark?: string
}

export interface UpdateUserParams {
  tg_user_id: number
  remark?: string
  tag_id_list?: string
}

export const tgUsersApi = {
  // 获取用户列表
  getList(params: UserListParams = {}) {
    return request.get('/tg/group_user/list', {
      params: { ...params, format: 'json' }
    })
  },

  // 更新用户信息（备注和标签）
  updateUser(data: UpdateUserParams) {
    return request.post('/tg/group_user/tag/update', data)
  },

  // 切换用户关注状态
  toggleFocus(tg_user_id: number) {
    return request.post('/tg/group_user/focus/toggle', { tg_user_id })
  },

  // 搜索用户
  search(params: UserListParams) {
    return request.get('/tg/users/search', { params })
  },

  // 获取重点关注用户（支持分页）
  getKeyFocusList(params: UserListParams = {}) {
    return request.get('/tg/group_user/key_focus', { 
      params: { ...params, format: 'json' }
    })
  },

  // 根据user_id获取用户信息
  getUserByUserId(user_id: string) {
    return request.get('/tg/group_user/by_user_id', {
      params: { user_id }
    })
  }
}