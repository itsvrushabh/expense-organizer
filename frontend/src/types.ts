export interface Expense {
  id: number
  description: string
  amount: number
  category: string
  date: string
}

export interface ExpenseSummary {
  total: number
  count: number
  expenses: Expense[]
}

export type ViewMode = 'day' | 'week' | 'month' | 'year'
