import "./test-setup";
import { describe, expect, it, mock } from "bun:test";
import { act, fireEvent, render, screen } from "@testing-library/react";
import type { Category, Expense } from "./types";
import { DayExcelView } from "./views/DayExcelView";

describe("DayExcelView Component", () => {
  const sampleExpenses: Expense[] = [
    {
      id: 1,
      description: "Groceries purchase",
      amount: 45.5,
      category: "Groceries",
      date: "2026-09-10",
      currency: "USD",
    },
    {
      id: 2,
      description: "Subway Ticket",
      amount: 2.75,
      category: "Transport",
      date: "2026-09-10",
      currency: "USD",
    },
  ];

  const sampleCategories: Category[] = [
    { id: 1, name: "Groceries", icon: "shopping-cart", color: "#4CAF50", is_active: true },
    { id: 2, name: "Transport", icon: "car", color: "#2196F3", is_active: true },
  ];

  it("renders expense table with correct descriptions, badges, and amounts", () => {
    const onUpdate = mock(() => Promise.resolve());
    const onDelete = mock(() => Promise.resolve());

    const { container } = render(
      <DayExcelView
        expenses={sampleExpenses}
        currency="USD"
        categories={sampleCategories}
        onUpdate={onUpdate}
        onDelete={onDelete}
      />,
    );

    expect(screen.getByText("Groceries purchase")).toBeDefined();
    expect(screen.getByText("Subway Ticket")).toBeDefined();
    expect(screen.getByText("$45.50")).toBeDefined();
    expect(screen.getByText("$2.75")).toBeDefined();
    expect(container.querySelectorAll("table").length).toBeGreaterThan(0);
  });

  it("triggers onDelete handler when delete button is clicked", () => {
    const onUpdate = mock(() => Promise.resolve());
    const onDelete = mock(() => Promise.resolve());

    render(
      <DayExcelView
        expenses={sampleExpenses}
        currency="USD"
        categories={sampleCategories}
        onUpdate={onUpdate}
        onDelete={onDelete}
      />,
    );

    const deleteButtons = screen.getAllByText("Delete");
    expect(deleteButtons.length).toBe(2);
    fireEvent.click(deleteButtons[0]!);

    expect(onDelete).toHaveBeenCalledWith(1);
  });

  it("opens edit modal and submits updated expense data", async () => {
    const onUpdate = mock(() => Promise.resolve());
    const onDelete = mock(() => Promise.resolve());

    render(
      <DayExcelView
        expenses={sampleExpenses}
        currency="USD"
        categories={sampleCategories}
        onUpdate={onUpdate}
        onDelete={onDelete}
      />,
    );

    const editButtons = screen.getAllByText("Edit");
    await act(async () => {
      fireEvent.click(editButtons[0]!);
    });

    expect(screen.getByText("Edit Expense")).toBeDefined();
    const saveButton = screen.getByText("Save Changes");
    await act(async () => {
      fireEvent.click(saveButton);
    });

    expect(onUpdate).toHaveBeenCalledWith(1, {
      description: "Groceries purchase",
      amount: 45.5,
      category: "Groceries",
      date: "2026-09-10",
    });
  });

  it("renders empty state message when expenses array is empty", () => {
    const onUpdate = mock(() => Promise.resolve());
    const onDelete = mock(() => Promise.resolve());

    render(
      <DayExcelView
        expenses={[]}
        currency="USD"
        categories={sampleCategories}
        onUpdate={onUpdate}
        onDelete={onDelete}
      />,
    );

    expect(screen.getByText(/no expenses/i)).toBeDefined();
  });
});
