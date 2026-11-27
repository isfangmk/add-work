import { Minus, Plus, Sparkles } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { WorkspaceSelect } from '@/components/WorkspaceSelect'
import { SprintSelect } from '@/components/SprintSelect'
import { RequirementSelect } from '@/components/RequirementSelect'
import { cn } from '@/lib/utils'
import type { FavoriteWorkspace, WorkItem } from '@/types'

interface WorkItemFormProps {
  workItems: WorkItem[]
  sourceItem: WorkItem | null
  cookie: string
  username: string | null
  favorites: FavoriteWorkspace[]
  taskRunning: boolean
  aiWriting: boolean
  onAdd: () => void
  onRemove: (index: number) => void
  onChange: (index: number, patch: Partial<WorkItem>) => void
  onAiWrite: () => void
  onSubmit: () => void
}

export function WorkItemForm({
  workItems, sourceItem, cookie, username, favorites, taskRunning, aiWriting,
  onAdd, onRemove, onChange, onAiWrite, onSubmit,
}: WorkItemFormProps) {
  const defaultWorkspace = sourceItem?.workspace_name || ''
  const preferredSprint = sourceItem?.sprint_id || ''

  const handleSubmit = () => {
    const invalid = workItems.some((item) => {
      const t = parseFloat(Number(item.time).toFixed(1))
      return !item.time || !Number.isFinite(t) || t <= 0 || !item.name.trim() || !item.requirement_id || !item.date
    })
    if (invalid) {
      toast.warning('请完整填写事项名称、关联需求、日期，且工时必须大于 0')
      return
    }
    onSubmit()
  }

  return (
    <div className="space-y-4">
      {workItems.map((item, index) => {
        const workspace = item.workspace_name || defaultWorkspace || ''
        return (
          <div key={item.id || index} className="grid grid-cols-1 gap-2 rounded-lg border bg-muted/20 p-3 md:grid-cols-[1.2fr_1fr_1fr_1.4fr_0.5fr_1fr_auto] md:items-center">
            <div className="min-w-0 space-y-1">
              <Label className="whitespace-nowrap text-[11px] text-muted-foreground">事项名称</Label>
              <Input
                className="h-11"
                value={item.name}
                onChange={(e) => onChange(index, { name: e.target.value })}
                placeholder="事项名称"
              />
            </div>
            <div className="min-w-0 space-y-1">
              <Label className="whitespace-nowrap text-[11px] text-muted-foreground">工作空间</Label>
              <WorkspaceSelect
                size="large"
                value={workspace}
                cookie={cookie}
                favorites={favorites}
                onChange={(v) => onChange(index, { workspace_name: v, sprint_id: '' })}
              />
            </div>
            <div className="min-w-0 space-y-1">
              <Label className="whitespace-nowrap text-[11px] text-muted-foreground">迭代</Label>
              <SprintSelect
                size="large"
                value={item.sprint_id}
                cookie={cookie}
                workspaceName={workspace}
                initialLabel={item.sprint}
                preferredSprint={workspace === defaultWorkspace ? preferredSprint : ''}
                disabled={!workspace}
                onChange={(v, name) => onChange(index, { sprint_id: v, sprint: name || '' })}
              />
            </div>
            <div className="min-w-0 space-y-1">
              <Label className="whitespace-nowrap text-[11px] text-muted-foreground">关联需求</Label>
              <RequirementSelect
                size="large"
                value={item.requirement_id}
                cookie={cookie}
                username={username}
                initialLabel={item.requirement_name ? `${item.requirement_key ? item.requirement_key + '  ' : ''}${item.requirement_name}` : undefined}
                onChange={(id, name) => onChange(index, { requirement_id: id, requirement_name: name })}
              />
            </div>
            <div className="min-w-0 space-y-1">
              <Label className="whitespace-nowrap text-[11px] text-muted-foreground">工时</Label>
              <Input
                className="h-11"
                type="number"
                min={0.1}
                step={0.1}
                value={item.time}
                onChange={(e) => onChange(index, { time: e.target.value })}
                placeholder="工时"
              />
            </div>
            <div className="min-w-0 space-y-1">
              <Label className="whitespace-nowrap text-[11px] text-muted-foreground">日期</Label>
              <Input
                className="h-11"
                type="date"
                value={item.date}
                onChange={(e) => onChange(index, { date: e.target.value })}
              />
            </div>
            <Button
              variant="destructive"
              size="icon"
              className="mt-5 h-11 w-11"
              onClick={() => onRemove(index)}
              disabled={workItems.length <= 1}
              aria-label="删除事项"
            >
              <Minus className="h-4 w-4" />
            </Button>
          </div>
        )
      })}
      <div className="flex flex-wrap gap-2">
        <Button className="h-10 flex-1 bg-brand-500 hover:bg-brand-600" onClick={onAdd}><Plus className="h-4 w-4" />添加事项</Button>
        <Button
          className="h-10 flex-1 bg-brand-500 hover:bg-brand-600 disabled:bg-brand-200 disabled:opacity-70"
          loading={aiWriting}
          disabled={!cookie.trim() || !username}
          onClick={onAiWrite}
        >
          <Sparkles className="h-4 w-4" />AI帮写
        </Button>
      </div>
      <p className={cn('text-xs text-muted-foreground')}>
        每个事项包含名称、工作空间、迭代、关联需求、工时和日期；基于 Git 提交 AI 帮写将自动填充当前周未填写的事项内容
      </p>
      <div className="flex justify-end border-t border-dashed border-[#e5e5e5] pt-3.5">
        <Button size="lg" className="min-w-[200px] bg-ink-900 hover:bg-ink-800 disabled:bg-slate-400" loading={taskRunning} disabled={!sourceItem || taskRunning} onClick={handleSubmit}>
          {taskRunning ? '任务执行中...' : sourceItem ? '开始执行任务' : '请先选择源事项'}
        </Button>
      </div>
    </div>
  )
}
