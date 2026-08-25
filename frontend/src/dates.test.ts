import { expect, test } from "bun:test"
import { daysInMonth, parseLocalDate, stepDate, toDateInput } from "./dates"

test("toDateInput formats local YYYY-MM-DD with padded month/day", () => {
  expect(toDateInput(new Date(2026, 7, 3))).toBe("2026-08-03")
  expect(toDateInput(new Date(2026, 0, 1))).toBe("2026-01-01")
})

test("parseLocalDate does not shift the calendar day", () => {
  const d = parseLocalDate("2026-08-23")
  expect(d.getFullYear()).toBe(2026)
  expect(d.getMonth()).toBe(7)
  expect(d.getDate()).toBe(23)
})

test("parseLocalDate accepts a trailing ISO time suffix", () => {
  const d = parseLocalDate("2026-01-15T00:00:00.000Z")
  expect(d.getFullYear()).toBe(2026)
  expect(d.getMonth()).toBe(0)
  expect(d.getDate()).toBe(15)
})

test("daysInMonth handles February in a leap year", () => {
  expect(daysInMonth(2024, 1)).toBe(29)
  expect(daysInMonth(2025, 1)).toBe(28)
  expect(daysInMonth(2026, 7)).toBe(31)
})

test("stepDate moves by the active view unit", () => {
  const start = new Date(2026, 7, 23)
  expect(stepDate(start, "day", 1).getDate()).toBe(24)
  expect(stepDate(start, "month", -1).getMonth()).toBe(6)
  expect(stepDate(start, "year", 1).getFullYear()).toBe(2027)
})
