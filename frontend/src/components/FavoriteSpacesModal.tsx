import { useEffect, useState } from 'react'
import { Check, Star } from 'lucide-react'
import { toast } from 'sonner'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { useWorkspaces } from '@/hooks/queries'
import type { FavoriteWorkspace, Workspace } from '@/types'

interface FavoriteSpacesModalProps {
  open: boolean
  cookie: string
  favorites: FavoriteWorkspace[]
  onClose: () => void
  onSave: (next: FavoriteWorkspace[]) => Promise<boolean>
}

export function FavoriteSpacesModal({ open, cookie, favorites, onClose, onSave }: FavoriteSpacesModalProps) {
  const { data: workspaces = [] } = useWorkspaces(cookie, open)
  const [selected, setSelected] = useState<Set<string>>(() => new Set(favorites.map((f) => f.workspace_name)))
  const [keyword, setKeyword] = useState('')
  const [saving, setSaving] = useState(false)

  // 打开时以最新收藏初始化选中态，避免异步加载完成后仍显示旧的空选中
  useEffect(() => {
    if (!open) return
    setSelected(new Set(favorites.map((f) => f.workspace_name)))
    setKeyword('')
  }, [open, favorites])

  const toggle = (name: string) => {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(name)) next.delete(name)
      else next.add(name)
      return next
    })
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      const next = workspaces
        .filter((w) => selected.has(w.workspace_name))
        .map((w) => ({ workspace_name: w.workspace_name, workspace_key: w.workspace_key, workspace_id: w.workspace_id }))
      const ok = await onSave(next)
      if (ok) onClose()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : '保存关注空间失败')
    } finally {
      setSaving(false)
    }
  }

  const filtered = (workspaces as Workspace[]).filter((w) => w.workspace_name.toLowerCase().includes(keyword.toLowerCase()))

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>关注空间</DialogTitle>
          <DialogDescription>选择需要读取工时的空间，日历只展示这些空间的数据</DialogDescription>
        </DialogHeader>
        <div className="space-y-3">
          <div className="flex flex-wrap gap-1.5">
            {favorites.length === 0 && <span className="text-sm text-muted-foreground">还没有关注的空间</span>}
            {favorites.map((f) => (
              <Badge key={f.workspace_name} variant="secondary" className="gap-1">
                <Star className="h-3 w-3 fill-amber-400 text-amber-400" />{f.workspace_name}
              </Badge>
            ))}
          </div>
          <Input value={keyword} onChange={(e) => setKeyword(e.target.value)} placeholder="搜索空间…" />
          <div className="max-h-64 space-y-1 overflow-y-auto rounded-lg border p-2">
            {filtered.map((w) => {
              const active = selected.has(w.workspace_name)
              return (
                <button
                  key={w.workspace_name}
                  type="button"
                  onClick={() => toggle(w.workspace_name)}
                  className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-sm hover:bg-accent"
                >
                  <span className={`flex h-4 w-4 items-center justify-center rounded border ${active ? 'border-brand-500 bg-brand-500 text-white' : ''}`}>
                    {active && <Check className="h-3 w-3" />}
                  </span>
                  {w.workspace_name}
                </button>
              )
            })}
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>取消</Button>
          <Button loading={saving} onClick={handleSave}>保存（{selected.size}）</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
