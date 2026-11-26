import { useEffect, useRef, useState } from 'react'
import { Check, CheckCircle2, Copy, Share2, Zap } from 'lucide-react'
import { toast } from 'sonner'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { REPO_URL, SHARE_URL } from '@/constants'

interface WelcomePromoModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onHide: () => void
}

const HIGHLIGHTS = [
  { icon: Zap, text: '一次填写一周的工时' },
  { icon: CheckCircle2, text: 'AI 帮写按 Git 提交生成工时草稿' },
  { icon: Share2, text: '转发给同事，一起少花时间在填报上' },
]

const SHARE_TEXT = '推荐一个添加工时工具：周历选源事项一键克隆，还支持 AI 帮写，省去重复填报。'

export function WelcomePromoModal({ open, onOpenChange, onHide }: WelcomePromoModalProps) {
  const [copied, setCopied] = useState(false)
  const copyTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => () => { if (copyTimer.current) clearTimeout(copyTimer.current) }, [])

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(`${SHARE_TEXT}\n${SHARE_URL}\n源码：${REPO_URL}`)
      toast.success('分享文案已复制，可直接发给同事')
      setCopied(true)
      if (copyTimer.current) clearTimeout(copyTimer.current)
      copyTimer.current = setTimeout(() => setCopied(false), 2000)
    } catch {
      toast.error('复制失败，请手动分享页面链接')
    }
  }

  const close = () => onOpenChange(false)
  // “不再显示”才持久化隐藏标记；确定 / 关闭 / ESC 仅本次关闭
  const dontShow = () => onHide()

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) close() }}>
      <DialogContent className="max-w-[440px] gap-0 overflow-hidden p-0">
        <DialogHeader className="sr-only">
          <DialogTitle>欢迎使用添加工时工具</DialogTitle>
          <DialogDescription>介绍工具能力并提供复制分享文案与不再显示的选项</DialogDescription>
        </DialogHeader>
        <div className="px-6 pb-5 pt-6">
          <div className="mb-4">
            <span className="mb-2 inline-flex items-center rounded-full bg-brand-50 px-2 py-0.5 text-xs leading-[18px] text-brand-600">欢迎使用</span>
            <h2 className="m-0 text-[22px] font-semibold leading-tight text-[rgba(0,0,0,0.88)]">添加工时工具</h2>
            <p className="mt-2 text-sm leading-relaxed text-[rgba(0,0,0,0.55)]">写给需要经常填报工时的同学。用得顺手的话，欢迎转给同事一起用。</p>
          </div>
          <ul className="mb-[18px] space-y-2.5 rounded-[10px] border border-[#f0f0f0] bg-[#f8f9fa] px-3.5 py-3">
            {HIGHLIGHTS.map(({ icon: Icon, text }) => (
              <li key={text} className="flex items-start gap-2.5 text-[13px] leading-relaxed text-[rgba(0,0,0,0.75)]">
                <span className="inline-flex h-[22px] w-[22px] shrink-0 items-center justify-center rounded-md border border-[#e8f5ee] bg-white text-brand-500">
                  <Icon className="h-3.5 w-3.5" />
                </span>
                {text}
              </li>
            ))}
          </ul>
          <div className="flex flex-col gap-3">
            <Button variant="outline" className="w-full" onClick={copy}>
              {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}复制分享文案
            </Button>
            <div className="flex items-center justify-between gap-3">
              <Button variant="ghost" onClick={dontShow}>不再显示</Button>
              <Button className="min-w-[96px] bg-brand-500 hover:bg-brand-600" onClick={close}>确 定</Button>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
