import type { Expense } from '../types'
import { formatCurrency, type Currency } from '../currency'
import { categoryColor } from '../colors'
import { daysInMonth, MONTHS, parseLocalDate } from '../dates'

interface Row {
  key: string
  label: string
  cellClass: string
}

function monthRows(selectedDate: Date): Row[] {
  const year = selectedDate.getFullYear()
  const month = selectedDate.getMonth()
  return Array.from({ length: daysInMonth(year, month) }, (_, i) => ({
    key: String(i + 1),
    label: String(i + 1),
    cellClass: 'date-cell',
  }))
}

function weekRows(selectedDate: Date): Row[] {
  const start = new Date(selectedDate)
  start.setDate(start.getDate() - start.getDay())
  return Array.from({ length: 7 }, (_, i) => {
    const day = new Date(start)
    day.setDate(day.getDate() + i)
    return {
      key: String(i),
      label: day.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }),
      cellClass: 'day-cell',
    }
  })
}
function yearRows(): Row[] {
  return MONTHS.map((name, idx) => ({
    key: String(idx),
    label: name,
    cellClass: 'month-cell',
  }))
}


function bucketKey(expense: Expense, mode: 'week' | 'month' | 'year'): string {
  const d = parseLocalDate(expense.date)
  if (mode === 'week') {
    return String(d.getDay())
  }
  return mode === 'month' ? String(d.getDate()) : String(d.getMonth())
}

function pivot(
  expenses: Expense[],
  categories: string[],
  rows: Row[],
  mode: 'week' | 'month' | 'year',
) {
  const byRowAndCategory: Record<string, Record<string, number>> = {}

  for (const expense of expenses) {
    const key = bucketKey(expense, mode)
    const row = (byRowAndCategory[key] ??= {})
    row[expense.category] = (row[expense.category] ?? 0) + expense.amount
  }

  const rowTotals: Record<string, number> = {}
  for (const row of rows) {
    rowTotals[row.key] = categories.reduce(
      (sum, cat) => sum + (byRowAndCategory[row.key]?.[cat] ?? 0),
      0,
    )
  }

  const categoryTotals: Record<string, number> = {}
  for (const cat of categories) {
    categoryTotals[cat] = rows.reduce(
      (sum, row) => sum + (byRowAndCategory[row.key]?.[cat] ?? 0),
      0,
    )
  }

  return { byRowAndCategory, rowTotals, categoryTotals }
}

function ExcelGridView({
  expenses,
  selectedDate,
  mode,
  currency,
}: {
  expenses: Expense[]
  selectedDate: Date
  mode: 'week' | 'month' | 'year'
  currency: Currency
}) {
  const rows = mode === 'month' ? monthRows(selectedDate) : mode === 'week' ? weekRows(selectedDate) : yearRows()
  const categories = [...new Set(expenses.map((e) => e.category))]
  const showTotals = mode !== 'week'
  const { byRowAndCategory, rowTotals, categoryTotals } = pivot(
    expenses,
    categories,
    rows,
    mode,
  )
  const grandTotal = Object.values(categoryTotals).reduce((a, b) => a + b, 0)
  const tableClass = mode === 'month' ? 'month-table' : mode === 'week' ? 'week-table' : 'year-table'
  return (
    <div className="excel-scroll">
      <table className={`excel-table ${tableClass}`}>
        <thead>
          <tr>
            <th className="sticky-col">Category</th>
            {rows.map((row) => (
              <th key={row.key} className={row.cellClass}>{row.label}</th>
            ))}
            {showTotals && <th className="total-col">Total</th>}
          </tr>
        </thead>
        <tbody>
          {categories.map((category) => {
            const color = categoryColor(category)
            return (
              <tr key={category}>
                <td className="sticky-col">
                  <span className="category-chip" style={{ background: color.bg, color: color.fg }}>
                    {category}
                  </span>
                </td>
                {rows.map((row) => (
                  <td key={row.key} className="amount-cell">
                    {formatCurrency(byRowAndCategory[row.key]?.[category], currency)}
                  </td>
                ))}
                {showTotals && (
                  <td className="total-col amount-cell">
                    {formatCurrency(categoryTotals[category], currency)}
                  </td>
                )}
              </tr>
            )
          })}
          {showTotals && (
            <tr className="totals-row">
              <td className="sticky-col">
                <strong>Total</strong>
              </td>
              {rows.map((row) => (
                <td key={row.key} className="amount-cell">
                  <strong>{formatCurrency(rowTotals[row.key], currency)}</strong>
                </td>
              ))}
              <td className="total-col amount-cell">
                <strong>{formatCurrency(grandTotal, currency)}</strong>
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  )
}

export { ExcelGridView }
