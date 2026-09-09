import 'package:flutter/material.dart';
import '../models/expense.dart';
import '../models/queue_item.dart';
import '../utils/colors.dart';
import '../utils/currency.dart';

class DayExcelView extends StatelessWidget {
  final List<Expense> expenses;
  final List<QueueItem> pendingExpenses;
  final AppCurrency currency;
  final Future<void> Function(int id, String description, double amount, String category, String date) onUpdate;
  final Future<void> Function(int id) onDelete;

  const DayExcelView({
    super.key,
    required this.expenses,
    this.pendingExpenses = const [],
    required this.currency,
    required this.onUpdate,
    required this.onDelete,
  });

  void _openEditor(BuildContext context, Expense expense) {
    showDialog(
      context: context,
      builder: (ctx) => _EditExpenseDialog(
        expense: expense,
        currency: currency,
        onUpdate: onUpdate,
      ),
    );
  }

  void _confirmDelete(BuildContext context, Expense expense) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Delete Expense'),
        content: Text('Delete "${expense.description}" (${currency.format(expense.amount)})?'),
        actions: [
          TextButton(onPressed: () => Navigator.of(ctx).pop(), child: const Text('Cancel')),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red, foregroundColor: Colors.white),
            onPressed: () async {
              await onDelete(expense.id);
              if (ctx.mounted) Navigator.of(ctx).pop();
            },
            child: const Text('Delete'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final allCategories = {
      ...expenses.map((e) => e.category),
      ...pendingExpenses.map((e) => e.category),
    }.toList();

    if (expenses.isEmpty && pendingExpenses.isEmpty) {
      return Container(
        padding: const EdgeInsets.all(40),
        alignment: Alignment.center,
        child: const Column(
          children: [
            Icon(Icons.table_chart_outlined, size: 56, color: Colors.grey),
            SizedBox(height: 12),
            Text('No expenses recorded for this day.', style: TextStyle(color: Colors.grey, fontSize: 16)),
          ],
        ),
      );
    }

    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: ConstrainedBox(
        constraints: BoxConstraints(minWidth: MediaQuery.of(context).size.width - 32),
        child: Container(
          margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: Colors.grey.shade300),
            boxShadow: [
              BoxShadow(color: Colors.black.withValues(alpha: 0.04), blurRadius: 8, offset: const Offset(0, 2)),
            ],
          ),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(12),
            child: DataTable(
              headingRowColor: WidgetStateProperty.all(const Color(0xFFF1F5F9)),
              dataRowMinHeight: 48,
              dataRowMaxHeight: 56,
              columnSpacing: 20,
              headingTextStyle: const TextStyle(fontWeight: FontWeight.bold, color: Color(0xFF1E293B)),
              columns: const [
                DataColumn(label: Text('Category')),
                DataColumn(label: Text('Description')),
                DataColumn(label: Text('Amount'), numeric: true),
                DataColumn(label: Text('Actions')),
              ],
              rows: [
                // Pending Offline Items
                ...pendingExpenses.map((item) {
                  final color = categoryColor(item.category);
                  return DataRow(
                    color: WidgetStateProperty.all(Colors.amber.shade50.withValues(alpha: 0.5)),
                    cells: [
                      DataCell(
                        Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                              decoration: BoxDecoration(
                                color: color.bg,
                                borderRadius: BorderRadius.circular(6),
                              ),
                              child: Text(
                                item.category,
                                style: TextStyle(color: color.fg, fontWeight: FontWeight.bold, fontSize: 12),
                              ),
                            ),
                            const SizedBox(width: 6),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
                              decoration: BoxDecoration(color: Colors.amber.shade200, borderRadius: BorderRadius.circular(4)),
                              child: const Text('⏳ Queued', style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold)),
                            ),
                          ],
                        ),
                      ),
                      DataCell(Text(item.description, style: const TextStyle(fontWeight: FontWeight.w500))),
                      DataCell(
                        Text(
                          currency.format(item.amount),
                          style: const TextStyle(fontWeight: FontWeight.bold),
                        ),
                      ),
                      const DataCell(Text('Pending Sync', style: TextStyle(color: Colors.grey, fontSize: 12))),
                    ],
                  );
                }),

                // Confirmed Server Expenses grouped by category
                for (final cat in allCategories) ...[
                  ...expenses.where((e) => e.category == cat).map((exp) {
                    final color = categoryColor(exp.category);
                    return DataRow(
                      cells: [
                        DataCell(
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                            decoration: BoxDecoration(
                              color: color.bg,
                              borderRadius: BorderRadius.circular(6),
                            ),
                            child: Text(
                              exp.category,
                              style: TextStyle(color: color.fg, fontWeight: FontWeight.bold, fontSize: 12),
                            ),
                          ),
                        ),
                        DataCell(Text(exp.description, style: const TextStyle(fontWeight: FontWeight.w500))),
                        DataCell(
                          Text(
                            currency.format(exp.amount),
                            style: const TextStyle(fontWeight: FontWeight.bold),
                          ),
                        ),
                        DataCell(
                          Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              IconButton(
                                icon: const Icon(Icons.edit_outlined, size: 18, color: Colors.blue),
                                tooltip: 'Edit',
                                onPressed: () => _openEditor(context, exp),
                              ),
                              IconButton(
                                icon: const Icon(Icons.delete_outline, size: 18, color: Colors.red),
                                tooltip: 'Delete',
                                onPressed: () => _confirmDelete(context, exp),
                              ),
                            ],
                          ),
                        ),
                      ],
                    );
                  }),
                ],
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _EditExpenseDialog extends StatefulWidget {
  final Expense expense;
  final AppCurrency currency;
  final Future<void> Function(int id, String description, double amount, String category, String date) onUpdate;

  const _EditExpenseDialog({
    required this.expense,
    required this.currency,
    required this.onUpdate,
  });

  @override
  State<_EditExpenseDialog> createState() => _EditExpenseDialogState();
}

