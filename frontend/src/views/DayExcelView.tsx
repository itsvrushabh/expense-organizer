import type { Expense } from '../types'

export function DayExcelView({ expenses }: { expenses: Expense[] }) {
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
          return categoryExpenses.map((expense, idx) => (
            <tr key={expense.id}>
              {idx === 0 && (
                <td rowSpan={categoryExpenses.length} className="category-cell">
                  {category}
                </td>
              )}
              <td>{expense.description}</td>
              <td className="amount-cell">${expense.amount.toFixed(2)}</td>
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
