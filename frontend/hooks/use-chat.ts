"use client"

import { useState, useCallback } from "react"
import type { Message, ChatState } from "@/types/chat"

interface UseChatOptions {
  onError?: (error: string) => void
}

interface UseChatReturn extends ChatState {
  sendMessage: (content: string) => Promise<void>
  clearMessages: () => void
  retryLastMessage: () => Promise<void>
}

interface QueryResult {
  answer: string
  rows: Record<string, unknown>[]
  row_count: number
}

async function fetchQueryResult(question: string): Promise<QueryResult> {
  const response = await fetch("/api/query", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, return_sql: false }),
  })

  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    throw new Error(err.detail ?? `Erro ${response.status} ao consultar o agente.`)
  }

  const data = await response.json()
  return {
    answer: data.answer ?? "Sem resposta disponível.",
    rows: data.rows ?? [],
    row_count: data.row_count ?? 0,
  }
}

export function useChat({
  onError,
}: UseChatOptions = {}): UseChatReturn {
  const [state, setState] = useState<ChatState>({
    messages: [],
    isLoading: false,
    error: null,
    isStreaming: false,
  })

  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim() || state.isLoading || state.isStreaming) return

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      content: content.trim(),
      role: "user",
      timestamp: new Date(),
      status: "complete",
    }

    const assistantMessageId = `assistant-${Date.now()}`

    // Add user message and placeholder for assistant
    setState(prev => ({
      ...prev,
      messages: [
        ...prev.messages,
        userMessage,
        {
          id: assistantMessageId,
          content: "",
          role: "assistant",
          timestamp: new Date(),
          status: "streaming",
        },
      ],
      isLoading: true,
      isStreaming: true,
      error: null,
    }))

    try {
      const result = await fetchQueryResult(content)

      setState(prev => ({
        ...prev,
        messages: prev.messages.map(msg =>
          msg.id === assistantMessageId
            ? { ...msg, content: result.answer, rows: result.rows, row_count: result.row_count, status: "complete" as const }
            : msg
        ),
        isLoading: false,
        isStreaming: false,
      }))
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Erro ao processar mensagem"
      
      setState(prev => ({
        ...prev,
        messages: prev.messages.map(msg =>
          msg.id === assistantMessageId
            ? { ...msg, content: "Desculpe, ocorreu um erro ao processar sua mensagem.", status: "error" as const }
            : msg
        ),
        isLoading: false,
        isStreaming: false,
        error: errorMessage,
      }))

      onError?.(errorMessage)
    }
  }, [state.isLoading, state.isStreaming, onError]) // eslint-disable-line react-hooks/exhaustive-deps

  const clearMessages = useCallback(() => {
    setState({
      messages: [],
      isLoading: false,
      error: null,
      isStreaming: false,
    })
  }, [])

  const retryLastMessage = useCallback(async () => {
    const lastUserMessage = [...state.messages]
      .reverse()
      .find(m => m.role === "user")
    
    if (lastUserMessage) {
      // Remove the last assistant message (error) and retry
      setState(prev => ({
        ...prev,
        messages: prev.messages.slice(0, -1),
      }))
      await sendMessage(lastUserMessage.content)
    }
  }, [state.messages, sendMessage])

  return {
    ...state,
    sendMessage,
    clearMessages,
    retryLastMessage,
  }
}
