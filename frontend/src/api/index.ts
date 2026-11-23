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

// 后端响应结构在各接口间不统一，调用方（JS 组件）按 any 消费，保持渐进迁移
async function postJson(url: string, body: unknown): Promise<any> {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  return res.json();
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

export function fetchSprints(cookie: string, workspaceName: string): Promise<any> {
  return postJson(API.sprintList, { cookie, workspace_name: workspaceName });
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
  const res = await fetch(`${API.taskStatus}?task_id=${taskId}`);
  return res.json();
}

export function submitFeedback(payload: unknown): Promise<any> {
  return postJson(API.feedback, payload);
}
