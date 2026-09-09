export interface Category {
  id: number;
  name: string;
  icon: string;
  color: string;
  is_active: boolean;
}

export interface CurrencyItem {
  code: string;
  name: string;
  symbol: string;
  exchange_rate: number;
  is_default?: boolean;
}

export interface Expense {
  id: number;
  description: string;
  amount: number;
  category: string;
  date: string;
  currency?: string;
  currency_symbol?: string;
  amount_usd?: number;
  category_id?: number;
  category_icon?: string;
  category_color?: string;
}

export interface ExpenseSummary {
  total: number;
  count: number;
  currency?: string;
  currency_symbol?: string;
  expenses: Expense[];
}

export type ViewMode = "day" | "week" | "month" | "year";

