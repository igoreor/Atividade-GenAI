"use client"

import { Sparkles } from "lucide-react"

const suggestions = [
  "Quais são os 10 produtos mais vendidos?",
  "Qual o percentual de pedidos entregues no prazo por estado?",
  "Quais categorias têm maior taxa de avaliação negativa?",
  "Quais estados têm maior volume de pedidos e maior ticket médio?",
]

interface EmptyStateProps {
  onSuggestionClick: (suggestion: string) => void
}

export function EmptyState({ onSuggestionClick }: EmptyStateProps) {
  return (
    <div className="flex flex-1 flex-col items-center justify-center px-4 py-12">
      <div className="mb-8 flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10 text-primary">
        <Sparkles className="h-8 w-8" />
      </div>

      <h1 className="mb-2 text-2xl font-semibold text-foreground">
        E-Commerce Analytics
      </h1>

      <p className="mb-8 max-w-md text-center text-sm text-muted-foreground">
        Faça perguntas em português sobre vendas, entregas, avaliações e consumidores.
      </p>

      <div className="grid w-full max-w-2xl gap-3 sm:grid-cols-2">
        {suggestions.map((suggestion, index) => (
          <button
            key={index}
            onClick={() => onSuggestionClick(suggestion)}
            className="group rounded-xl border border-border bg-secondary/30 p-4 text-left transition-all hover:border-primary/50 hover:bg-secondary/50"
          >
            <p className="text-sm text-foreground group-hover:text-primary transition-colors">
              {suggestion}
            </p>
          </button>
        ))}
      </div>
    </div>
  )
}
