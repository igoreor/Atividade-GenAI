"use client"

import { useState, useRef, useCallback, KeyboardEvent } from "react"
import { ArrowUp } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface PromptInputProps {
  onSend: (message: string) => void
  disabled?: boolean
  placeholder?: string
}

export function PromptInput({
  onSend,
  disabled = false,
  placeholder = "Envie uma mensagem...",
}: PromptInputProps) {
  const [message, setMessage] = useState("")
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const handleSend = useCallback(() => {
    if (message.trim() && !disabled) {
      onSend(message)
      setMessage("")
      
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto"
      }
    }
  }, [message, disabled, onSend])

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setMessage(e.target.value)
    
    const textarea = e.target
    textarea.style.height = "auto"
    textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`
  }

  return (
    <div className="border-t border-border bg-background/80 backdrop-blur-sm">
      <div className="mx-auto max-w-3xl px-4 py-4">
        <div className="relative flex items-end rounded-2xl border border-border bg-secondary/50 shadow-sm focus-within:ring-2 focus-within:ring-ring focus-within:ring-offset-2 focus-within:ring-offset-background">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={handleInput}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled}
            rows={1}
            className={cn(
              "flex-1 resize-none bg-transparent px-4 py-3 pr-12 text-sm",
              "placeholder:text-muted-foreground",
              "focus:outline-none",
              "disabled:cursor-not-allowed disabled:opacity-50",
              "scrollbar-thin scrollbar-thumb-muted"
            )}
            style={{ maxHeight: "200px" }}
          />
          
          <div className="absolute right-2 bottom-2">
            <Button
              onClick={handleSend}
              disabled={!message.trim() || disabled}
              size="icon"
              className={cn(
                "h-8 w-8 rounded-lg transition-all",
                message.trim() && !disabled
                  ? "bg-primary hover:bg-primary/90 text-primary-foreground"
                  : "bg-muted text-muted-foreground cursor-not-allowed"
              )}
              aria-label="Enviar mensagem"
            >
              <ArrowUp className="h-4 w-4" />
            </Button>
          </div>
        </div>

        <p className="mt-2 text-center text-xs text-muted-foreground">
          A IA pode cometer erros. Considere verificar informações importantes.
        </p>
      </div>
    </div>
  )
}
