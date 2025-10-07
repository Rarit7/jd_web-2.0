/**
 * 广告追踪系统 TypeScript 类型定义
 */

// ==================== 枚举类型 ====================

/**
 * 内容类型
 */
export enum ContentType {
  URL = 'url',
  TELEGRAM_ACCOUNT = 'telegram_account',
  T_ME_INVITE = 't_me_invite',
  T_ME_CHANNEL_MSG = 't_me_channel_msg',
  T_ME_PRIVATE_INVITE = 't_me_private_invite',
  TELEGRAPH = 'telegraph'
}

/**
 * 来源类型
 */
export enum SourceType {
  CHAT = 'chat',
  USER_DESC = 'user_desc',
  USERNAME = 'username',
  NICKNAME = 'nickname',
  GROUP_INTRO = 'group_intro'
}

// ==================== 额外信息类型 ====================

/**
 * IP地理位置信息
 */
export interface IpLocation {
  country: string
  country_code: string
  region?: string
  city?: string
  isp?: string
  organization?: string
}

/**
 * t.me目标信息
 */
export interface TmeTargetInfo {
  name?: string
  avatar_url?: string
  description?: string
  member_count?: number
}

/**
 * URL类型的额外信息
 */
export interface UrlExtraInfo {
  domain?: string
  is_phishing?: boolean
  phishing_check_api?: string
  threat_types?: string[]
  website_title?: string
  status_code?: number
  is_short_url?: boolean
  original_url?: string
  final_url?: string
  redirect_chain_length?: number
  ip_address?: string
  ip_location?: IpLocation
}

/**
 * Telegram账户额外信息
 */
export interface TelegramAccountExtraInfo {
  account_type?: 'user' | 'bot' | 'channel'
}

/**
 * t.me链接额外信息
 */
export interface TmeLinkExtraInfo {
  tme_target_type?: 'user' | 'group' | 'channel'
  tme_target_name?: string
  tme_target_info?: TmeTargetInfo
}

/**
 * Telegraph文章额外信息
 */
export interface TelegraphExtraInfo {
  telegraph_title?: string
  telegraph_content?: string
  telegraph_images?: string[]
  telegraph_violation_score?: number
}

/**
 * 额外信息联合类型
 */
export type ExtraInfo = UrlExtraInfo & TelegramAccountExtraInfo & TmeLinkExtraInfo & TelegraphExtraInfo

// ==================== 实体类型 ====================

/**
 * 广告追踪记录
 */
export interface AdTracking {
  id: number
  content: string
  content_type: ContentType
  normalized_content: string
  extra_info: ExtraInfo | null
  merchant_name: string | null
  source_type: SourceType
  source_id: string
  user_id: string | null
  chat_id: string | null
  first_seen: string
  last_seen: string
  occurrence_count: number
  tag_ids?: number[]
  created_at?: string
  updated_at?: string
}

/**
 * 用户信息（简化）
 */
export interface UserInfo {
  user_id: string
  nickname?: string
  username?: string
  avatar_url?: string
  description?: string
}

/**
 * 群组信息（简化）
 */
export interface GroupInfo {
  chat_id: string
  group_name?: string
  group_title?: string
  avatar_url?: string
  description?: string
}

/**
 * 广告追踪详情（包含关联信息）
 */
export interface AdTrackingDetail extends AdTracking {
  user_info?: UserInfo
  group_info?: GroupInfo
  source_text?: string | null
  source_timestamp?: string | null
}

// ==================== API 请求/响应类型 ====================

/**
 * 列表查询参数
 */
export interface AdTrackingListParams {
  page?: number
  page_size?: number
  content_type?: ContentType
  user_id?: string
  chat_id?: string
  source_type?: SourceType
  start_date?: string
  end_date?: string
  search?: string
  sort_by?: 'first_seen' | 'last_seen' | 'occurrence_count'
  sort_order?: 'asc' | 'desc'
}

/**
 * 列表响应数据
 */
export interface AdTrackingListResponse {
  data: AdTracking[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

/**
 * 按域名搜索参数
 */
export interface SearchByDomainParams {
  domain: string
  page?: number
  page_size?: number
}

/**
 * 按域名搜索响应
 */
export interface SearchByDomainResponse {
  data: AdTracking[]
  total: number
  page: number
  page_size: number
  domain: string
}

/**
 * 统计参数
 */
export interface StatsParams {
  start_date?: string
  end_date?: string
}

/**
 * 统计响应 - 总览
 */
export interface StatsSummary {
  total_records: number
  total_occurrences: number
  unique_users: number
  unique_chats: number
  unique_merchants: number
}

/**
 * 按内容类型统计
 */
export interface ContentTypeStats {
  content_type: ContentType
  count: number
  total_occurrences: number
}

/**
 * 按来源类型统计
 */
export interface SourceTypeStats {
  source_type: SourceType
  count: number
}

/**
 * Top群组统计
 */
export interface TopChat {
  chat_id: string
  count: number
  group_name?: string
}

/**
 * Top用户统计
 */
export interface TopUser {
  user_id: string
  count: number
  nickname?: string
}

/**
 * Top商家统计
 */
export interface TopMerchant {
  merchant_name: string
  count: number
  total_occurrences: number
}

/**
 * 统计响应
 */
export interface StatsResponse {
  summary: StatsSummary
  content_type_stats: ContentTypeStats[]
  source_type_stats: SourceTypeStats[]
  top_chats: TopChat[]
  top_users: TopUser[]
  top_merchants: TopMerchant[]
}

/**
 * 任务执行参数
 */
export interface ExecuteTaskParams {
  task_type: 'daily' | 'historical' | 'chat_record' | 'user_info' | 'group_info'
  target_date?: string
  batch_size?: number
  max_batches?: number
  record_id?: number
  user_id?: string
  chat_id?: string
}

/**
 * 任务执行响应
 */
export interface ExecuteTaskResponse {
  task_id: string
  task_type: string
  status: string
}

/**
 * 任务状态响应
 */
export interface TaskStatusResponse {
  task_id: string
  status: 'PENDING' | 'STARTED' | 'SUCCESS' | 'FAILURE' | 'RETRY'
  result?: any
  info?: string
}

/**
 * 添加标签参数
 */
export interface AddTagsParams {
  tag_ids: number[]
}

/**
 * 添加标签响应
 */
export interface AddTagsResponse {
  message: string
  added_count: number
}

/**
 * 删除响应
 */
export interface DeleteResponse {
  message: string
}

/**
 * 标准API响应包装
 */
export interface ApiResponse<T = any> {
  err_code: number
  err_msg: string
  payload: T
}

// ==================== UI 状态类型 ====================

/**
 * 筛选条件
 */
export interface FilterConditions {
  contentTypes: ContentType[]
  sourceTypes: SourceType[]
  tagIds: number[]
  dateRange: [string, string] | null
  search: string
  userId: string
  chatId: string
  domain: string
  sortBy: 'first_seen' | 'last_seen' | 'occurrence_count'
  sortOrder: 'asc' | 'desc'
}

/**
 * 分页信息
 */
export interface Pagination {
  page: number
  pageSize: number
  total: number
}
