import { useState } from "react";
import { categoryColor } from "../colors";
import { type Currency, formatCurrency } from "../currency";
import type { Expense } from "../types";

interface ExpenseDraft {
  description: string;
  amount: string;
  category: string;
  date: string;
}

function toDraft(expense: Expense): ExpenseDraft {
  return {
    description: expense.description,
    amount: String(expense.amount),
    category: expense.category,
    date: expense.date,
  };
}

export function DayExcelView({
  expenses,
  currency,
  onUpdate,
  onDelete,
}: {
  expenses: Expense[];
  currency: Currency;
  onUpdate: (
    id: number,
    data: { description: string; amount: number; category: string; date: string },
  ) => Promise<void>;
  onDelete: (id: number) => Promise<void>;
}) {
  const [editing, setEditing] = useState<{ id: number; draft: ExpenseDraft } | null>(null);
  const categories = [...new Set(expenses.map((e) => e.category))];

  const openEditor = (expense: Expense) => setEditing({ id: expense.id, draft: toDraft(expense) });

  const saveEdit = async () => {
    if (!editing) return;
    const amount = Number.parseFloat(editing.draft.amount);
    if (
      !editing.draft.description ||
      !editing.draft.category ||
      !editing.draft.date ||
      Number.isNaN(amount)
    ) {
      return;
    }
    await onUpdate(editing.id, {
      description: editing.draft.description.trim(),
      amount,
      category: editing.draft.category.trim(),
      date: editing.draft.date,
    });
    setEditing(null);
  };

  const removeExpense = async (expense: Expense) => {
    if (
      window.confirm(
        `Delete "${expense.description}" (${formatCurrency(expense.amount, currency)})?`,
      )
    ) {
      await onDelete(expense.id);
    }
  };

  return (
    <>
      <table className="excel-table">
        <thead>
          <tr>
            <th>Category</th>
            <th>Description</th>
            <th>Amount</th>
            <th className="actions-col">Actions</th>
          </tr>
        </thead>
        <tbody>
          {categories.map((category) => {
            const categoryExpenses = expenses.filter((e) => e.category === category);
            const color = categoryColor(category);
            return categoryExpenses.map((expense, idx) => (
              <tr key={expense.id}>
                {idx === 0 && (
                  <td rowSpan={categoryExpenses.length} className="category-cell">
                    <span
                      className="category-chip"
                      style={{ background: color.bg, color: color.fg }}
                    >
                      {category}
                    </span>
                  </td>
                )}
                <td>{expense.description}</td>
                <td className="amount-cell">{formatCurrency(expense.amount, currency)}</td>
                <td className="actions-cell">
                  <button className="row-action edit" onClick={() => openEditor(expense)}>
                    Edit
                  </button>
                  <button className="row-action delete" onClick={() => removeExpense(expense)}>
                    Delete
                  </button>
                </td>
              </tr>
            ));
          })}
          {expenses.length === 0 && (
            <tr>
              <td colSpan={4} className="empty-cell">
                No expenses for this day
              </td>
            </tr>
          )}
        </tbody>
      </table>

      {editing && (
        <div className="modal-backdrop" onClick={() => setEditing(null)}>
          <div className="cell-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Edit Expense</h3>
              <button className="modal-close" onClick={() => setEditing(null)} aria-label="Close">
                ×
              </button>
            </div>
            <div className="edit-form">
              <label>
                Description
                <input
                  type="text"
                  value={editing.draft.description}
                  onChange={(e) =>
                    setEditing({
                      ...editing,
                      draft: { ...editing.draft, description: e.target.value },
                    })
                  }
                />
              </label>
              <label>
                Amount (
                {formatCurrency(Number.parseFloat(editing.draft.amount || "0") || 0, currency)})
                <input
                  type="number"
                  step="0.01"
                  min="0.01"
                  value={editing.draft.amount}
                  onChange={(e) =>
                    setEditing({ ...editing, draft: { ...editing.draft, amount: e.target.value } })
                  }
                />
              </label>
              <label>
                Category
                <input
                  type="text"
                  value={editing.draft.category}
                  onChange={(e) =>
                    setEditing({
                      ...editing,
                      draft: { ...editing.draft, category: e.target.value },
                    })
                  }
                />
              </label>
              <label>
                Date
                <input
                  type="date"
                  value={editing.draft.date}
                  onChange={(e) =>
                    setEditing({ ...editing, draft: { ...editing.draft, date: e.target.value } })
                  }
                />
              </label>
            </div>
            <div className="modal-actions">
              <button className="form-button secondary" onClick={() => setEditing(null)}>
                Cancel
              </button>
              <button className="form-button primary" onClick={saveEdit}>
                Save Changes
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
