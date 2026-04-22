"use client"

import { cn } from "@/lib/utils"
import { User, Bot, RotateCcw, Copy, Check } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useState } from "react"
import type { Message } from "@/types/chat"
import { MarkdownMessage } from "./markdown-message"
import { DataViz } from "./data-viz"

interface ChatMessageProps {
  message: Message
  onRetry?: () => void
}

export function ChatMessage({ message, onRetry }: ChatMessageProps) {
  const [copied, setCopied] = useState(false)
  const isUser = message.role === "user"
  const isStreaming = message.status === "streaming"
  const isError = message.status === "error"

  const handleCopy = async () => {
    await navigator.clipboard.writeText(message.content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className={cn("group py-6 px-4 sm:px-6", !isUser && "bg-secondary/20")}>
      <div className="mx-auto max-w-3xl flex gap-4">
        {/* avatar */}
        <div
          className={cn(
            "flex h-8 w-8 shrink-0 items-center justify-center rounded-full mt-0.5",
            isUser
              ? "bg-primary text-primary-foreground"
              : "bg-secondary text-secondary-foreground border border-border"
          )}
        >
          {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
        </div>

        <div className="flex-1 min-w-0 space-y-1">
          <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
            {isUser ? "Você" : "Assistente"}
          </span>

          {/* message body */}
          {isStreaming && !message.content ? (
            <div className="flex items-center gap-1 pt-1">
              <span className="h-2 w-2 rounded-full bg-foreground/50 animate-bounce" style={{ animationDelay: "0ms" }} />
              <span className="h-2 w-2 rounded-full bg-foreground/50 animate-bounce" style={{ animationDelay: "150ms" }} />
              <span className="h-2 w-2 rounded-full bg-foreground/50 animate-bounce" style={{ animationDelay: "300ms" }} />
            </div>
          ) : isUser ? (
            <p className="text-sm leading-relaxed text-foreground">{message.content}</p>
          ) : isError ? (
            <p className="text-sm text-destructive">{message.content}</p>
          ) : (
            <>
              <MarkdownMessage content={message.content} />
              {message.rows && message.rows.length > 0 && (
                <DataViz rows={message.rows} row_count={message.row_count ?? message.rows.length} />
              )}
            </>
          )}

          {/* action buttons */}
          {!isUser && message.status === "complete" && (
            <div className="flex items-center gap-1 pt-1 opacity-0 group-hover:opacity-100 transition-opacity">
              <Button
                variant="ghost" size="sm"
                onClick={handleCopy}
                className="h-7 px-2 text-muted-foreground hover:text-foreground"
              >
                {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
                <span className="ml-1 text-xs">{copied ? "Copiado" : "Copiar"}</span>
              </Button>
            </div>
          )}

          {isError && onRetry && (
            <Button
              variant="outline" size="sm"
              onClick={onRetry}
              className="mt-2 text-destructive border-destructive/50 hover:bg-destructive/10"
            >
              <RotateCcw className="h-4 w-4 mr-2" />
              Tentar novamente
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}
