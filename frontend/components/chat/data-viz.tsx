"use client"

import { useState } from "react"
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell, Legend,
} from "recharts"
import { BarChart2, Table2, ChevronDown, ChevronUp } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

// ── Palette ──────────────────────────────────────────────────────────────────
const COLORS = [
  "#6366f1", "#8b5cf6", "#ec4899", "#f59e0b",
  "#10b981", "#3b82f6", "#ef4444", "#14b8a6",
]

// ── Helpers ──────────────────────────────────────────────────────────────────
function isNumeric(v: unknown): v is number {
  return typeof v === "number" && isFinite(v)
}

function formatValue(key: string, value: unknown): string {
  if (!isNumeric(value)) return String(value ?? "—")
  const lower = key.toLowerCase()
  if (lower.includes("brl") || lower.includes("preco") || lower.includes("ticket") || lower.includes("total") || lower.includes("receita")) {
    return `R$ ${value.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
  }
  if (lower.includes("pct") || lower.includes("percent")) {
    return `${value.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%`
  }
  if (Number.isInteger(value)) return value.toLocaleString("pt-BR")
  return value.toLocaleString("pt-BR", { maximumFractionDigits: 2 })
}

function truncateLabel(label: string, max = 20): string {
  return label.length > max ? label.slice(0, max) + "…" : label
}

// ── Chart type detection ─────────────────────────────────────────────────────
type VizType = "bar" | "bar-horizontal" | "pie" | "table"

function detectViz(rows: Record<string, unknown>[]): {
  type: VizType
  labelKey: string
  numericKeys: string[]
} {
  if (!rows.length) return { type: "table", labelKey: "", numericKeys: [] }

  const keys = Object.keys(rows[0])
  const numericKeys = keys.filter(k => isNumeric(rows[0][k]))
  const stringKeys = keys.filter(k => typeof rows[0][k] === "string")
  const labelKey = stringKeys[0] ?? keys[0]

  // single row — just table
  if (rows.length === 1) return { type: "table", labelKey, numericKeys }

  // too many rows for a meaningful chart
  if (rows.length > 30) return { type: "table", labelKey, numericKeys }

  // no numeric column
  if (!numericKeys.length) return { type: "table", labelKey, numericKeys }

  // pie: few rows + has a percentage/proportion column
  const hasPct = numericKeys.some(k => k.toLowerCase().includes("pct") || k.toLowerCase().includes("percent"))
  if (hasPct && rows.length <= 10 && numericKeys.length === 1) {
    return { type: "pie", labelKey, numericKeys }
  }

  // horizontal bar when many rows
  if (rows.length > 12) return { type: "bar-horizontal", labelKey, numericKeys }

  return { type: "bar", labelKey, numericKeys }
}

// ── Custom tooltip ────────────────────────────────────────────────────────────
interface TooltipEntry { name: string; value: number; payload?: Record<string, unknown> }

function CustomTooltip({ active, payload }: { active?: boolean; payload?: TooltipEntry[] }) {
  if (!active || !payload?.length) return null
  // _label is set in data mapping; fallback to numeric index never shown
  const label = payload[0]?.payload?.["_label"] as string | undefined
  return (
    <div className="rounded-lg border border-border bg-popover px-3 py-2 text-xs shadow-md max-w-55">
      {label && <p className="mb-1 font-medium text-foreground wrap-break-word">{label}</p>}
      {payload.map((p, i) => (
        <p key={i} className="text-muted-foreground">
          {p.name}: <span className="font-medium text-foreground">{formatValue(p.name, p.value)}</span>
        </p>
      ))}
    </div>
  )
}

// ── Table view ────────────────────────────────────────────────────────────────
function DataTable({ rows }: { rows: Record<string, unknown>[] }) {
  const keys = Object.keys(rows[0])
  return (
    <div className="overflow-x-auto rounded-lg border border-border">
      <table className="w-full text-xs">
        <thead className="bg-muted/60">
          <tr>
            {keys.map(k => (
              <th key={k} className="px-3 py-2 text-left font-medium text-foreground/70 whitespace-nowrap">
                {k.replace(/_/g, " ")}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, ri) => (
            <tr key={ri} className={cn("border-t border-border transition-colors hover:bg-muted/30", ri % 2 === 1 && "bg-muted/10")}>
              {keys.map(k => (
                <td key={k} className="px-3 py-1.5 text-foreground/90 whitespace-nowrap">
                  {formatValue(k, row[k])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// ── Bar chart ─────────────────────────────────────────────────────────────────
function BarViz({ rows, labelKey, numericKeys, horizontal }: {
  rows: Record<string, unknown>[]
  labelKey: string
  numericKeys: string[]
  horizontal?: boolean
}) {
  // use only first 2 numeric keys to avoid clutter
  const activeKeys = numericKeys.slice(0, 2)
  const data = rows.map(r => ({
    ...r,
    _label: truncateLabel(String(r[labelKey] ?? ""), horizontal ? 28 : 16),
  }))

  const height = horizontal ? Math.max(260, rows.length * 28) : 260

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart
        data={data}
        layout={horizontal ? "vertical" : "horizontal"}
        margin={{ top: 4, right: 8, left: 8, bottom: horizontal ? 4 : 40 }}
      >
        <CartesianGrid strokeDasharray="3 3" className="stroke-border/40" />
        {horizontal ? (
          <>
            <YAxis dataKey="_label" type="category" width={140} tick={{ fontSize: 11 }} className="fill-muted-foreground" />
            <XAxis type="number" tick={{ fontSize: 11 }} className="fill-muted-foreground" tickFormatter={v => v.toLocaleString("pt-BR")} />
          </>
        ) : (
          <>
            <XAxis dataKey="_label" tick={{ fontSize: 10 }} angle={-35} textAnchor="end" className="fill-muted-foreground" />
            <YAxis tick={{ fontSize: 11 }} className="fill-muted-foreground" tickFormatter={v => v.toLocaleString("pt-BR")} />
          </>
        )}
        <Tooltip content={<CustomTooltip />} />
        {activeKeys.map((k, i) => (
          <Bar key={k} dataKey={k} name={k.replace(/_/g, " ")} fill={COLORS[i]} radius={[3, 3, 0, 0]} maxBarSize={40} />
        ))}
      </BarChart>
    </ResponsiveContainer>
  )
}

// ── Pie chart ─────────────────────────────────────────────────────────────────
function PieViz({ rows, labelKey, numericKey }: {
  rows: Record<string, unknown>[]
  labelKey: string
  numericKey: string
}) {
  const data = rows.map(r => ({
    name: truncateLabel(String(r[labelKey] ?? ""), 22),
    value: Number(r[numericKey] ?? 0),
  }))

  return (
    <ResponsiveContainer width="100%" height={260}>
      <PieChart>
        <Pie data={data} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={90} label={({ name, value }) => `${name}: ${value.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%`} labelLine={false}>
          {data.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
        </Pie>
        <Tooltip formatter={(v: number) => `${v.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%`} />
        <Legend wrapperStyle={{ fontSize: 11 }} />
      </PieChart>
    </ResponsiveContainer>
  )
}

// ── Main component ────────────────────────────────────────────────────────────
interface DataVizProps {
  rows: Record<string, unknown>[]
  row_count: number
}

export function DataViz({ rows, row_count }: DataVizProps) {
  const [open, setOpen] = useState(true)
  const [view, setView] = useState<"chart" | "table">("chart")

  if (!rows.length) return null

  const { type, labelKey, numericKeys } = detectViz(rows)
  const hasChart = type !== "table"

  return (
    <div className="mt-3 rounded-xl border border-border bg-muted/20 overflow-hidden">
      {/* header bar */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-border bg-muted/30">
        <span className="text-xs font-medium text-muted-foreground">
          {row_count} {row_count === 1 ? "resultado" : "resultados"}
        </span>
        <div className="flex items-center gap-1">
          {hasChart && (
            <>
              <Button
                variant="ghost" size="sm"
                className={cn("h-6 px-2 text-xs", view === "chart" && "bg-background shadow-sm")}
                onClick={() => setView("chart")}
              >
                <BarChart2 className="h-3 w-3 mr-1" /> Gráfico
              </Button>
              <Button
                variant="ghost" size="sm"
                className={cn("h-6 px-2 text-xs", view === "table" && "bg-background shadow-sm")}
                onClick={() => setView("table")}
              >
                <Table2 className="h-3 w-3 mr-1" /> Tabela
              </Button>
            </>
          )}
          <Button variant="ghost" size="sm" className="h-6 w-6 p-0" onClick={() => setOpen(o => !o)}>
            {open ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
          </Button>
        </div>
      </div>

      {/* body */}
      {open && (
        <div className="p-3">
          {(!hasChart || view === "table") ? (
            <DataTable rows={rows} />
          ) : type === "pie" ? (
            <PieViz rows={rows} labelKey={labelKey} numericKey={numericKeys[0]} />
          ) : (
            <BarViz rows={rows} labelKey={labelKey} numericKeys={numericKeys} horizontal={type === "bar-horizontal"} />
          )}
        </div>
      )}
    </div>
  )
}
