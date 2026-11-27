import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { AppHeader } from '@/components/AppHeader'
import { Section } from '@/components/Section'
import { CookiePanel } from '@/components/CookiePanel'
import { WeekCalendar, type WeekCalendarRef } from '@/components/WeekCalendar'
import { WorkItemForm } from '@/components/WorkItemForm'
import { EditItemModal, type EditPayload } from '@/components/EditItemModal'
import { FavoriteSpacesModal } from '@/components/FavoriteSpacesModal'
import { FeedbackModal } from '@/components/FeedbackModal'
import { WelcomePromoModal } from '@/components/WelcomePromoModal'
import { TaskLogPanel } from '@/components/TaskLogPanel'
import { AppFooter } from '@/components/AppFooter'
import { useAppStore } from '@/stores/useAppStore'
import {
  useCurrentUser,
  useFavorites,
  useWorkItems,
} from '@/hooks/queries'
import { fetchLlmSummary, pollTaskStatus, saveFavoriteWorkspaces, startTask } from '@/lib/api'
import { classifyLogLine, type ClassifiedLogLine } from '@/lib/logUtils'
import { formatDate, getWeekRange, isInCurrentWeek, isWeekend } from '@/lib/utils'
import { createWorkItem, type FavoriteWorkspace, type WorkItem } from '@/types'

// 从日历中挑选最新一条工时作为源事项
function pickLatestSourceItem(calendarData: Record<string, WorkItem[]>): WorkItem | null {
  const entries = Object.entries(calendarData || {})
    .filter(([, items]) => Array.isArray(items) && items.length > 0)
    .sort(([a], [b]) => b.localeCompare(a))
  if (!entries.length) return null
  return entries[0][1][entries[0][1].length - 1] || null
}

