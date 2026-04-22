"use client"

import { useRef, useEffect } from "react"
import { useChat } from "@/hooks/use-chat"
import { ChatMessage, PromptInput, EmptyState, AIChatHeader } from "@/components/chat"

export default function ChatPage() {
  const { messages, isLoading, isStreaming, sendMessage, clearMessages, retryLastMessage } = useChat()
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  const handleSend = async (content: string) => {
    await sendMessage(content)
  }

  const hasMessages = messages.length > 0

  return (
    <div className="flex h-screen flex-col bg-background">
      <AIChatHeader onNewChat={clearMessages} />

      <main className="flex flex-1 flex-col overflow-hidden">
        {hasMessages ? (
          <div className="flex-1 overflow-y-auto">
            {messages.map((message) => (
              <ChatMessage
                key={message.id}
                message={message}
                onRetry={message.status === "error" ? retryLastMessage : undefined}
              />
            ))}
            <div ref={messagesEndRef} />
          </div>
        ) : (
          <EmptyState onSuggestionClick={handleSend} />
        )}

        <PromptInput
          onSend={handleSend}
          disabled={isLoading || isStreaming}
          placeholder={isStreaming ? "Aguarde a resposta..." : "Envie uma mensagem..."}
        />
      </main>
    </div>
  )
}
