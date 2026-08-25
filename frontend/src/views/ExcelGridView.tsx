import type { Expense } from '../types'
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

function yearRows(): Row[] {
  return MONTHS.map((name, idx) => ({
    key: String(idx),
    label: name,
    cellClass: 'month-cell',
  }))
}

function bucketKey(expense: Expense, mode: 'month' | 'year'): string {
  const d = parseLocalDate(expense.date)
  return mode === 'month' ? String(d.getDate()) : String(d.getMonth())
}

function pivot(
  expenses: Expense[],
  categories: string[],
  rows: Row[],
  mode: 'month' | 'year',
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

function formatAmount(amount: number | undefined): string {
  return amount ? `$${amount.toFixed(2)}` : '-'
}

export function ExcelGridView({
  expenses,
  selectedDate,
  mode,
}: {
  expenses: Expense[]
  selectedDate: Date
  mode: 'month' | 'year'
}) {
  const rows = mode === 'month' ? monthRows(selectedDate) : yearRows()
  const categories = [...new Set(expenses.map((e) => e.category))].sort()
  const { byRowAndCategory, rowTotals, categoryTotals } = pivot(
    expenses,
    categories,
    rows,
    mode,
  )
  const grandTotal = Object.values(categoryTotals).reduce((a, b) => a + b, 0)
  const rowHeader = mode === 'month' ? 'Date' : 'Month'
  const totalHeader = mode === 'month' ? 'Daily Total' : 'Monthly Total'
  const tableClass = mode === 'month' ? 'month-table' : 'year-table'

  return (
    <div className="excel-scroll">
      <table className={`excel-table ${tableClass}`} >
        <thead>
        <tr>
          {rows.map((row) => {
            const total = rowTotals[row.key] ?? 0
            return (
              <th key={row.key} className={`sticky-col ${row.cellClass}`}>
                {row.label}
              </th>
            )
          }
          )}
        </tr>
        </thead>
        <tbody>
          <tr></tr>
        </tbody>
      </table>
      <table className={`excel-table ${tableClass}`}>
        <thead>
          <tr>
            <th className="sticky-col">{rowHeader}</th>
            {categories.map((category) => (
              <th key={category}>{category}</th>
            ))}
            <th className="total-col">{totalHeader}</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => {
            const total = rowTotals[row.key] ?? 0
            return (
              <tr key={row.key} className={total > 0 ? 'has-data' : ''}>
                <td className={`sticky-col ${row.cellClass}`}>{row.label}</td>
                {categories.map((category) => (
                  <td key={category} className="amount-cell">
                    {formatAmount(byRowAndCategory[row.key]?.[category])}
                  </td>
                ))}
                <td className="total-col amount-cell">{formatAmount(total)}</td>
              </tr>
            )
          })}
          <tr className="totals-row">
            <td className="sticky-col">
              <strong>Total</strong>
            </td>
            {categories.map((category) => (
              <td key={category} className="amount-cell">
                <strong>${(categoryTotals[category] ?? 0).toFixed(2)}</strong>
              </td>
            ))}
            <td className="total-col amount-cell">
              <strong>${grandTotal.toFixed(2)}</strong>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  )
}
