import { useEffect, useState } from 'react'
import type { Expense } from '../types'
import { formatCurrency, type Currency } from '../currency'
import { categoryColor } from '../colors'
import { daysInMonth, MONTHS, parseLocalDate } from '../dates'

interface CellSelection {
  title: string
  expenses: Expense[]
}

function Grid6x6View({
  expenses,
  selectedDate,
  mode,
  currency,
}: {
  expenses: Expense[]
  selectedDate: Date
  mode: 'month' | 'year'
  currency: Currency
}) {
  const [selectedCell, setSelectedCell] = useState<CellSelection | null>(null)

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setSelectedCell(null)
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [])

  const buckets: Record<number, Expense[]> = {}

  for (const expense of expenses) {
    const d = parseLocalDate(expense.date)
    let key = -1
    if (mode === 'month') {
      if (d.getFullYear() === selectedDate.getFullYear() && d.getMonth() === selectedDate.getMonth()) {
        key = d.getDate()
      }
    } else if (d.getFullYear() === selectedDate.getFullYear()) {
      key = d.getMonth() + 1
    }

    if (key !== -1) {
      ;(buckets[key] ??= []).push(expense)
    }
  }

  const daysInCurrentMonth = daysInMonth(selectedDate.getFullYear(), selectedDate.getMonth())

  const cells = Array.from({ length: mode === 'month' ? daysInCurrentMonth : 12 }, (_, i) => {
    if (mode === 'month') {
      const day = i + 1
      const date = new Date(selectedDate.getFullYear(), selectedDate.getMonth(), day)
      return {
        key: i,
        label: String(day),
        title: date.toLocaleDateString('en-GB', { weekday: 'short', day: '2-digit', month: 'short', year: 'numeric' }),
        data: buckets[day],
        dimmed: false,
      }
    }
    const val = i + 1
    return {
      key: i,
      label: MONTHS[i] ?? '',
      title: `${MONTHS[i] ?? ''} ${selectedDate.getFullYear()}`,
      data: buckets[val],
      dimmed: false,
    }
  })

  const openCell = (title: string, data: Expense[] | undefined) => {
    if (!data || data.length === 0) return
    setSelectedCell({ title, expenses: [...data].sort((a, b) => b.amount - a.amount) })
  }

  const maxCellTotal = Math.max(
    0,
    ...cells.map((cell) => (cell.data ?? []).reduce((sum, exp) => sum + exp.amount, 0)),
  )

  const cellStyle = (cell: (typeof cells)[number]) => {
    if (!cell.data || cell.data.length === 0 || maxCellTotal === 0) {
      return { '--scl': '0.92' } as React.CSSProperties
    }
    const total = cell.data.reduce((sum, exp) => sum + exp.amount, 0)
    const ratio = total / maxCellTotal
    const level = Math.min(5, Math.max(1, Math.round(ratio * 5)))
    return {
      '--heat-l': `${94 - level * 6}%`,
      '--scl': `${(0.9 + 0.25 * ratio).toFixed(3)}`,
    } as React.CSSProperties
  }

  return (
    <div>
      <div
        className="grid-view"
        style={{
          gridTemplateColumns: `repeat(auto-fill, minmax(${mode === 'month' ? '140px' : '200px'}, 1fr))`,
        }}
      >
        {cells.map((cell) => (
          <div
            key={cell.key}
            className={`grid-cell${cell.data && cell.data.length > 0 ? ' clickable has-data' : ''}`}
            style={cellStyle(cell)}
            onClick={() => openCell(cell.title, cell.data)}
            role={cell.data && cell.data.length > 0 ? 'button' : undefined}
            tabIndex={cell.data && cell.data.length > 0 ? 0 : undefined}
            onKeyDown={(e) => e.key === 'Enter' && openCell(cell.title, cell.data)}
          >
            <div className="cell-label">{cell.label}</div>
            {cell.data && cell.data.length > 0 && (
              <>
                <div className="cell-total">{formatCurrency(cell.data.reduce((sum, exp) => sum + exp.amount, 0), currency)}</div>
                <div className="cell-count">
                  {cell.data.length} {cell.data.length === 1 ? 'entry' : 'entries'}
                </div>
              </>
            )}
          </div>
        ))}
      </div>

      {selectedCell && (
        <div className="modal-backdrop" onClick={() => setSelectedCell(null)}>
          <div className="cell-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{selectedCell.title}</h3>
              <button className="modal-close" onClick={() => setSelectedCell(null)} aria-label="Close">×</button>
            </div>
            {mode === 'year' ? (
              <>
                <ul className="expense-list">
                  {Object.entries(
                    selectedCell.expenses.reduce<Record<string, number>>((byCategory, exp) => {
                      byCategory[exp.category] = (byCategory[exp.category] ?? 0) + exp.amount
                      return byCategory
                    }, {}),
                  )
                    .sort((a, b) => b[1] - a[1])
                    .map(([category, total]) => {
                      const color = categoryColor(category)
                      return (
                        <li key={category} className="expense-row">
                          <span
                            className="category-chip"
                            style={{ background: color.bg, color: color.fg }}
                          >
                            {category}
                          </span>
                          <span className="expense-amount">{formatCurrency(total, currency)}</span>
                        </li>
                      )
                    })}
                </ul>
                <div className="modal-footer">
                  <span>Grand Total</span>
                  <strong>{formatCurrency(selectedCell.expenses.reduce((sum, exp) => sum + exp.amount, 0), currency)}</strong>
                </div>
              </>
            ) : (
              <>
                <ul className="expense-list">
                  {selectedCell.expenses.map((exp) => {
                    const color = categoryColor(exp.category)
                    return (
                      <li key={exp.id} className="expense-row">
                        <div className="expense-main">
                          <span className="expense-desc">{exp.description}</span>
                          <span className="category-chip" style={{ background: color.bg, color: color.fg }}>
                            {exp.category}
                          </span>
                        </div>
                        <span className="expense-amount">{formatCurrency(exp.amount, currency)}</span>
                      </li>
                    )
                  })}
                </ul>
                <div className="modal-footer">
                  <span>Total</span>
                  <strong>{formatCurrency(selectedCell.expenses.reduce((sum, exp) => sum + exp.amount, 0), currency)}</strong>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export { Grid6x6View }