class _EditExpenseDialogState extends State<_EditExpenseDialog> {
  late final TextEditingController _descCtrl;
  late final TextEditingController _amountCtrl;
  late final TextEditingController _catCtrl;
  late final TextEditingController _dateCtrl;
  bool _isSaving = false;

  @override
  void initState() {
    super.initState();
    _descCtrl = TextEditingController(text: widget.expense.description);
    _amountCtrl = TextEditingController(
      text: (widget.expense.amount * widget.currency.rate).toStringAsFixed(2),
    );
    _catCtrl = TextEditingController(text: widget.expense.category);
    _dateCtrl = TextEditingController(text: widget.expense.date);
  }

  @override
  void dispose() {
    _descCtrl.dispose();
    _amountCtrl.dispose();
    _catCtrl.dispose();
    _dateCtrl.dispose();
    super.dispose();
  }

  Future<void> _handleSave() async {
    final rawAmount = double.tryParse(_amountCtrl.text.trim());
    if (rawAmount == null || rawAmount <= 0) return;
    final baseAmount = widget.currency.toBase(rawAmount);

    setState(() => _isSaving = true);
    await widget.onUpdate(
      widget.expense.id,
      _descCtrl.text.trim(),
      baseAmount,
      _catCtrl.text.trim(),
      _dateCtrl.text.trim(),
    );
    if (mounted) Navigator.of(context).pop();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Edit Expense'),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: _descCtrl,
              decoration: const InputDecoration(labelText: 'Description', border: OutlineInputBorder()),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _amountCtrl,
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
              decoration: InputDecoration(
                labelText: 'Amount (${widget.currency.symbol})',
                border: const OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _catCtrl,
              decoration: const InputDecoration(labelText: 'Category', border: OutlineInputBorder()),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _dateCtrl,
              decoration: const InputDecoration(labelText: 'Date (YYYY-MM-DD)', border: OutlineInputBorder()),
            ),
          ],
        ),
      ),
      actions: [
        TextButton(onPressed: () => Navigator.of(context).pop(), child: const Text('Cancel')),
        ElevatedButton(
          onPressed: _isSaving ? null : _handleSave,
          child: _isSaving
              ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
              : const Text('Save'),
        ),
      ],
    );
  }
}

