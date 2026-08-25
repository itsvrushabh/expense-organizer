import { useState, useEffect, type FormEvent } from 'react'
import './App.css'
import { api } from './api'
import { formatDate, stepDate, toDateInput } from './dates'
import type { Expense, ViewMode } from './types'
import { DayExcelView } from './views/DayExcelView'
import { ExcelGridView } from './views/ExcelGridView'

const emptyForm = () => ({
  description: '',
  amount: '',
  category: '',
  date: toDateInput(new Date()),
})

function App() {
  const [expenses, setExpenses] = useState<Expense[]>([])
  const [viewMode, setViewMode] = useState<ViewMode>('month')
  const [selectedDate, setSelectedDate] = useState(new Date())
  const [newExpense, setNewExpense] = useState(emptyForm)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchExpenses()
  }, [viewMode, selectedDate])

  const fetchExpenses = async () => {
    try {
      let path = ''
      if (viewMode === 'day') {
        path = `/expenses/day/${toDateInput(selectedDate)}`
      } else if (viewMode === 'month') {
        path = `/expenses/month/${selectedDate.getFullYear()}/${selectedDate.getMonth() + 1}`
      } else {
        path = `/expenses/year/${selectedDate.getFullYear()}`
      }
      const data = await api.getExpenses(path)
      setExpenses(data.expenses || [])
      setError(null)
    } catch (err) {
      console.error('Error fetching expenses:', err)
      setError('Could not load expenses')
    }
  }

  const addExpense = async (e: FormEvent) => {
    e.preventDefault()
    try {
      await api.addExpense({
        ...newExpense,
        amount: parseFloat(newExpense.amount),
      })
      setNewExpense(emptyForm())
      setError(null)
      fetchExpenses()
    } catch (err) {
      console.error('Error adding expense:', err)
      setError('Could not add expense')
    }
  }

  const total = expenses.reduce((sum, exp) => sum + exp.amount, 0)

  return (
    <div className="app">
      <header className="header">
        <h1>Expense Organizer</h1>
      </header>

      {error && <div className="error-banner">{error}</div>}

      <div className="add-expense-form">
        <h2>Add New Expense</h2>
        <form onSubmit={addExpense}>
          <input
            type="text"
            placeholder="Description"
            value={newExpense.description}
            onChange={(e) => setNewExpense({ ...newExpense, description: e.target.value })}
            required
          />
          <input
            type="number"
            placeholder="Amount"
            step="0.01"
            value={newExpense.amount}
            onChange={(e) => setNewExpense({ ...newExpense, amount: e.target.value })}
            required
          />
          <input
            type="text"
            placeholder="Category"
            value={newExpense.category}
            onChange={(e) => setNewExpense({ ...newExpense, category: e.target.value })}
            required
          />
          <input
            type="date"
            value={newExpense.date}
            onChange={(e) => setNewExpense({ ...newExpense, date: e.target.value })}
            required
          />
          <button type="submit">Add Expense</button>
        </form>
      </div>

      <div className="controls">
        <div className="view-selector">
          {(['day', 'month', 'year'] as const).map((mode) => (
            <button
              key={mode}
              className={viewMode === mode ? 'active' : ''}
              onClick={() => setViewMode(mode)}
            >
              {mode.charAt(0).toUpperCase() + mode.slice(1)}
            </button>
          ))}
        </div>

        <div className="date-navigator">
          <button onClick={() => setSelectedDate(stepDate(selectedDate, viewMode, -1))}>◀</button>
          <span className="date-display">{formatDate(selectedDate, viewMode)}</span>
          <button onClick={() => setSelectedDate(stepDate(selectedDate, viewMode, 1))}>▶</button>
        </div>

        <div className="total-display">Total: ${total.toFixed(2)}</div>
      </div>

      <div className="excel-container">
        {viewMode === 'day' ? (
          <DayExcelView expenses={expenses} />
        ) : (
          <ExcelGridView expenses={expenses} selectedDate={selectedDate} mode={viewMode} />
        )}
      </div>
    </div>
  )
}

export default App
