import request from './request'

export interface TelegramDownloadSettings {
  download_all: boolean
  download_images: boolean
  download_audio: boolean
  download_videos: boolean
  download_archives: boolean
  download_documents: boolean
  download_programs: boolean
}

export interface TelegramSettings {
  api_id: string
  api_hash: string
  sqlite_db_name: string
  proxy: {
    enabled: boolean
    protocal: string
    ip: string
    port: number
  }
  history_days: number
  download_settings: TelegramDownloadSettings
}

// API响应类型
export interface ApiResponse<T = any> {
  err_code: number
  err_msg: string
  payload: T
}

export const systemApi = {
  // 获取Telegram设置
  getTelegramSettings() {
    return request.get<ApiResponse<TelegramSettings>>('/system/telegram-settings')
  },

  // 更新Telegram设置
  updateTelegramSettings(data: TelegramSettings) {
    return request.post<ApiResponse<null>>('/system/telegram-settings', data)
  }
}