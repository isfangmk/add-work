import { useState } from 'react'
import { ChevronsUpDown, Star } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from '@/components/ui/command'
import { useWorkspaces } from '@/hooks/queries'
import { cn } from '@/lib/utils'
import type { Workspace } from '@/types'

interface WorkspaceSelectProps {
  value: string
  onChange: (value: string) => void
  cookie: string
  favorites: { workspace_name: string }[]
  disabled?: boolean
  size?: 'default' | 'large'
}

export function WorkspaceSelect({ value, onChange, cookie, favorites, disabled, size = 'default' }: WorkspaceSelectProps) {
  const [open, setOpen] = useState(false)
  const { data: workspaces = [] } = useWorkspaces(cookie, open)
  const favNames = new Set(favorites.map((f) => f.workspace_name))
  const ordered = [...workspaces].sort((a, b) => {
    const af = favNames.has(a.workspace_name) ? 1 : 0
    const bf = favNames.has(b.workspace_name) ? 1 : 0
    return bf - af
  })

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          disabled={disabled}
          className={cn('w-full justify-between font-normal', size === 'large' && 'h-11', !value && 'text-muted-foreground')}
        >
          <span className="flex items-center gap-1 truncate">
            {favNames.has(value) && <Star className="h-3.5 w-3.5 fill-amber-400 text-amber-400" />}
            {value || '工作空间'}
          </span>
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[var(--radix-popover-trigger-width)] p-0">
        <Command>
          <CommandInput placeholder="搜索工作空间…" />
          <CommandList>
            <CommandEmpty>未找到工作空间</CommandEmpty>
            <CommandGroup>
              {ordered.map((ws: Workspace) => (
                <CommandItem
                  key={ws.workspace_name}
                  value={ws.workspace_name}
                  title={ws.workspace_name}
                  onSelect={() => { onChange(ws.workspace_name); setOpen(false) }}
                  className={cn(value === ws.workspace_name && 'bg-brand-50 text-brand-700')}
                >
                  {favNames.has(ws.workspace_name) && <Star className="mr-1 h-3.5 w-3.5 fill-amber-400 text-amber-400" />}
                  <span className="truncate">{ws.workspace_name}</span>
                </CommandItem>
              ))}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  )
}
