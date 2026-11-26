import { useState } from 'react'
import { BookOpen, Code2, MessageCircle } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { APP_VERSION, REPO_URL } from '@/constants'

const HELP_ITEMS = [
  '浏览器登录 Gitee，复制 PRE-GW-SESSION Cookie 填入上方输入框。',
  '在「工时情况」日历中点击一项作为源事项（用于克隆字段模板）。',
  '在事项列表填写名称、迭代、工时、日期；可点「AI帮写」按本周 Git 提交生成草稿。',
  '点击「开始执行任务」，下方结果区会展示执行日志；完成后可跳转项目空间核对。',
  'Cookie 会本地缓存，并在服务端保活；失效后请重新粘贴。',
]

interface AppFooterProps {
  onFeedback: () => void
}

const linkClass =
  'inline-flex items-center gap-1 rounded px-1 py-0.5 text-[#1677ff] hover:bg-blue-50 hover:text-[#4096ff]'

export function AppFooter({ onFeedback }: AppFooterProps) {
  const [helpOpen, setHelpOpen] = useState(false)

  return (
    <>
      <footer className="mt-7 flex flex-wrap items-center justify-center gap-y-0.5 border-t border-[#f0f0f0] bg-gradient-to-b from-[#f8f9fa] to-transparent pt-4 text-[13px] leading-normal text-[rgba(0,0,0,0.45)]">
        <span className="font-medium text-[rgba(0,0,0,0.65)]">添加工时工具</span>
        <Sep />
        <a href={REPO_URL} target="_blank" rel="noopener noreferrer" className={linkClass}>
          <Code2 className="h-3.5 w-3.5" />源码
        </a>
        <Sep />
        <button type="button" className={linkClass} onClick={() => setHelpOpen(true)}>
          <BookOpen className="h-3.5 w-3.5" />使用说明
        </button>
        <Sep />
        <span className="rounded-full bg-[#f5f5f5] px-2 text-xs tabular-nums">{APP_VERSION}</span>
        <Sep />
        <button type="button" className={linkClass} onClick={onFeedback}>
          <MessageCircle className="h-3.5 w-3.5" />问题反馈
        </button>
      </footer>

      <Dialog open={helpOpen} onOpenChange={setHelpOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>使用说明</DialogTitle></DialogHeader>
          <ol className="list-decimal space-y-1 pl-5 text-sm leading-relaxed text-[rgba(0,0,0,0.75)]">
            {HELP_ITEMS.map((item) => <li key={item}>{item}</li>)}
          </ol>
        </DialogContent>
      </Dialog>
    </>
  )
}

function Sep() {
  return <span aria-hidden className="mx-2.5 select-none text-[#d9d9d9]">·</span>
}
