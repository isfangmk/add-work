import type {
  ApiEnvelope,
  CalendarData,
  CurrentUser,
  FavoriteWorkspace,
  LlmSummary,
  Requirement,
  Sprint,
  TaskStatus,
  Workspace,
} from '@/types'

const isDev = import.meta.env.DEV
const PREFIX = '/add-work'
export const API_BASE = isDev ? `http://127.0.0.1:5000${PREFIX}` : PREFIX

export const API = {
  currentUser: `${API_BASE}/get-current-user`,
  workItems: `${API_BASE}/get-work-items-by-range`,
  startTask: `${API_BASE}/start-task`,
  taskStatus: `${API_BASE}/task-status`,
  llmSummary: `${API_BASE}/llm-summary-by-range`,
  workspaceList: `${API_BASE}/get-workspace-list`,
  sprintList: `${API_BASE}/get-sprint-list`,
  requirementSearch: `${API_BASE}/search-requirements`,
  favoriteWorkspaces: `${API_BASE}/get-favorite-workspaces`,
  saveFavoriteWorkspaces: `${API_BASE}/save-favorite-workspaces`,
  feedback: `${API_BASE}/feedback`,
} as const

function formatDetail(detail: unknown): string {
  if (!detail) return ''
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail
      .map((item: { loc?: (string | number)[]; msg?: string }) => {
        const field = item.loc?.filter((p) => p !== 'body').join('.')
        return field ? `${field}: ${item.msg || '参数错误'}` : item.msg || '参数错误'
      })
      .join('；')
  }
  return ''
}

async function parseResponse<T>(res: Response): Promise<ApiEnvelope<T>> {
  let body: ApiEnvelope<T> & { detail?: unknown; msg?: string | null }
  try {
    body = await res.json()
  } catch {
    throw new Error(`服务器返回了无效响应（HTTP ${res.status}）`)
  }
  if (!res.ok) {
    throw new Error(formatDetail(body.detail) || body.msg || `请求失败（HTTP ${res.status}）`)
  }
  if ('success' in body && body.success === false) {
    throw new Error(body.msg || '请求失败')
  }
  return body
}

async function postJson<T>(url: string, payload: unknown): Promise<ApiEnvelope<T>> {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  return parseResponse<T>(res)
}

export function fetchCurrentUser(cookie: string) {
  return postJson<CurrentUser>(API.currentUser, { cookie })
}

export function fetchWorkItems(payload: {
  cookie: string
  start_date: string
  end_date: string
  username: string
  git_email: string
}) {
  return postJson<CalendarData>(API.workItems, payload)
}

export function fetchWorkspaces(cookie: string) {
  return postJson<Workspace[]>(API.workspaceList, { cookie })
}

export function fetchSprints(cookie: string, workspaceName: string, allWorkspaces = false, keyword = '') {
  return postJson<Sprint[]>(API.sprintList, {
    cookie,
    workspace_name: workspaceName,
    all_workspaces: allWorkspaces,
    keyword,
  })
}

export function searchRequirements(cookie: string, keyword = '') {
  return postJson<Requirement[]>(API.requirementSearch, { cookie, keyword })
}

export function fetchFavoriteWorkspaces(username: string) {
  return postJson<FavoriteWorkspace[]>(API.favoriteWorkspaces, { username })
}

export function saveFavoriteWorkspaces(username: string, workspaces: FavoriteWorkspace[]) {
  return postJson<null>(API.saveFavoriteWorkspaces, { username, workspaces })
}

export function fetchLlmSummary(payload: {
  git_email: string
  start_date: string
  end_date: string
  exclude_dates: string[]
}) {
  return postJson<LlmSummary>(API.llmSummary, payload)
}

export interface StartTaskPayload {
  username: string
  cookie: string
  source_object_id: string
  workspace_name: string
  is_update?: boolean
  names: string[]
  sprint_ids: string[]
  times: number[]
  dates: string[]
  workspace_names?: string[]
  requirement_ids: string[]
}

export function startTask(payload: StartTaskPayload) {
  return postJson<{ task_id: string }>(API.startTask, payload)
}

export async function pollTaskStatus(taskId: string): Promise<TaskStatus> {
  const res = await fetch(`${API.taskStatus}?task_id=${encodeURIComponent(taskId)}`)
  let body: TaskStatus & { detail?: unknown }
  try {
    body = await res.json()
  } catch {
    throw new Error(`服务器返回了无效响应（HTTP ${res.status}）`)
  }
  if (!res.ok) {
    throw new Error(formatDetail(body.detail) || `请求失败（HTTP ${res.status}）`)
  }
  // /task-status 返回裸结构 { running, log, success? }，不是统一 envelope
  return { running: body.running, log: body.log || [], success: body.success }
}

export function submitFeedback(payload: unknown) {
  return postJson<null>(API.feedback, payload)
}
