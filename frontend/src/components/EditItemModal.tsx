import { useEffect, useState } from 'react'
import { toast } from 'sonner'
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { WorkspaceSelect } from '@/components/WorkspaceSelect'
import { SprintSelect } from '@/components/SprintSelect'
import { RequirementSelect } from '@/components/RequirementSelect'
import { useFavorites } from '@/hooks/queries'
import type { FavoriteWorkspace, WorkItem } from '@/types'

interface EditItemModalProps {
  open: boolean
  item: WorkItem | null
  cookie: string
  username: string | null
  onClose: () => void
  onSubmit: (payload: EditPayload) => Promise<boolean>
}

export interface EditPayload {
  name: string
  workspace_name: string
  sprint_id: string
  requirement_id: string
  time: number
  date: string
}

export function EditItemModal({ open, item, cookie, username, onClose, onSubmit }: EditItemModalProps) {
  const [name, setName] = useState('')
  const [workspace, setWorkspace] = useState('')
  const [sprintId, setSprintId] = useState('')
  const [sprintName, setSprintName] = useState('')
  const [requirementId, setRequirementId] = useState('')
  const [requirementName, setRequirementName] = useState('')
  const [time, setTime] = useState('')
  const [date, setDate] = useState('')
  const [saving, setSaving] = useState(false)

  const { data: favorites = [] } = useFavorites(username)

  useEffect(() => {
    if (!open || !item) return
    setName(item.name || '')
    setWorkspace(item.workspace_name || '')
    setSprintId(item.sprint_id || '')
    setSprintName(item.sprint || '')
    setRequirementId(item.requirement_id || '')
    setRequirementName(item.requirement_name || '')
    setTime(String(item.time ?? ''))
    setDate(item.date || '')
  }, [open, item])

  const handleSubmit = async () => {
    if (!name.trim() || !requirementId || !workspace) {
      toast.warning('请填写名称、工作空间并关联需求')
      return
    }
    const t = Number(time)
    if (!Number.isFinite(t) || t <= 0) {
      toast.warning('工时必须大于 0')
      return
    }
    if (!date) { toast.warning('请选择日期'); return }
    setSaving(true)
    try {
      const ok = await onSubmit({ name: name.trim(), workspace_name: workspace, sprint_id: sprintId, requirement_id: requirementId, time: t, date })
      if (ok) onClose()
    } finally {
      setSaving(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>更新事项</DialogTitle>
        </DialogHeader>
        <div className="space-y-3">
          <div className="space-y-1"><Label>事项名称</Label><Input value={name} onChange={(e) => setName(e.target.value)} onFocus={(e) => { const el = e.currentTarget; requestAnimationFrame(() => { if (document.activeElement === el) el.setSelectionRange(el.value.length, el.value.length) }) }} /></div>
          <div className="space-y-1">
            <Label>工作空间</Label>
            <WorkspaceSelect value={workspace} cookie={cookie} favorites={favorites as FavoriteWorkspace[]} onChange={(v) => { setWorkspace(v); setSprintId(''); setSprintName('') }} />
          </div>
          <div className="space-y-1">
            <Label>迭代</Label>
            <SprintSelect value={sprintId} cookie={cookie} workspaceName={workspace} preferredSprint={item?.sprint_id} initialLabel={sprintName} onChange={(v, name) => { setSprintId(v); setSprintName(name || '') }} />
          </div>
          <div className="space-y-1">
            <Label>关联需求</Label>
            <RequirementSelect value={requirementId} cookie={cookie} username={username} initialLabel={requirementName} onChange={(id, n) => { setRequirementId(id); setRequirementName(n) }} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1"><Label>工时（小时）</Label><Input type="number" min={0.1} step={0.1} value={time} onChange={(e) => setTime(e.target.value)} /></div>
            <div className="space-y-1"><Label>日期</Label><Input type="date" value={date} onChange={(e) => setDate(e.target.value)} /></div>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>取消</Button>
          <Button loading={saving} onClick={handleSubmit}>提交修改</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
