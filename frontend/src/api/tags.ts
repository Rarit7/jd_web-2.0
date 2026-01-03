import request from './request'

export interface Tag {
  id: number
  name: string
  color: string
  is_nsfw: boolean
  status: string
  created_at: string
  updated_at: string
  keywords?: TagKeywordMapping[] // 关联的关键词（用于预览）
  keywordsTotal?: number // 关键词总数
}

export interface TagsResponse {
  err_code: number
  err_msg: string
  payload: {
    data: Tag[]
  }
}

export interface ApiResponse {
  err_code: number
  err_msg: string
  payload: any
}

export interface TagKeywordMapping {
  id: number
  tag_id: number
  keyword: string
  is_active: boolean
  auto_focus: boolean
  created_at: string
  updated_at: string
}

export interface AutoTagLog {
  id: number
  tg_user_id: string
  tag_id: number
  keyword: string
  source_type: 'chat' | 'nickname' | 'desc'
  source_id: string
  detail_info?: {
    user_id: string
    user_nickname: string
    user_username: string
    // chat 类型特有字段
    chat_id?: string
    chat_title?: string
    message_id?: string
    message_text?: string
    message_date?: string
    // nickname 类型特有字段
    old_nickname?: string
    new_nickname?: string
    // desc 类型特有字段
    old_desc?: string
    new_desc?: string
    // 通用字段
    matched_text: string
  }
  created_at: string
}

export interface TaskStatus {
  task_id: string
  status: string
  result: any
  info: any
}

export interface AutoTagStats {
  summary: {
    total_logs: number
    unique_users: number
    unique_tags: number
  }
  tag_stats: Array<{
    tag_id: number
    tag_name: string
    tag_color: string
    tag_count: number
    user_count: number
  }>
  source_stats: Array<{
    source_type: string
    count: number
  }>
  keyword_stats: Array<{
    keyword: string
    count: number
  }>
}

class TagsApi {
  // 获取标签列表
  async getList(): Promise<TagsResponse> {
    const response = await request.get('/tag/list', {
      params: { format: 'json' }
    })
    return response.data
  }

  // 添加标签
  async add(data: { name: string; color: string }): Promise<ApiResponse> {
    const response = await request.post('/tag/add', data, {
      headers: {
        'Content-Type': 'application/json'
      }
    })
    return response.data
  }

  // 编辑标签
  async edit(data: { id: number; name: string; color: string }): Promise<ApiResponse> {
    const response = await request.put('/tag/edit', data, {
      headers: {
        'Content-Type': 'application/json'
      }
    })
    return response.data
  }

  // 删除标签
  async delete(id: number): Promise<ApiResponse> {
    const response = await request.delete('/tag/delete', {
      data: { id },
      headers: {
        'Content-Type': 'application/json'
      }
    })
    return response.data
  }

  // 创建标签关键词映射
  async createKeywordMapping(data: { tag_id: number; keyword: string; auto_focus?: boolean; is_active?: boolean }): Promise<ApiResponse> {
    const response = await request.post('/tag/tag-keywords', data, {
      headers: {
        'Content-Type': 'application/json'
      }
    })
    return response.data
  }

  // 获取标签的关键词列表
  async getKeywordMappings(tagId: number, params?: { page?: number; page_size?: number; is_active?: boolean }): Promise<ApiResponse> {
    const response = await request.get(`/tag/tag-keywords/${tagId}`, { params })
    return response.data
  }

  // 获取标签的所有活跃关键词（无分页）
  async getAllTagKeywords(tagId: number): Promise<ApiResponse> {
    const response = await request.get(`/tag/tag-keywords/${tagId}/all`)
    return response.data
  }

  // 更新关键词映射
  async updateKeywordMapping(keywordId: number, data: { keyword?: string; auto_focus?: boolean; is_active?: boolean }): Promise<ApiResponse> {
    const response = await request.put(`/tag/tag-keywords/${keywordId}`, data, {
      headers: {
        'Content-Type': 'application/json'
      }
    })
    return response.data
  }

  // 删除关键词映射
  async deleteKeywordMapping(keywordId: number): Promise<ApiResponse> {
    const response = await request.delete(`/tag/tag-keywords/${keywordId}`)
    return response.data
  }

  // 批量创建关键词映射
  async batchCreateKeywords(data: { tag_id: number; keywords: string[]; auto_focus?: boolean }): Promise<ApiResponse> {
    const response = await request.post('/tag/tag-keywords/batch', data, {
      headers: {
        'Content-Type': 'application/json'
      }
    })
    return response.data
  }

  // 触发自动标签任务
  async executeAutoTagging(data: { type: 'daily' | 'historical' }): Promise<ApiResponse> {
    const response = await request.post('/tag/auto-tagging/execute', data, {
      headers: {
        'Content-Type': 'application/json'
      },
      timeout: 120000 // 2分钟超时，因为任务可能需要较长时间
    })
    return response.data
  }

  // 获取任务状态
  async getTaskStatus(taskId: string): Promise<ApiResponse> {
    const response = await request.get(`/tag/auto-tagging/task-status/${taskId}`)
    return response.data
  }

  // 获取自动标签日志
  async getAutoTagLogs(params?: { page?: number; page_size?: number; tag_id?: number; user_id?: string; source_type?: string }): Promise<ApiResponse> {
    const response = await request.get('/tag/auto-tagging/logs', { params })
    return response.data
  }

  // 获取自动标签统计
  async getAutoTagStats(): Promise<{ err_code: number; err_msg: string; payload: AutoTagStats }> {
    const response = await request.get('/tag/auto-tagging/stats')
    return response.data
  }

  // 预览自动标签效果
  async previewAutoTagging(data: { text: string }): Promise<ApiResponse> {
    const response = await request.post('/tag/auto-tagging/preview', data, {
      headers: {
        'Content-Type': 'application/json'
      }
    })
    return response.data
  }
}

export const tagsApi = new TagsApi()