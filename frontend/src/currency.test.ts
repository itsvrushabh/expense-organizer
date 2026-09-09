import { describe, expect, it } from "bun:test";
import {
  CURRENCIES,
  type Currency,
  RATES,
  SYMBOLS,
  formatCurrency,
  toBase,
  updateLiveRates,
} from "./currency";

describe("currency helpers", () => {
  it("has all 6 currencies configured with positive rates and symbols", () => {
    const expectedCurrencies: Currency[] = ["USD", "INR", "EUR", "JPY", "GBP", "CNY"];
    expect(CURRENCIES.length).toBe(6);

    for (const code of expectedCurrencies) {
      expect(RATES[code]).toBeGreaterThan(0);
      expect(SYMBOLS[code]).toBeDefined();
      expect(typeof SYMBOLS[code]).toBe("string");
      expect(CURRENCIES.some((c) => c.code === code)).toBe(true);
    }
  });

  it("toBase converts values properly relative to USD", () => {
    expect(toBase(100, "USD")).toBeCloseTo(100.0, 2);
    // INR: 840 INR / 84 = 10 USD
    expect(toBase(840, "INR")).toBeCloseTo(10.0, 2);
    // EUR: 92 EUR / 0.92 = 100 USD
    expect(toBase(92, "EUR")).toBeCloseTo(100.0, 2);
    // JPY: 1500 JPY / 150 = 10 USD
    expect(toBase(1500, "JPY")).toBeCloseTo(10.0, 2);
    // GBP: 78 GBP / 0.78 = 100 USD
    expect(toBase(78, "GBP")).toBeCloseTo(100.0, 2);
  });

  it("formatCurrency formats amounts with appropriate currency symbol and precision", () => {
    expect(formatCurrency(10, "USD")).toBe("$10.00");
    expect(formatCurrency(10, "INR")).toBe("₹840.00");
    expect(formatCurrency(10, "EUR")).toBe("€9.20");
    expect(formatCurrency(10, "JPY")).toBe("¥1500.00");
    expect(formatCurrency(10, "GBP")).toBe("£7.80");
    expect(formatCurrency(10, "CNY")).toBe("¥72.00");
  });

  it("formatCurrency returns dash when amount is undefined", () => {
    expect(formatCurrency(undefined, "USD")).toBe("-");
    expect(formatCurrency(undefined, "INR")).toBe("-");
  });

  it("updateLiveRates dynamically updates rates and symbols from backend feed", () => {
    const originalInrRate = RATES.INR;
    updateLiveRates([
      { code: "INR", exchange_rate: 94.84, symbol: "₹" },
      { code: "EUR", exchange_rate: 0.86, symbol: "€" },
    ]);
    expect(RATES.INR).toBe(94.84);
    expect(RATES.EUR).toBe(0.86);

    // Verify formatCurrency uses new live rate
    expect(formatCurrency(10, "INR")).toBe("₹948.40");

    // Reset back
    updateLiveRates([
      { code: "INR", exchange_rate: originalInrRate },
      { code: "EUR", exchange_rate: 0.92 },
    ]);
  });
});
