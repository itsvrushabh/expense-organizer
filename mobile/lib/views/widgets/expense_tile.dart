import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

class ExpenseTile extends StatelessWidget {
  final String description;
  final double amount;
  final String category;
  final String date;
  final bool isPending;
  final bool isFailed;
  final String? errorText;

  const ExpenseTile({
    super.key,
    required this.description,
    required this.amount,
    required this.category,
    required this.date,
    this.isPending = false,
    this.isFailed = false,
    this.errorText,
  });

  IconData _getCategoryIcon(String cat) {
    switch (cat.toLowerCase()) {
      case 'food':
      case 'dining':
      case 'groceries':
        return Icons.restaurant;
      case 'transport':
      case 'travel':
      case 'fuel':
        return Icons.directions_car;
      case 'electricity':
      case 'utilities':
        return Icons.bolt;
      case 'internet':
      case 'wifi':
        return Icons.wifi;
      case 'loan':
      case 'emi':
      case 'rent':
        return Icons.account_balance;
      case 'entertainment':
      case 'movies':
        return Icons.movie;
      case 'shopping':
        return Icons.shopping_bag;
      default:
        return Icons.receipt_long;
    }
  }

  Color _getCategoryColor(BuildContext context, String cat) {
    switch (cat.toLowerCase()) {
      case 'food':
        return Colors.orange.shade700;
      case 'transport':
        return Colors.blue.shade700;
      case 'electricity':
        return Colors.amber.shade800;
      case 'internet':
        return Colors.cyan.shade700;
      case 'loan':
        return Colors.purple.shade700;
      case 'entertainment':
        return Colors.pink.shade700;
      case 'shopping':
        return Colors.teal.shade700;
      default:
        return Theme.of(context).colorScheme.primary;
    }
  }

  @override
  Widget build(BuildContext context) {
    final currency = NumberFormat.currency(symbol: '\$', decimalDigits: 2);
    final catColor = _getCategoryColor(context, category);

    return Card(
      elevation: 0,
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(14),
        side: BorderSide(
          color: isPending || isFailed
              ? (isFailed ? Colors.red.shade300 : Colors.amber.shade400)
              : Colors.grey.shade200,
          width: isPending || isFailed ? 1.5 : 1,
        ),
      ),
      color: isPending
          ? Colors.amber.shade50.withValues(alpha: 0.5)
          : (isFailed ? Colors.red.shade50.withValues(alpha: 0.5) : Colors.white),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        child: Row(
          children: [
            // Icon
            CircleAvatar(
              radius: 20,
              backgroundColor: catColor.withValues(alpha: 0.12),
              child: Icon(_getCategoryIcon(category), color: catColor, size: 20),
            ),
            const SizedBox(width: 12),

            // Description + Category + Date
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    description,
                    style: const TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 15,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 4),
                  Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(
                          color: catColor.withValues(alpha: 0.1),
                          borderRadius: BorderRadius.circular(4),
                        ),
                        child: Text(
                          category,
                          style: TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w600,
                            color: catColor,
                          ),
                        ),
                      ),
                      const SizedBox(width: 6),
                      Text(
                        date,
                        style: TextStyle(
                          fontSize: 12,
                          color: Colors.grey.shade600,
                        ),
                      ),
                      if (isPending) ...[
                        const SizedBox(width: 6),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                          decoration: BoxDecoration(
                            color: Colors.amber.shade200,
                            borderRadius: BorderRadius.circular(4),
                          ),
                          child: const Text(
                            '⏳ Queued',
                            style: TextStyle(
                              fontSize: 10,
                              fontWeight: FontWeight.bold,
                              color: Colors.brown,
                            ),
                          ),
                        ),
                      ],
                      if (isFailed) ...[
                        const SizedBox(width: 6),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                          decoration: BoxDecoration(
                            color: Colors.red.shade200,
                            borderRadius: BorderRadius.circular(4),
                          ),
                          child: const Text(
                            '⚠️ Sync Error',
                            style: TextStyle(
                              fontSize: 10,
                              fontWeight: FontWeight.bold,
                              color: Colors.red,
                            ),
                          ),
                        ),
                      ],
                    ],
                  ),
                ],
              ),
            ),

            // Amount
            Text(
              currency.format(amount),
              style: TextStyle(
                fontWeight: FontWeight.w800,
                fontSize: 16,
                color: isFailed ? Colors.red.shade800 : Colors.black87,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
