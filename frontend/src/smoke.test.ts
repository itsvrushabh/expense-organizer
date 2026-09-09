import { describe, expect, it } from "bun:test";
import { CURRENCIES, formatCurrency } from "./currency";
import { parseLocalDate, toDateInput } from "./dates";

describe("frontend smoke suite", () => {
  it("core date transformations execute reliably", () => {
    const today = new Date();
    const str = toDateInput(today);
    expect(str).toMatch(/^\d{4}-\d{2}-\d{2}$/);

    const parsed = parseLocalDate(str);
    expect(parsed.getFullYear()).toBe(today.getFullYear());
    expect(parsed.getMonth()).toBe(today.getMonth());
  });

  it("currency list includes USD default and base symbols", () => {
    expect(CURRENCIES.length).toBeGreaterThanOrEqual(3);
    const usd = CURRENCIES.find((c) => c.code === "USD");
    expect(usd).toBeDefined();
    expect(formatCurrency(100, "USD")).toBe("$100.00");
  });
});
