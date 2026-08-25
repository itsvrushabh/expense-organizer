import type { Expense } from '../types'
import { formatCurrency, type Currency } from '../currency'
import { categoryColor } from '../colors'

export function DayExcelView({ expenses, currency }: { expenses: Expense[], currency: Currency }) {
  const categories = [...new Set(expenses.map((e) => e.category))]

  return (
    <table className="excel-table">
      <thead>
        <tr>
          <th>Category</th>
          <th>Description</th>
          <th>Amount</th>
        </tr>
      </thead>
      <tbody>
        {categories.map((category) => {
          const categoryExpenses = expenses.filter((e) => e.category === category)
          const color = categoryColor(category)
          return categoryExpenses.map((expense, idx) => (
            <tr key={expense.id}>
              {idx === 0 && (
                <td rowSpan={categoryExpenses.length} className="category-cell">
                  <span className="category-chip" style={{ background: color.bg, color: color.fg }}>
                    {category}
                  </span>
                </td>
              )}
              <td>{expense.description}</td>
              <td className="amount-cell">{formatCurrency(expense.amount, currency)}</td>
            </tr>
          ))
        })}
        {expenses.length === 0 && (
          <tr>
            <td colSpan={3} className="empty-cell">
              No expenses for this day
            </td>
          </tr>
        )}
      </tbody>
    </table>
  )
}
