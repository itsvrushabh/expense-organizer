import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../models/expense.dart';
import '../models/queue_item.dart';
import '../utils/colors.dart';
import '../utils/currency.dart';

class ExcelGridView extends StatelessWidget {
  final List<Expense> expenses;
  final List<QueueItem> pendingExpenses;
  final DateTime selectedDate;
  final String mode; // 'week', 'month', 'year'
  final AppCurrency currency;

  const ExcelGridView({
    super.key,
    required this.expenses,
    this.pendingExpenses = const [],
    required this.selectedDate,
    this.mode = 'week',
    required this.currency,
  });

  List<Map<String, dynamic>> _getRows() {
    if (mode == 'week') {
      final start = selectedDate.subtract(Duration(days: selectedDate.weekday % 7)); // Sunday
      return List.generate(7, (i) {
        final day = start.add(Duration(days: i));
        return {
          'key': i.toString(),
          'label': DateFormat('dd MMM yyyy').format(day),
          'date': day,
        };
      });
    } else if (mode == 'month') {
      final daysInMonth = DateUtils.getDaysInMonth(selectedDate.year, selectedDate.month);
      return List.generate(daysInMonth, (i) {
        final dayNum = i + 1;
        return {
          'key': dayNum.toString(),
          'label': dayNum.toString(),
          'dayNum': dayNum,
        };
      });
    } else {
      // Year
      return List.generate(12, (i) {
        final monthName = DateFormat('MMM').format(DateTime(selectedDate.year, i + 1, 1));
        return {
          'key': i.toString(),
          'label': monthName,
          'monthNum': i + 1,
        };
      });
    }
  }

  String _bucketKey(String dateStr) {
    final d = DateTime.tryParse(dateStr);
    if (d == null) return '-1';

    if (mode == 'week') {
      return (d.weekday % 7).toString();
    } else if (mode == 'month') {
      return d.day.toString();
    } else {
      return (d.month - 1).toString();
    }
  }

  @override
  Widget build(BuildContext context) {
    final categories = {
      ...expenses.map((e) => e.category),
      ...pendingExpenses.map((e) => e.category),
    }.toList();

    if (categories.isEmpty) {
      return Container(
        padding: const EdgeInsets.all(40),
        alignment: Alignment.center,
        child: const Column(
          children: [
            Icon(Icons.grid_on, size: 56, color: Colors.grey),
            SizedBox(height: 12),
            Text('No expenses recorded for this period.', style: TextStyle(color: Colors.grey, fontSize: 16)),
          ],
        ),
      );
    }

    final rows = _getRows();

    // Pivot table: byRowAndCategory[rowKey][category] = sum
    final Map<String, Map<String, double>> byRowAndCategory = {};

    for (final exp in expenses) {
      final key = _bucketKey(exp.date);
      byRowAndCategory.putIfAbsent(key, () => {});
      byRowAndCategory[key]![exp.category] = (byRowAndCategory[key]![exp.category] ?? 0.0) + exp.amount;
    }

    for (final exp in pendingExpenses) {
      final key = _bucketKey(exp.date);
      byRowAndCategory.putIfAbsent(key, () => {});
      byRowAndCategory[key]![exp.category] = (byRowAndCategory[key]![exp.category] ?? 0.0) + exp.amount;
    }

    final Map<String, double> rowTotals = {};
    for (final r in rows) {
      final key = r['key'] as String;
      double sum = 0.0;
      for (final cat in categories) {
        sum += byRowAndCategory[key]?[cat] ?? 0.0;
      }
      rowTotals[key] = sum;
    }

    final Map<String, double> categoryTotals = {};
    for (final cat in categories) {
      double sum = 0.0;
      for (final r in rows) {
        final key = r['key'] as String;
        sum += byRowAndCategory[key]?[cat] ?? 0.0;
      }
      categoryTotals[cat] = sum;
    }

    final grandTotal = categoryTotals.values.fold(0.0, (a, b) => a + b);

    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
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
            dataRowMinHeight: 44,
            dataRowMaxHeight: 52,
            columnSpacing: 18,
            columns: [
              const DataColumn(label: Text('Category', style: TextStyle(fontWeight: FontWeight.bold))),
              ...rows.map((r) => DataColumn(
                    label: Text(r['label'] as String, style: const TextStyle(fontWeight: FontWeight.bold)),
                    numeric: true,
                  )),
              const DataColumn(label: Text('Total', style: TextStyle(fontWeight: FontWeight.bold)), numeric: true),
            ],
            rows: [
              // Category rows
              ...categories.map((cat) {
                final color = categoryColor(cat);
                return DataRow(
                  cells: [
                    DataCell(
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(color: color.bg, borderRadius: BorderRadius.circular(6)),
                        child: Text(cat, style: TextStyle(color: color.fg, fontWeight: FontWeight.bold, fontSize: 12)),
                      ),
                    ),
                    ...rows.map((r) {
                      final val = byRowAndCategory[r['key']]?[cat];
                      return DataCell(
                        Text(
                          val != null && val > 0 ? currency.format(val) : '-',
                          style: TextStyle(
                            color: val != null && val > 0 ? Colors.black87 : Colors.grey.shade400,
                            fontWeight: val != null && val > 0 ? FontWeight.w600 : FontWeight.normal,
                          ),
                        ),
                      );
                    }),
                    DataCell(
                      Text(
                        currency.format(categoryTotals[cat]),
                        style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.blueAccent),
                      ),
                    ),
                  ],
                );
              }),

              // Total row
              DataRow(
                color: WidgetStateProperty.all(const Color(0xFFF8FAFC)),
                cells: [
                  const DataCell(Text('Total', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13))),
                  ...rows.map((r) {
                    final t = rowTotals[r['key']] ?? 0.0;
                    return DataCell(
                      Text(
                        t > 0 ? currency.format(t) : '-',
                        style: const TextStyle(fontWeight: FontWeight.bold),
                      ),
                    );
                  }),
                  DataCell(
                    Text(
                      currency.format(grandTotal),
                      style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.green),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
