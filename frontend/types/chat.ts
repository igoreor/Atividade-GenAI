export interface Message {
  id: string
  content: string
  role: 'user' | 'assistant'
  timestamp: Date
  status: 'sending' | 'streaming' | 'complete' | 'error'
  rows?: Record<string, unknown>[]
  row_count?: number
}

export interface ChatState {
  messages: Message[]
  isLoading: boolean
  error: string | null
  isStreaming: boolean
}

export interface Conversation {
  id: string
  title: string
  createdAt: Date
  updatedAt: Date
}
