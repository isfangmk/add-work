import { useEffect, useState } from 'react'
import { toast } from 'sonner'
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { submitFeedback } from '@/lib/api'

interface FeedbackModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  username: string | null
}

const MAX_CONTENT = 2000

export function FeedbackModal({ open, onOpenChange, username }: FeedbackModalProps) {
  const [contact, setContact] = useState('')
  const [content, setContent] = useState('')
  const [sending, setSending] = useState(false)

  useEffect(() => {
    if (open) { setContact(''); setContent('') }
  }, [open])

  const handleSend = async () => {
    const clean = content.trim()
    if (!clean) { toast.error('请填写反馈内容'); return }
    if (Array.from(clean).length < 5) { toast.error('请至少填写 5 个字'); return }
    setSending(true)
    try {
      const data = await submitFeedback({
        content: clean,
        username: (username || '').trim() || undefined,
        contact: contact.trim() || undefined,
      })
      if (!data.success) { toast.error(data.msg || '提交失败'); return }
      toast.success(data.msg || '反馈已提交')
      onOpenChange(false)
    } catch (err) {
      toast.error(err instanceof Error ? err.message : '提交失败')
    } finally {
      setSending(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader><DialogTitle>问题反馈</DialogTitle></DialogHeader>
        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="feedback-contact">联系方式</Label>
            <Input
              id="feedback-contact"
              value={contact}
              onChange={(e) => setContact(e.target.value)}
              placeholder="可选，企业微信 / 邮箱 / 手机号"
              maxLength={200}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="feedback-content"><span className="mr-1 text-danger">*</span>反馈内容</Label>
            <Textarea
              id="feedback-content"
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="描述遇到的问题、期望的功能或改进建议"
              maxLength={MAX_CONTENT}
              rows={5}
            />
            <div className="text-right text-xs text-muted-foreground">{content.length} / {MAX_CONTENT}</div>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>取消</Button>
          <Button loading={sending} onClick={handleSend}>提交</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
