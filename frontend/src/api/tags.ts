import request from './request'

export interface Tag {
  id: number
  name: string
  color: string
  status: string
  created_at: string
  updated_at: string
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
}

export const tagsApi = new TagsApi()