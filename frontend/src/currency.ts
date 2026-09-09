export type Currency = "USD" | "INR" | "CNY";

export const RATES: Record<Currency, number> = { USD: 1, INR: 84, CNY: 7.2 };

export const SYMBOLS: Record<Currency, string> = { USD: "$", INR: "₹", CNY: "¥" };

export const CURRENCIES: { code: Currency; label: string }[] = [
  { code: "USD", label: "USD ($)" },
  { code: "INR", label: "INR (₹)" },
  { code: "CNY", label: "CNY (¥)" },
];

export function toBase(amount: number, currency: Currency): number {
  return amount / RATES[currency];
}

export function formatCurrency(amount: number | undefined, currency: Currency): string {
  if (amount === undefined) return "-";
  return `${SYMBOLS[currency]}${(amount * RATES[currency]).toFixed(2)}`;
}
