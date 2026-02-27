const isDev = process.env.NODE_ENV === 'development';
const PREFIX = '/add-work';
export const API_BASE = isDev ? `http://127.0.0.1:5000${PREFIX}` : PREFIX;

export const API = {
  workItems: `${API_BASE}/get-work-items-by-range`,
  startTask: `${API_BASE}/start-task`,
  taskStatus: `${API_BASE}/task-status`,
  llmSummary: `${API_BASE}/llm-summary-by-range`,
  sprintList: `${API_BASE}/get-sprint-list`,
  feedback: `${API_BASE}/feedback`
};

async function postJson(url, body) {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  return res.json();
}

export function fetchWorkItems(payload) {
  return postJson(API.workItems, payload);
}

export function fetchSprints(cookie, workspaceName) {
  return postJson(API.sprintList, { cookie, workspace_name: workspaceName });
}

export function fetchLlmSummary(payload) {
  return postJson(API.llmSummary, payload);
}

export function startTask(payload) {
  return postJson(API.startTask, payload);
}

export async function pollTaskStatus(taskId) {
  const res = await fetch(`${API.taskStatus}?task_id=${taskId}`);
  return res.json();
}

export function submitFeedback(payload) {
  return postJson(API.feedback, payload);
}
