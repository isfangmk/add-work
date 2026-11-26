import { useEffect, useRef, useState } from 'react'
import { CheckCircle2, ChevronDown, ChevronUp, KeyRound, TriangleAlert } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface CookiePanelProps {
  cookie: string
  username: string | null
  onChange: (value: string) => void
}

export function CookiePanel({ cookie, username, onChange }: CookiePanelProps) {
  const filled = Boolean(cookie?.trim())
  const [expanded, setExpanded] = useState(!filled)
  const focusedRef = useRef(false)
  const prevFilledRef = useRef(filled)

  // 仅在外部替换凭证（清空 / 填入）时同步展开状态，编辑中保持展开
  useEffect(() => {
    if (focusedRef.current) return
    if (prevFilledRef.current !== filled) setExpanded(!filled)
    prevFilledRef.current = filled
  }, [filled])

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex min-w-0 flex-wrap items-center gap-2">
          <KeyRound className="h-4 w-4 text-[rgba(0,0,0,0.45)]" />
          {filled ? (
            <span className="inline-flex h-[22px] items-center gap-1 rounded px-2 text-xs font-medium text-brand-500" style={{ backgroundColor: '#dfede2' }}>
              <CheckCircle2 className="h-3.5 w-3.5" />Cookie 已填写
            </span>
          ) : (
            <span className="inline-flex h-[22px] items-center gap-1 rounded bg-[#fffbe6] px-2 text-xs font-medium text-[#faaa14]">
              <TriangleAlert className="h-3.5 w-3.5" />Cookie 未填写
            </span>
          )}
          {username && <span className="text-[13px] text-[rgba(0,0,0,0.65)]">当前用户：{username}</span>}
        </div>
        <Button
          type="button"
          variant="link"
          size="sm"
          className="h-6 px-0 text-[#1677ff] hover:text-[#4096ff]"
          onClick={() => setExpanded((v) => !v)}
        >
          {expanded ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
          {expanded ? '收起' : '展开编辑'}
        </Button>
      </div>
      {expanded && (
        <div className="mt-3">
          <textarea
            value={cookie}
            onChange={(e) => onChange(e.target.value)}
            onFocus={() => { focusedRef.current = true }}
            onBlur={() => { focusedRef.current = false }}
            placeholder="请粘贴 Gitee 的 PRE-GW-SESSION Cookie 值"
            rows={3}
            className="flex w-full rounded-md border border-[#d9d9d9] bg-white px-3 py-2 text-sm text-[rgba(0,0,0,0.88)] outline-none transition-colors placeholder:text-[rgba(0,0,0,0.25)] focus:border-brand-500 focus:ring-1 focus:ring-[#d9d9d9]"
          />
          <p className="mt-2 text-xs text-[rgba(0,0,0,0.45)]">
            获取方式：浏览器登录 https://gitee.ibr.net.cn → F12 → 存储 → Cookie → 找到 PRE-GW-SESSION → 复制值
          </p>
        </div>
      )}
    </div>
  )
}
