const isDev = process.env.NODE_ENV === 'development';
const PREFIX = '/add-work';
export const API_BASE = isDev ? `http://127.0.0.1:5000${PREFIX}` : PREFIX;

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
  feedback: `${API_BASE}/feedback`
};

// 后端成功响应统一为 {success, msg, data}；错误时可能是 {detail} 或 {msg}
interface ApiEnvelope {
  success?: boolean;
  msg?: string;
  detail?: string | Array<{ msg?: string; loc?: (string | number)[] }>;
  data?: any;
}

function formatDetail(detail: ApiEnvelope["detail"]): string {
  if (!detail) return '';
  if (typeof detail === 'string') return detail;
  // FastAPI 422 校验错误：detail 是 [{loc, msg, type}, ...]
  return detail
    .map((item) => {
      const field = item.loc?.filter((p) => p !== 'body').join('.');
      return field ? `${field}: ${item.msg || '参数错误'}` : item.msg || '参数错误';
    })
    .join('；');
}

async function parseResponse(res: Response): Promise<any> {
  let body: ApiEnvelope;
  try {
    body = await res.json();
  } catch {
    throw new Error(`服务器返回了无效响应（HTTP ${res.status}）`);
  }
  if (!res.ok) {
    throw new Error(formatDetail(body.detail) || body.msg || `请求失败（HTTP ${res.status}）`);
  }
  return body;
}

async function postJson(url: string, body: unknown): Promise<any> {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  return parseResponse(res);
}

export function fetchCurrentUser(cookie: string): Promise<any> {
  return postJson(API.currentUser, { cookie });
}

export function fetchWorkItems(payload: unknown): Promise<any> {
  return postJson(API.workItems, payload);
}

export function fetchWorkspaces(cookie: string): Promise<any> {
  return postJson(API.workspaceList, { cookie });
}

export function fetchSprints(cookie: string, workspaceName: string, allWorkspaces = false, keyword = ''): Promise<any> {
  return postJson(API.sprintList, { cookie, workspace_name: workspaceName, all_workspaces: allWorkspaces, keyword });
}

export function searchRequirements(cookie: string, keyword: string = ''): Promise<any> {
  return postJson(API.requirementSearch, { cookie, keyword });
}

export function fetchFavoriteWorkspaces(username: string): Promise<any> {
  return postJson(API.favoriteWorkspaces, { username });
}

export function saveFavoriteWorkspaces(username: string, workspaces: unknown[]): Promise<any> {
  return postJson(API.saveFavoriteWorkspaces, { username, workspaces });
}

export function fetchLlmSummary(payload: unknown): Promise<any> {
  return postJson(API.llmSummary, payload);
}

export function startTask(payload: unknown): Promise<any> {
  return postJson(API.startTask, payload);
}

export async function pollTaskStatus(taskId: string): Promise<any> {
  const res = await fetch(`${API.taskStatus}?task_id=${encodeURIComponent(taskId)}`);
  return parseResponse(res);
}

export function submitFeedback(payload: unknown): Promise<any> {
  return postJson(API.feedback, payload);
}
