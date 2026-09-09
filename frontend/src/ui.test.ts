import { describe, expect, it } from 'bun:test'
import { parseLocalDate, stepDate, toDateInput } from './dates'
import { toBase } from './currency'

describe('UI navigation and date-stepping logic', () => {
  it('steps day forward and backward correctly across month boundaries', () => {
    const march31 = new Date(2026, 2, 31)
    const april1 = stepDate(march31, 'day', 1)
    expect(toDateInput(april1)).toBe('2026-04-01')

    const backToMarch31 = stepDate(april1, 'day', -1)
    expect(toDateInput(backToMarch31)).toBe('2026-03-31')
  })

  it('steps week forward and backward by 7 days', () => {
    const march15 = new Date(2026, 2, 15)
    const nextWeek = stepDate(march15, 'week', 1)
    expect(toDateInput(nextWeek)).toBe('2026-03-22')

    const prevWeek = stepDate(march15, 'week', -1)
    expect(toDateInput(prevWeek)).toBe('2026-03-08')
  })

  it('steps month forward and backward across year boundary', () => {
    const dec2026 = new Date(2026, 11, 15)
    const jan2027 = stepDate(dec2026, 'month', 1)
    expect(toDateInput(jan2027)).toBe('2027-01-15')

    const backToDec = stepDate(jan2027, 'month', -1)
    expect(toDateInput(backToDec)).toBe('2026-12-15')
  })

  it('steps year forward and backward properly', () => {
    const mid2026 = new Date(2026, 5, 1)
    const mid2027 = stepDate(mid2026, 'year', 1)
    expect(toDateInput(mid2027)).toBe('2027-06-01')

    const mid2025 = stepDate(mid2026, 'year', -1)
    expect(toDateInput(mid2025)).toBe('2025-06-01')
  })

  it('prepares normalized expense submission data for selected currency', () => {
    const rawForm = {
      description: 'Dinner at Bistro',
      amount: '500',
      category: 'Food',
      date: '2026-09-10',
    }

    // Entering 500 in INR should convert to base USD before API submission
    const usdAmount = toBase(parseFloat(rawForm.amount), 'INR')
    const submissionPayload = {
      ...rawForm,
      amount: usdAmount,
    }

    expect(submissionPayload.description).toBe('Dinner at Bistro')
    expect(submissionPayload.amount).toBeCloseTo(5.95, 2)
    expect(submissionPayload.category).toBe('Food')
    expect(submissionPayload.date).toBe('2026-09-10')
  })

  it('filters active categories and resolves category badge colors accurately', () => {
    const backendCategories = [
      { id: 1, name: 'Food', icon: 'utensils', color: '#FF5722', is_active: true },
      { id: 2, name: 'Online', icon: 'globe', color: '#3F51B5', is_active: true },
      { id: 3, name: 'ArchivedCat', icon: 'archive', color: '#9E9E9E', is_active: false },
    ]

    const activeCategories = backendCategories.filter((c) => c.is_active)
    expect(activeCategories.length).toBe(2)
    expect(activeCategories.some((c) => c.name === 'ArchivedCat')).toBe(false)

    // Resolve color badge for selection
    const selectedName = 'online'
    const matched = activeCategories.find((c) => c.name.toLowerCase() === selectedName.toLowerCase())
    expect(matched).toBeDefined()
    expect(matched?.color).toBe('#3F51B5')
    expect(matched?.name).toBe('Online')
  })
})