export default function App() {
  const {
    cookie, username, gitEmail, weekOffset,
    editOpen, favoriteOpen, feedbackOpen, welcomeOpen,
    setCookie, setUser, setWeekOffset, setEditOpen, setFavoriteOpen, setFeedbackOpen, setWelcomeOpen, hideWelcomePromo,
  } = useAppStore()
  const queryClient = useQueryClient()

  const [sourceItem, setSourceItem] = useState<WorkItem | null>(null)
  const [workItems, setWorkItems] = useState<WorkItem[]>(() => [createWorkItem()])
  const [taskLog, setTaskLog] = useState<ClassifiedLogLine[]>([])
  const [taskRunning, setTaskRunning] = useState(false)
  const [aiWriting, setAiWriting] = useState(false)
  const calendarRef = useRef<WeekCalendarRef>(null)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const pollGenRef = useRef(0)
  const pendingScrollRef = useRef(false)
  const autoSelectedRef = useRef('')
  const identityRef = useRef('')

  const weekRange = useMemo(() => getWeekRange(weekOffset), [weekOffset])
  const { data: currentUser, isError: userIsError, error: userQueryError } = useCurrentUser(cookie)
  const userError = userIsError
    ? (userQueryError instanceof Error ? userQueryError.message : '检查复制Cookie是否完整或已过期')
    : null

  // 同步用户信息
  useEffect(() => {
    if (currentUser?.username) {
      setUser(currentUser.username, currentUser.git_email || '')
    }
  }, [currentUser, setUser])

  const {
    data: calendarRaw, isLoading: calendarLoading, isError: calendarIsError, error: calendarQueryError,
  } = useWorkItems({
    cookie,
    start_date: formatDate(weekRange.monday),
    end_date: formatDate(weekRange.sunday),
    username: username || '',
    git_email: gitEmail || '',
  })

  const { data: favorites = [] } = useFavorites(username)
  const calendarData = (calendarRaw || {}) as Record<string, WorkItem[]>
  const calendarError = userError || (calendarIsError
    ? (calendarQueryError instanceof Error ? calendarQueryError.message : '加载工时数据失败')
    : null)

  // 账号 / Cookie 切换时清空旧账号数据，避免把旧源事项提交给新账号
  useEffect(() => {
    const identity = `${cookie}|${username}`
    if (identityRef.current === identity) return
    const hadIdentity = identityRef.current !== ''
    identityRef.current = identity
    if (!hadIdentity) return
    setSourceItem(null)
    setWorkItems([createWorkItem()])
    autoSelectedRef.current = ''
  }, [cookie, username])

  // 切周重新挂载日历后，补做排队中的滚动
  useEffect(() => {
    if (!calendarLoading && pendingScrollRef.current) {
      pendingScrollRef.current = false
      calendarRef.current?.scrollToRight()
    }
  }, [calendarLoading])

  // cookie 变化或尚未选择时，自动选最后一个工时作为源事项；切周不重选
  useEffect(() => {
    if (calendarLoading) return
    const signature = `${cookie}|${username}`
    if (autoSelectedRef.current === signature && sourceItem) return
    const picked = pickLatestSourceItem(calendarData)
    if (!picked) return
    setSourceItem(picked)
    autoSelectedRef.current = signature
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cookie, username, calendarData, calendarLoading])

  // 轮询清理：递增代次，忽略已卸载 / 已替换任务的在途请求
  useEffect(() => () => {
    pollGenRef.current += 1
    if (pollRef.current) clearInterval(pollRef.current)
  }, [])

  const beginPoll = useCallback((taskId: string, onDone: () => void) => {
    if (pollRef.current) clearInterval(pollRef.current)
    const gen = ++pollGenRef.current
    let failures = 0
    pollRef.current = setInterval(async () => {
      try {
        const status = await pollTaskStatus(taskId)
        if (gen !== pollGenRef.current) return
        failures = 0
        setTaskLog(status.log.map(classifyLogLine))
        if (!status.running) {
          if (pollRef.current) clearInterval(pollRef.current)
          pollRef.current = null
          setTaskRunning(false)
          onDone()
        }
      } catch (err) {
        if (gen !== pollGenRef.current) return
        failures += 1
        // 单次网络抖动不终止轮询，连续失败 3 次才停止
        if (failures < 3) {
          setTaskLog((prev) => [...prev, { message: `轮询暂时失败，正在重试（${failures}/3）`, type: 'error' }])
          return
        }
        if (pollRef.current) clearInterval(pollRef.current)
        pollRef.current = null
        setTaskRunning(false)
        setTaskLog((prev) => [...prev, { message: `❌ 轮询失败：${err instanceof Error ? err.message : '未知错误'}`, type: 'error' }])
      }
    }, 2000)
  }, [])

  const refreshAfterTask = useCallback((opts: { jumpCurrentWeek?: boolean; scrollWeekend?: boolean } = {}) => {
    if (opts.jumpCurrentWeek && weekOffset !== 0) {
      // 切周会改变 useWorkItems 的 queryKey，新一周数据随 key 变化自动加载一次
      setWeekOffset(0)
    } else {
      // 当前周不变：使 workItems 失效，由 React Query 重新请求一次
      queryClient.invalidateQueries({ queryKey: ['workItems'] })
    }
    if (opts.scrollWeekend) {
      pendingScrollRef.current = true
      calendarRef.current?.scrollToRight()
    }
  }, [weekOffset, setWeekOffset, queryClient])

  const handleAddItem = () => {
    setWorkItems((prev) => [...prev, createWorkItem({ workspace_name: sourceItem?.workspace_name || '' })])
  }
  const handleRemoveItem = (index: number) => {
    setWorkItems((prev) => prev.filter((_, i) => i !== index))
  }
  const handleChangeItem = (index: number, patch: Partial<WorkItem>) => {
    setWorkItems((prev) => prev.map((item, i) => (i === index ? { ...item, ...patch } : item)))
  }

  const submitCreate = useCallback(async () => {
    if (!sourceItem) { toast.warning('请从日历中选择一个源事项！'); return false }
    if (!username) { toast.warning('请先等待登录完成'); return false }
    const valid = workItems.filter((i) => i.name && i.time && i.date)
    if (!valid.length) { toast.warning('请至少填写一个完整的事项！'); return false }
    // 与表单校验保持一致：工时按一位小数取整后仍需大于 0
    if (valid.some((i) => !(parseFloat(Number(i.time).toFixed(1)) > 0))) {
      toast.warning('工时必须大于 0')
      return false
    }
    const defaultSprint = sourceItem.sprint_id || ''
    const defaultWorkspace = sourceItem.workspace_name || ''
    const workspaceNames = valid.map((i) => i.workspace_name || defaultWorkspace)
    if (workspaceNames.some((n) => !n)) { toast.warning('请为每个事项选择工作空间'); return false }
    if (valid.some((i) => !i.requirement_id)) { toast.warning('请为每个事项选择关联需求'); return false }

    setTaskRunning(true)
    setTaskLog([{ message: '📅 任务已提交，正在执行...', type: 'info' }])
    try {
      const data = await startTask({
        username: username || '', cookie,
        source_object_id: sourceItem.object_id || '',
        workspace_name: workspaceNames[0],
        workspace_names: workspaceNames,
        names: valid.map((i) => i.name),
        times: valid.map((i) => parseFloat(Number(i.time).toFixed(1))),
        dates: valid.map((i) => i.date),
        sprint_ids: valid.map((i) => {
          if (i.sprint_id) return i.sprint_id
          const ws = i.workspace_name || defaultWorkspace
          return ws === defaultWorkspace ? defaultSprint : ''
        }),
        requirement_ids: valid.map((i) => i.requirement_id || ''),
      })
      if (!data.success) throw new Error(data.msg || '任务启动失败')
      const taskId = data.data?.task_id
      if (!taskId) throw new Error('未获取到任务ID')
      beginPoll(taskId, () => refreshAfterTask({
        jumpCurrentWeek: valid.some((i) => isInCurrentWeek(i.date)),
        scrollWeekend: valid.some((i) => isWeekend(i.date)),
      }))
      return true
    } catch (err) {
      setTaskRunning(false)
      setTaskLog([{ message: `❌ 任务启动失败：${err instanceof Error ? err.message : '未知错误'}`, type: 'error' }])
      return false
    }
  }, [sourceItem, workItems, username, cookie, beginPoll, refreshAfterTask])

  const submitUpdate = useCallback(async (p: EditPayload & { item?: WorkItem }) => {
    if (!p.item || !username || !cookie) return false
    const workspace = p.workspace_name || p.item.workspace_name
    if (!workspace) { toast.warning('请选择工作空间'); return false }
    if (!p.requirement_id) { toast.warning('请选择关联需求'); return false }
    setTaskRunning(true)
    setTaskLog([{ message: '📅 更新任务已提交，正在执行...', type: 'info' }])
    try {
      const data = await startTask({
        username, cookie,
        source_object_id: p.item.object_id || '',
        workspace_name: workspace,
        is_update: true,
        names: [p.name.trim()],
        sprint_ids: [p.sprint_id || p.item.sprint_id],
        times: [parseFloat(Number(p.time).toFixed(1))],
        dates: [p.date],
        requirement_ids: [p.requirement_id],
      })
      if (!data.success) throw new Error(data.msg || '提交失败')
      const taskId = data.data?.task_id
      if (!taskId) throw new Error('未获取到任务ID')
      beginPoll(taskId, () => refreshAfterTask())
      return true
    } catch (err) {
      setTaskRunning(false)
      setTaskLog([{ message: `❌ 更新失败：${err instanceof Error ? err.message : '未知错误'}`, type: 'error' }])
      return false
    }
  }, [username, cookie, beginPoll, refreshAfterTask])

  const aiWrite = useCallback(async () => {
    if (!cookie.trim()) { toast.warning('请先填写有效的Cookie！'); return }
    if (!username) { toast.warning('请先等待日历数据加载完成！'); return }
    setAiWriting(true)
    try {
      const filledDates = new Set(Object.entries(calendarData).filter(([, items]) => items?.length).map(([d]) => d))
      const data = await fetchLlmSummary({
        git_email: gitEmail || '',
        start_date: formatDate(weekRange.monday),
        end_date: formatDate(weekRange.sunday),
        exclude_dates: Array.from(filledDates),
      })
      if (!data.success) { toast.error(data.msg || 'AI生成事项失败'); return }
      const entries = Object.entries(data.data || {})
      if (!entries.length) { toast.info(data.msg || '该日期范围内没有可用的 Git 提交记录'); return }
      setWorkItems(entries.map(([date, name]) => createWorkItem({ name, date, workspace_name: sourceItem?.workspace_name || '' })))
      toast.success(`已生成 ${entries.length} 条事项`)
    } catch (err) {
      toast.error(`AI生成失败：${err instanceof Error ? err.message : '未知错误'}`)
    } finally {
      setAiWriting(false)
    }
  }, [cookie, username, gitEmail, weekRange, calendarData, sourceItem])

  const saveFavs = useCallback(async (next: FavoriteWorkspace[]): Promise<boolean> => {
    if (!username) { toast.warning('请先等待登录完成'); return false }
    const data = await saveFavoriteWorkspaces(username, next)
    if (!data.success) { toast.error(data.msg || '保存关注空间失败'); return false }
    toast.success('关注空间已保存')
    queryClient.invalidateQueries({ queryKey: ['favorites', username] })
    setSourceItem(null)
    autoSelectedRef.current = ''
    queryClient.invalidateQueries({ queryKey: ['workItems'] })
    return true
  }, [username, queryClient])

  return (
    <div className="mx-auto max-w-[1280px] px-5 py-6">
      <WelcomePromoModal open={welcomeOpen} onOpenChange={setWelcomeOpen} onHide={hideWelcomePromo} />
      <div className="rounded-xl border border-[#f0f0f0] bg-white px-6 pb-4 pt-5 shadow-sm">
        <AppHeader />

        <div className="flex flex-col gap-4">
          <Section step={1} title="凭证" description="粘贴 Gitee PRE-GW-SESSION，用于读取与提交工时">
            <CookiePanel cookie={cookie} username={username} onChange={setCookie} />
          </Section>

          <Section
            step={2}
            title={`${weekRange.weekLabel}工时情况`}
            description={
              <>
                点击一项作为源事项（用于克隆字段模板）
                <button type="button" className="ml-3 border-b border-dashed border-brand-500 font-medium text-brand-600 hover:text-brand-500" onClick={() => setFavoriteOpen(true)}>
                  ★ 关注空间 · {favorites.length}
                </button>
              </>
            }
            action={
              <div className="flex items-center gap-2">
                <Button size="icon" className="h-6 w-6 rounded bg-[#3498db] p-0 hover:bg-[#2980b9] disabled:bg-[rgba(0,0,0,0.04)] disabled:text-[rgba(0,0,0,0.25)] disabled:opacity-100" disabled={weekOffset <= -4} onClick={() => setWeekOffset(weekOffset - 1)} aria-label="上一周"><ChevronLeft className="h-3.5 w-3.5" /></Button>
                <Button size="icon" className="h-6 w-6 rounded bg-[#3498db] p-0 hover:bg-[#2980b9] disabled:bg-[rgba(0,0,0,0.04)] disabled:text-[rgba(0,0,0,0.25)] disabled:opacity-100" disabled={weekOffset >= 0} onClick={() => setWeekOffset(weekOffset + 1)} aria-label="下一周"><ChevronRight className="h-3.5 w-3.5" /></Button>
              </div>
            }
          >
            <WeekCalendar
              ref={calendarRef}
              calendarData={calendarData}
              monday={weekRange.monday}
              sourceItem={sourceItem}
              onSelect={setSourceItem}
              onEdit={(item) => { setSourceItem(item); setEditOpen(true) }}
              loading={calendarLoading}
              error={calendarError}
              favorites={favorites as FavoriteWorkspace[]}
              onOpenFavorites={() => setFavoriteOpen(true)}
            />
          </Section>

          <Section step={3} title="填写事项" description="填写名称、工作空间、迭代、关联需求、工时与日期，可使用 AI 帮写草稿">
            <WorkItemForm
              workItems={workItems}
              sourceItem={sourceItem}
              cookie={cookie}
              username={username}
              favorites={favorites as FavoriteWorkspace[]}
              taskRunning={taskRunning}
              aiWriting={aiWriting}
              onAdd={handleAddItem}
              onRemove={handleRemoveItem}
              onChange={handleChangeItem}
              onAiWrite={aiWrite}
              onSubmit={submitCreate}
            />
          </Section>

          <Section step={4} title="执行结果" description="任务日志与跳转链接会显示在这里">
            <TaskLogPanel taskLog={taskLog} />
          </Section>

          <AppFooter onFeedback={() => setFeedbackOpen(true)} />
        </div>

        <EditItemModal
          open={editOpen}
          item={sourceItem}
          cookie={cookie}
          username={username}
          onClose={() => setEditOpen(false)}
          onSubmit={(p) => submitUpdate({ ...p, item: sourceItem || undefined } as EditPayload & { item?: WorkItem })}
        />
        <FavoriteSpacesModal
          open={favoriteOpen}
          cookie={cookie}
          favorites={favorites as FavoriteWorkspace[]}
          onClose={() => setFavoriteOpen(false)}
          onSave={saveFavs}
        />
        <FeedbackModal open={feedbackOpen} onOpenChange={setFeedbackOpen} username={username} />
      </div>
    </div>
  )
}
