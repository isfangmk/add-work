import { useEffect, useRef } from 'react'
import type { ClassifiedLogLine } from '@/lib/logUtils'

interface TaskLogPanelProps {
  taskLog: ClassifiedLogLine[]
}

// 日志配色：success 绿、error 红、其余默认色；不渲染图标
const COLOR: Record<ClassifiedLogLine['type'], string> = {
  success: 'text-[#52c41a]',
  error: 'text-[#ff4d4f]',
  info: '',
  default: '',
}

function renderMessage(message: string) {
  const parts = String(message).split(/(https?:\/\/[^\s]+)/g)
  return parts.map((part, i) =>
    /^https?:\/\//.test(part) ? (
      <a key={i} href={part} target="_blank" rel="noopener noreferrer" className="text-[#1677ff] hover:underline">{part}</a>
    ) : (
      <span key={i}>{part}</span>
    ),
  )
}

export function TaskLogPanel({ taskLog }: TaskLogPanelProps) {
  const ref = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (ref.current) ref.current.scrollTop = ref.current.scrollHeight
  }, [taskLog])

  const empty = taskLog.length === 0
  return (
    <div
      ref={ref}
      className={
        empty
          ? 'flex min-h-[72px] items-center rounded-lg border border-[#f0f0f0] bg-white px-3.5 py-3'
          : 'h-[280px] overflow-y-auto rounded-lg border border-[#f0f0f0] bg-white px-3.5 py-3'
      }
    >
      {empty ? (
        <span className="w-full text-center text-sm text-[rgba(0,0,0,0.45)]">选择源事项并填写表单后，点击「开始执行任务」，结果将显示在此处</span>
      ) : (
        <div>
          {taskLog.map((line, i) => (
            <div
              key={i}
              className={`mb-1 whitespace-pre-wrap text-sm ${COLOR[line.type]}`}
            >
              {renderMessage(line.message)}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
