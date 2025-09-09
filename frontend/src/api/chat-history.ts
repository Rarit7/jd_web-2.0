import request from './request'

export interface DocumentInfo {
  path: string
  ext: string
  mime_type: string
  is_sticker?: boolean
  sticker_type?: string
  display_text?: string
  display_icon?: string
  filename_origin?: string
  file_size?: number
}

export interface ChatMessage {
  id: number
  group_name: string
  message: string
  nickname: string
  postal_time: string
  username: string
  user_id: string
  user_avatar: string
  is_key_focus?: boolean
  photo_paths: string[]
  document_paths: string[]  // 保持向后兼容
  documents: DocumentInfo[]  // 新增：包含类型信息的文档列表
  reply_to_msg_id: number
  message_ids: string
  chat_id: string
}

export interface ChatHistoryParams {
  page?: number
  page_size?: number
  search_content?: string
  search_tag?: string
  start_date?: string
  end_date?: string
  message_id?: number
  reply_to_msg_id?: number
  search_group_id?: string[]
  search_user_id?: string[]
  search_account_id?: string[]
  show_all?: string
}

export interface ChatExportParams {
  chat_id: string
  start_time?: string
  end_time?: string
  get_photo: boolean
}

export interface ChatHistoryResponse {
  err_code: number
  err_msg: string
  payload: {
    data: ChatMessage[]
    total_pages: number
    current_page: number
    total_records: number
    group_list: Array<{chat_id: string, group_name: string}>
    group_user_list: Array<{user_id: string, chat_id: string, nickname: string, desc: string, photo: string, username: string}>
    tg_accounts: Array<{account_id: number, username: string}>
  }
}

export interface UserChatHistoryResponse {
  err_code: number
  err_msg: string
  payload: {
    data: ChatMessage[]
    total_pages: number
    current_page: number
    total_records: number
    group_info: {chat_id: string, group_name: string, title: string}
    user_info: {user_id: string, username: string, nickname: string, avatar_path: string, is_key_focus: boolean}
  }
}

export const chatHistoryApi = {
  // 获取聊天记录列表
  getList: (params: ChatHistoryParams = {}) => {
    // 设置默认参数
    const defaultParams = {
      page: 1,
      page_size: 20,
      ...params
    }
    
    return request.get<ChatHistoryResponse>('/tg/chat_room/history/json', { 
      params: defaultParams 
    })
  },

  // 根据群组ID获取聊天记录
  getByGroupId: (groupId: string, params: Omit<ChatHistoryParams, 'search_group_id'> = {}) => {
    // 设置默认参数
    const defaultParams = {
      page: 1,
      page_size: 20,
      ...params
    }
    
    return request.get<ChatHistoryResponse>(`/tg/chat_room/history/by_group/${groupId}`, { 
      params: defaultParams 
    })
  },

  // 根据用户ID和群组ID获取聊天记录
  getByUserInGroup: (groupId: string, userId: string, params: Omit<ChatHistoryParams, 'search_group_id' | 'search_user_id'> = {}) => {
    // 设置默认参数
    const defaultParams = {
      page: 1,
      page_size: 20,
      ...params
    }
    
    return request.get<UserChatHistoryResponse>(`/tg/chat_room/history/by_user_in_group/${groupId}/${userId}`, { 
      params: defaultParams 
    })
  },

  // 根据私人聊天ID获取聊天记录
  getByPrivateChat: (chatId: string, params: Omit<ChatHistoryParams, 'search_group_id' | 'search_user_id'> = {}) => {
    // 设置默认参数
    const defaultParams = {
      page: 1,
      page_size: 20,
      ...params
    }
    
    return request.get<ChatHistoryResponse>(`/tg/chat_room/history/by_private_chat/${chatId}`, { 
      params: defaultParams 
    })
  },

  // 导出聊天记录
  export: (params: ChatExportParams) => {
    return request.get('/tg/chat_room/history/download', {
      params,
      responseType: 'blob'
    })
  },

  // 根据消息ID查找消息所在的页数
  findMessagePage: (groupId: string, messageId: number, pageSize: number = 20) => {
    return request.get(`/tg/chat_room/history/find_page/${groupId}/${messageId}`, {
      params: { page_size: pageSize }
    })
  },

  // 触发获取新的Telegram聊天历史记录
  fetchNewHistory: () => {
    return request.post('/tg/chat_room/history/fetch_new')
  },

  // 获取用户统计数据
  getUserStats: (userId: string) => {
    return request.get(`/tg/user/stats/${userId}`)
  }
}