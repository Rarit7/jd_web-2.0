import request from './request'

export interface TgGroup {
  id: number
  name: string
  chat_id: string
  status: string
  desc: string
  tag: string
  tag_id_list: string
  created_at: string
  account_id: string
  photo: string
  title: string
  remark: string
  latest_postal_time: string
  three_days_ago: number
  group_type: number
  members_count: number
  members_increment: number
  records_count: number
  records_increment: number
}

export interface TgGroupListParams {
  account_id?: string
  group_name?: string
  chat_id?: string
  group_link?: string
  remark?: string
  tag_ids?: string
}

export interface AddGroupParams {
  name: string
  session_name?: string
}

export interface UpdateGroupTagParams {
  group_id: number
  tag_id_list: string
  remark: string
}

export interface FetchHistoryParams {
  group_name: string
  chat_id: number
}

export const tgGroupsApi = {
  // 获取群组列表
  getList: (params?: TgGroupListParams) => {
    return request.get<{
      err_code: number
      err_msg: string
      payload: {
        data: TgGroup[]
        tag_list: any[]
        default_account_id: string
        default_group_name: string
        default_remark: string
        role_ids: number[]
      }
    }>('/tg/group/list/json', { params })
  },

  // 删除群组
  delete: (group_id: number) => {
    return request.get(`/tg/group/delete?group_id=${group_id}`)
  },

  // 添加群组
  add: (data: AddGroupParams) => {
    return request.post('/tg/group/add', data, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    })
  },

  // 更新群组标签
  updateTag: (data: UpdateGroupTagParams) => {
    return request.post('/tg/group/tag/update', data)
  },

  // 获取群组历史
  fetchHistory: (data: FetchHistoryParams) => {
    return request.post('/tg/group/fetch-history', data)
  },

  // 下载群组数据
  download: (params?: TgGroupListParams) => {
    return request.get('/tg/group/download', { 
      params,
      responseType: 'blob'
    })
  }
}