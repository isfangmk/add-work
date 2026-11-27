import { useEffect, useId, useRef, useState } from 'react'
import { ChevronsUpDown, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { Label } from '@/components/ui/label'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from '@/components/ui/command'
import { useSprints } from '@/hooks/queries'
import { cn } from '@/lib/utils'
import type { Sprint } from '@/types'

interface SprintSelectProps {
  value: string
  onChange: (value: string, name?: string) => void
  cookie: string
  workspaceName: string
  preferredSprint?: string
  initialLabel?: string
  disabled?: boolean
  size?: 'default' | 'large'
}

export function SprintSelect({ value, onChange, cookie, workspaceName, preferredSprint, initialLabel, disabled, size = 'default' }: SprintSelectProps) {
  const [open, setOpen] = useState(false)
  const [onlyCurrent, setOnlyCurrent] = useState(true)
  const [keyword, setKeyword] = useState('')
  const [debounced, setDebounced] = useState('')
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const checkboxId = useId()

  useEffect(() => {
    if (timer.current) clearTimeout(timer.current)
    timer.current = setTimeout(() => setDebounced(keyword.trim()), 300)
    return () => { if (timer.current) clearTimeout(timer.current) }
  }, [keyword])

  const { data: sprints = [], isFetching } = useSprints(cookie, workspaceName, !onlyCurrent, debounced, open)

  const list = [...sprints].sort((a, b) => {
    if (onlyCurrent && preferredSprint) {
      if (a.object_id === preferredSprint) return -1
      if (b.object_id === preferredSprint) return 1
    }
    return 0
  })

  const label = (value && initialLabel) || list.find((s) => s.object_id === value)?.name || value

  return (
    <Popover open={open} onOpenChange={(v) => {
      setOpen(v)
      if (!v) setKeyword('')
    }}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          disabled={disabled || (!workspaceName && onlyCurrent)}
          className={cn('flex w-full min-w-0 justify-between font-normal', size === 'large' && 'h-11', !value && 'text-muted-foreground')}
        >
          <span className="truncate">{label || (workspaceName || !onlyCurrent ? '请选择迭代' : '请先选择工作空间')}</span>
          {isFetching ? <Loader2 className="ml-2 h-4 w-4 animate-spin opacity-50" /> : <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="min-w-[190px] w-[var(--radix-popover-trigger-width)] p-0">
        <Command shouldFilter={onlyCurrent}>
          <CommandInput
            placeholder={onlyCurrent ? '搜索迭代…' : '输入关键字搜索全部迭代…'}
            value={keyword}
            onValueChange={setKeyword}
          />
          <div className="flex items-center gap-2 whitespace-nowrap border-b px-3 py-2">
            <Checkbox
              id={checkboxId}
              checked={onlyCurrent}
              onCheckedChange={(v) => {
                setOnlyCurrent(v === true)
                setKeyword('')
                if (timer.current) clearTimeout(timer.current)
                setDebounced('')
              }}
            />
            <Label htmlFor={checkboxId} className="cursor-pointer whitespace-nowrap text-xs">只显示当前空间的迭代</Label>
          </div>
          <CommandList>
            <CommandEmpty>未找到迭代</CommandEmpty>
            <CommandGroup>
              {list.map((s: Sprint) => (
                <CommandItem
                  key={s.object_id}
                  value={s.name}
                  title={s.name}
                  onSelect={() => {
                    const next = s.object_id === value ? '' : s.object_id
                    onChange(next, next ? s.name : '')
                    setOpen(false)
                  }}
                  className={cn(value === s.object_id && 'bg-brand-50 text-brand-700')}
                >
                  <span className="flex-1 truncate">{s.name}</span>
                  {!onlyCurrent && s.workspace_name && (
                    <span className="ml-2 text-xs text-muted-foreground">{s.workspace_name}</span>
                  )}
                </CommandItem>
              ))}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  )
}
