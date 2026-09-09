import 'expense.dart';

class ExpenseSummary {
  final double total;
  final int count;
  final List<Expense> expenses;

  const ExpenseSummary({
    required this.total,
    required this.count,
    required this.expenses,
  });

  factory ExpenseSummary.fromJson(Map<String, dynamic> json) {
    final list = (json['expenses'] as List<dynamic>?) ?? [];
    return ExpenseSummary(
      total: (json['total'] as num?)?.toDouble() ?? 0.0,
      count: json['count'] as int? ?? list.length,
      expenses: list
          .map((item) => Expense.fromJson(item as Map<String, dynamic>))
          .toList(),
    );
  }

  static const empty = ExpenseSummary(total: 0.0, count: 0, expenses: []);
}
