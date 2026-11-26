export type LogLineType = 'success' | 'error' | 'info' | 'default'

export interface ClassifiedLogLine {
  message: string
  type: LogLineType
}

export function classifyLogLine(line: string): ClassifiedLogLine {
  const text = line.trimStart()
  if (text.startsWith('✅')) return { message: line, type: 'success' }
  if (text.startsWith('❌')) return { message: line, type: 'error' }
  if (text.startsWith('📅') || text.startsWith('📋') || text.startsWith('⭐') || text.startsWith('😎') || text.startsWith('===') || text.startsWith('🎉')) {
    return { message: line, type: 'info' }
  }
  return { message: line, type: 'default' }
}
