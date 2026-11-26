import { useCallback, useEffect, useRef, useState } from 'react'
import { ChevronsUpDown, Loader2, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from '@/components/ui/command'
import { useRequirements } from '@/hooks/queries'
import { forgetSearch, loadRecentSearches, rememberSearch } from '@/lib/recentSearches'
import { cn } from '@/lib/utils'
import type { Requirement } from '@/types'

interface RequirementSelectProps {
  value: string
  onChange: (id: string, name: string) => void
  cookie: string
  username?: string | null
  initialLabel?: string
  placeholder?: string
  disabled?: boolean
  size?: 'default' | 'large'
}

export function RequirementSelect({ value, onChange, cookie, username, initialLabel, placeholder = '请选择关联需求', disabled, size = 'default' }: RequirementSelectProps) {
  const [open, setOpen] = useState(false)
  const [keyword, setKeyword] = useState('')
  const [active, setActive] = useState('')
  const [recent, setRecent] = useState(() => loadRecentSearches(username))
  const inputRef = useRef<HTMLInputElement>(null)

  const timer = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => { setRecent(loadRecentSearches(username)) }, [username])

  const { data: requirements = [], isFetching } = useRequirements(cookie, active, open)

  // 搜索动作：记录历史由调用方决定，防抖输入不记录
  const runSearch = useCallback((text: string, remember: boolean) => {
    const clean = text.trim()
    setActive(clean)
    if (remember && clean) setRecent(rememberSearch(username, clean))
  }, [username])

  // 输入防抖 300ms 自动搜索，仅更新列表，不写入历史
  useEffect(() => {
    if (timer.current) clearTimeout(timer.current)
    timer.current = setTimeout(() => runSearch(keyword, false), 300)
    return () => { if (timer.current) clearTimeout(timer.current) }
  }, [keyword, runSearch])

  // 回车：立即搜索并记录历史；捕获阶段拦截避免选中高亮项
  useEffect(() => {
    const el = inputRef.current
    if (!el) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== 'Enter') return
      e.preventDefault()
      e.stopPropagation()
      if (timer.current) clearTimeout(timer.current)
      runSearch(keyword, true)
    }
    el.addEventListener('keydown', onKey, true)
    return () => el.removeEventListener('keydown', onKey, true)
  }, [keyword, runSearch, open])

  const label = value && initialLabel ? initialLabel : requirements.find((r) => r.id === value)?.name || value

  const options: Requirement[] = [...requirements]
  if (value && !options.some((r) => r.id === value)) {
    options.unshift({ id: value, key: '', name: initialLabel || value })
  }

  return (
    <Popover open={open} onOpenChange={(v) => {
      setOpen(v)
      if (!v) { setKeyword(''); setActive('') }
    }}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          disabled={disabled}
          className={cn('w-full justify-between font-normal', size === 'large' && 'h-11', !value && 'text-muted-foreground')}
        >
          <span className="truncate">{label || placeholder}</span>
          {isFetching ? <Loader2 className="ml-2 h-4 w-4 animate-spin opacity-50" /> : <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[var(--radix-popover-trigger-width)] p-0">
        <Command shouldFilter={false}>
          <CommandInput
            ref={inputRef}
            placeholder="输入关键字后回车搜索…"
            value={keyword}
            onValueChange={setKeyword}
          />
          {recent.length > 0 && (
            <div className="flex items-center gap-1.5 overflow-hidden whitespace-nowrap border-b px-3 py-2">
              <span className="shrink-0 text-xs text-muted-foreground">最近</span>
              {recent.map((text) => (
                <span key={text} className="inline-flex shrink-0 items-center gap-1 rounded bg-muted px-1.5 py-0.5 text-xs">
                  <button
                    type="button"
                    className="max-w-16 truncate"
                    title={text}
                    onMouseDown={(e) => e.preventDefault()}
                    onClick={() => { setKeyword(text); runSearch(text, true) }}
                  >
                    {text}
                  </button>
                  <button
                    type="button"
                    aria-label="删除"
                    onMouseDown={(e) => e.preventDefault()}
                    onClick={() => setRecent(forgetSearch(username, text))}
                    className="text-muted-foreground hover:text-foreground"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </span>
              ))}
            </div>
          )}
          <CommandList>
            <CommandEmpty>未找到需求</CommandEmpty>
            <CommandGroup>
              {options.map((r) => (
                <CommandItem
                  key={r.id}
                  value={r.id}
                  title={r.key ? `${r.key}  ${r.name}` : r.name}
                  onSelect={() => { onChange(r.id === value ? '' : r.id, r.name); setOpen(false) }}
                  className={cn(value === r.id && 'bg-brand-50 text-brand-700')}
                >
                  <span className="truncate">{r.key ? `${r.key}  ${r.name}` : r.name}</span>
                </CommandItem>
              ))}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  )
}
