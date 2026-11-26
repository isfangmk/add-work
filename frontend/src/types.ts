// 领域模型：与后端 snake_case 契约对应

export interface ApiEnvelope<T = unknown> {
  success: boolean
  msg: string | null
  data: T | null
}

export interface CurrentUser {
  username: string
  git_email: string
}

export interface Workspace {
  workspace_name: string
  workspace_id: string
  workspace_key: string
  isFavorite?: boolean
}

export interface Sprint {
  object_id: string
  name: string
  workspace_name: string
}

export interface Requirement {
  id: string
  key: string
  name: string
}

export interface WorkItem {
  /** 前端列表行的稳定标识，不提交到后端 */
  id?: string
  object_id?: string
  name: string
  time: string | number
  date: string
  sprint: string
  sprint_id: string
  workspace_name: string
  requirement_id: string
  requirement_name: string
  requirement_key: string
}

export interface CalendarDay {
  date: string
  items: WorkItem[]
  total: number
}

export type CalendarData = Record<string, WorkItem[]>

export interface FavoriteWorkspace {
  workspace_name: string
  workspace_key: string
  workspace_id?: string
}

export interface TaskLogLine {
  message: string
  type: 'success' | 'error' | 'info' | 'default'
}

export interface TaskStatus {
  running: boolean
  success?: boolean
  log: string[]
}

export interface LlmSummary {
  [date: string]: string
}

export const EMPTY_WORK_ITEM: WorkItem = {
  id: '',
  name: '',
  time: '',
  date: '',
  sprint: '',
  sprint_id: '',
  workspace_name: '',
  requirement_id: '',
  requirement_name: '',
  requirement_key: '',
}

export function createWorkItem(patch: Partial<WorkItem> = {}): WorkItem {
  return { ...EMPTY_WORK_ITEM, id: crypto.randomUUID(), ...patch }
}
