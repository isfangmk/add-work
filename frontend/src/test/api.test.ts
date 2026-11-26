import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import {
  API,
  fetchCurrentUser,
  fetchWorkItems,
  fetchSprints,
  searchRequirements,
  startTask,
  pollTaskStatus,
  submitFeedback,
} from '@/lib/api'

function mockResponse(body: unknown, ok = true, status = 200) {
  return { ok, status, json: async () => body } as Response
}

describe('API 层', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn())
  })
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('端点使用 snake_case 契约路径', () => {
    expect(API.currentUser).toContain('/get-current-user')
    expect(API.sprintList).toContain('/get-sprint-list')
    expect(API.requirementSearch).toContain('/search-requirements')
  })

  it('fetchCurrentUser 发送 cookie 并返回 data', async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      mockResponse({ success: true, msg: 'ok', data: { username: 'fang', git_email: 'f@x.com' } }),
    )
    const res = await fetchCurrentUser('COOKIE')
    expect(fetch).toHaveBeenCalledWith(
      API.currentUser,
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ cookie: 'COOKIE' }),
      }),
    )
    expect(res.data!.username).toBe('fang')
  })

  it('fetchWorkItems 使用 snake_case 日期字段', async () => {
    vi.mocked(fetch).mockResolvedValueOnce(mockResponse({ success: true, data: {} }))
    await fetchWorkItems({
      cookie: 'C',
      start_date: '2026-11-23',
      end_date: '2026-11-29',
      username: 'fang',
      git_email: 'f@x.com',
    })
    const body = JSON.parse(vi.mocked(fetch).mock.calls[0][1]?.body as string)
    expect(body).toHaveProperty('start_date', '2026-11-23')
    expect(body).toHaveProperty('end_date', '2026-11-29')
    expect(body).toHaveProperty('git_email', 'f@x.com')
  })

  it('fetchSprints 传递 all_workspaces 和 keyword', async () => {
    vi.mocked(fetch).mockResolvedValueOnce(mockResponse({ success: true, data: [] }))
    await fetchSprints('C', 'WS', true, 'ONE4')
    const body = JSON.parse(vi.mocked(fetch).mock.calls[0][1]?.body as string)
    expect(body).toMatchObject({ workspace_name: 'WS', all_workspaces: true, keyword: 'ONE4' })
  })

  it('searchRequirements 用 keyword 查询', async () => {
    vi.mocked(fetch).mockResolvedValueOnce(mockResponse({ success: true, data: [] }))
    await searchRequirements('C', 'Titan')
    const body = JSON.parse(vi.mocked(fetch).mock.calls[0][1]?.body as string)
    expect(body).toEqual({ cookie: 'C', keyword: 'Titan' })
  })

  it('非 2xx 时提取 FastAPI 422 detail 为可读文本', async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      mockResponse(
        { detail: [{ loc: ['body', 'git_email'], msg: 'Field required' }] },
        false,
        422,
      ),
    )
    await expect(fetchCurrentUser('C')).rejects.toThrow('git_email: Field required')
  })

  it('pollTaskStatus 返回顶层 log / running（非 envelope 包装）', async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      mockResponse({ running: false, log: ['✅ 完成', '🎉 结束'], success: true }),
    )
    const status = await pollTaskStatus('T1')
    expect(fetch).toHaveBeenCalledWith(`${API.taskStatus}?task_id=T1`)
    expect(status.log).toEqual(['✅ 完成', '🎉 结束'])
    expect(status.running).toBe(false)
  })

  it('envelope success=false 即使 HTTP 200 也抛出错误', async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      mockResponse({ success: false, msg: '凭证已过期', data: null }),
    )
    await expect(fetchCurrentUser('EXPIRED')).rejects.toThrow('凭证已过期')
  })

  it('detail 为字符串时直接使用', async () => {
    vi.mocked(fetch).mockResolvedValueOnce(mockResponse({ detail: '服务不可用' }, false, 500))
    await expect(submitFeedback({})).rejects.toThrow('服务不可用')
  })

  it('startTask 携带全部 snake_case 字段', async () => {
    vi.mocked(fetch).mockResolvedValueOnce(mockResponse({ success: true, data: { task_id: 'T1' } }))
    const res = await startTask({
      username: 'fang',
      cookie: 'C',
      source_object_id: 'OBJ1',
      workspace_name: 'WS',
      names: ['事项'],
      sprint_ids: ['S1'],
      times: [1.5],
      dates: ['2026-11-24'],
      requirement_ids: ['REQ1'],
      is_update: false,
    })
    const body = JSON.parse(vi.mocked(fetch).mock.calls[0][1]?.body as string)
    expect(body).toHaveProperty('source_object_id', 'OBJ1')
    expect(body).toHaveProperty('workspace_name', 'WS')
    expect(body).toHaveProperty('requirement_ids', ['REQ1'])
    expect(res.data!.task_id).toBe('T1')
  })
})
