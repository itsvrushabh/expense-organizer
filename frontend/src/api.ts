import type { Expense, ExpenseSummary } from './types'

/**
 * Browser calls go to the Bun server's /api proxy, which forwards to the
 * FastAPI backend. That way docker-compose's API_URL=http://backend:8000
 * is used server-side and never has to be baked into the client bundle.
 */
const API_BASE = '/api'

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const detail = await res.text().catch(() => res.statusText)
    throw new Error(detail || `Request failed: ${res.status}`)
  }
  return res.json() as Promise<T>
}

export const api = {
  getExpenses: async (path: string): Promise<ExpenseSummary> =>
    handle<ExpenseSummary>(await fetch(`${API_BASE}${path}`)),

  addExpense: async (data: {
    description: string
    amount: number
    category: string
    date: string
  }): Promise<Expense> =>
    handle<Expense>(
      await fetch(`${API_BASE}/expenses`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      }),
    ),

  updateExpense: async (
    id: number,
    data: {
      description: string
      amount: number
      category: string
      date: string
    },
  ): Promise<Expense> =>
    handle<Expense>(
      await fetch(`${API_BASE}/expenses/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      }),
    ),

  deleteExpense: async (id: number): Promise<void> => {
    const res = await fetch(`${API_BASE}/expenses/${id}`, { method: 'DELETE' })
    if (!res.ok) throw new Error(`Failed to delete expense ${id}`)
  },
}
