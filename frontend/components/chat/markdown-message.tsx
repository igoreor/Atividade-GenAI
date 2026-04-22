"use client"

import { cn } from "@/lib/utils"
import { Fragment } from "react"

// ── Inline parser ────────────────────────────────────────────────────────────
// Handles: **bold**, *italic*, `code`
function parseInline(text: string): React.ReactNode[] {
  const parts: React.ReactNode[] = []
  const re = /(\*\*(.+?)\*\*|\*(.+?)\*|`(.+?)`)/g
  let last = 0
  let match: RegExpExecArray | null

  while ((match = re.exec(text)) !== null) {
    if (match.index > last) parts.push(text.slice(last, match.index))

    if (match[2]) {
      parts.push(<strong key={match.index} className="font-semibold">{match[2]}</strong>)
    } else if (match[3]) {
      parts.push(<em key={match.index}>{match[3]}</em>)
    } else if (match[4]) {
      parts.push(
        <code key={match.index} className="rounded bg-muted px-1 py-0.5 font-mono text-xs">
          {match[4]}
        </code>
      )
    }
    last = match.index + match[0].length
  }

  if (last < text.length) parts.push(text.slice(last))
  return parts
}

// ── Block parser ─────────────────────────────────────────────────────────────
function parseBlocks(markdown: string): React.ReactNode[] {
  const lines = markdown.split("\n")
  const nodes: React.ReactNode[] = []
  let i = 0

  while (i < lines.length) {
    const line = lines[i]

    // blank line
    if (!line.trim()) { i++; continue }

    // heading
    const headingMatch = line.match(/^(#{1,3})\s+(.+)/)
    if (headingMatch) {
      const level = headingMatch[1].length
      const Tag = level === 1 ? "h2" : level === 2 ? "h3" : "h4"
      const cls = level === 1
        ? "mt-4 mb-1 text-base font-bold"
        : level === 2
        ? "mt-3 mb-1 text-sm font-bold"
        : "mt-2 text-sm font-semibold"
      nodes.push(<Tag key={i} className={cls}>{parseInline(headingMatch[2])}</Tag>)
      i++; continue
    }

    // pipe table
    if (line.trim().startsWith("|")) {
      const tableLines: string[] = []
      while (i < lines.length && lines[i].trim().startsWith("|")) {
        tableLines.push(lines[i])
        i++
      }
      // filter separator rows (---|---)
      const dataRows = tableLines.filter(l => !/^\s*\|[\s\-|:]+\|\s*$/.test(l))
      if (dataRows.length > 0) {
        const parseRow = (r: string) =>
          r.split("|").map(c => c.trim()).filter((_, idx, arr) => idx > 0 && idx < arr.length - 1)

        const [header, ...body] = dataRows
        nodes.push(
          <div key={i} className="my-3 overflow-x-auto rounded-lg border border-border">
            <table className="w-full text-xs">
              <thead className="bg-muted/60">
                <tr>
                  {parseRow(header).map((cell, ci) => (
                    <th key={ci} className="px-3 py-2 text-left font-medium text-foreground/80">
                      {parseInline(cell)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {body.map((row, ri) => (
                  <tr key={ri} className={cn("border-t border-border", ri % 2 === 1 && "bg-muted/20")}>
                    {parseRow(row).map((cell, ci) => (
                      <td key={ci} className="px-3 py-1.5 text-foreground/90">{parseInline(cell)}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      }
      continue
    }

    // unordered list
    if (/^[\-\*]\s/.test(line)) {
      const items: string[] = []
      while (i < lines.length && /^[\-\*]\s/.test(lines[i])) {
        items.push(lines[i].replace(/^[\-\*]\s+/, ""))
        i++
      }
      nodes.push(
        <ul key={i} className="my-2 ml-4 space-y-1 list-disc text-sm">
          {items.map((item, ii) => <li key={ii}>{parseInline(item)}</li>)}
        </ul>
      )
      continue
    }

    // ordered list
    if (/^\d+\.\s/.test(line)) {
      const items: string[] = []
      while (i < lines.length && /^\d+\.\s/.test(lines[i])) {
        items.push(lines[i].replace(/^\d+\.\s+/, ""))
        i++
      }
      nodes.push(
        <ol key={i} className="my-2 ml-4 space-y-1 list-decimal text-sm">
          {items.map((item, ii) => <li key={ii}>{parseInline(item)}</li>)}
        </ol>
      )
      continue
    }

    // paragraph
    const paraLines: string[] = []
    while (
      i < lines.length &&
      lines[i].trim() &&
      !/^(#{1,3}\s|[\-\*]\s|\d+\.\s|\|)/.test(lines[i])
    ) {
      paraLines.push(lines[i])
      i++
    }
    if (paraLines.length) {
      nodes.push(
        <p key={i} className="text-sm leading-relaxed">
          {parseInline(paraLines.join(" "))}
        </p>
      )
    }
  }

  return nodes
}

// ── Component ────────────────────────────────────────────────────────────────
interface MarkdownMessageProps {
  content: string
  className?: string
}

export function MarkdownMessage({ content, className }: MarkdownMessageProps) {
  const blocks = parseBlocks(content)
  return (
    <div className={cn("space-y-1 text-foreground", className)}>
      {blocks.map((block, i) => <Fragment key={i}>{block}</Fragment>)}
    </div>
  )
}
