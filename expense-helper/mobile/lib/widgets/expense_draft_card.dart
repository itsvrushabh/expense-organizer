import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../models/chat_models.dart';

class ExpenseDraftCard extends StatelessWidget {
  final ExpenseDraft draft;
  final bool isAwaitingConfirmation;
  final bool isSaved;
  final int? savedExpenseId;
  final VoidCallback? onConfirm;
  final VoidCallback? onCancel;
  final ValueChanged<String>? onSuggestionTap;

  const ExpenseDraftCard({
    super.key,
    required this.draft,
    this.isAwaitingConfirmation = false,
    this.isSaved = false,
    this.savedExpenseId,
    this.onConfirm,
    this.onCancel,
    this.onSuggestionTap,
  });

  IconData _getCategoryIcon(String category) {
    switch (category.toLowerCase()) {
      case 'food':
      case 'dining':
        return Icons.restaurant;
      case 'groceries':
        return Icons.local_grocery_store;
      case 'transport':
        return Icons.directions_car;
      case 'shopping':
        return Icons.shopping_bag;
      case 'entertainment':
        return Icons.movie;
      case 'utilities':
        return Icons.power;
      case 'health':
        return Icons.local_hospital;
      case 'travel':
        return Icons.flight;
      default:
        return Icons.receipt_long;
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final currencyFormatter = NumberFormat.currency(
      symbol: '\$',
      decimalDigits: 2,
    );

    return Container(
      margin: const EdgeInsets.only(top: 8, bottom: 4),
      decoration: BoxDecoration(
        color: isSaved
            ? Colors.green.withValues(alpha: 0.08)
            : theme.colorScheme.surfaceContainerHighest.withValues(alpha: 0.7),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: isSaved
              ? Colors.green.withValues(alpha: 0.4)
              : theme.colorScheme.primary.withValues(alpha: 0.3),
          width: 1.5,
        ),
      ),
      padding: const EdgeInsets.all(14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header row with Badge & Status
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  Icon(
                    _getCategoryIcon(draft.category),
                    size: 18,
                    color: isSaved ? Colors.green : theme.colorScheme.primary,
                  ),
                  const SizedBox(width: 6),
                  Text(
                    isSaved ? 'SAVED EXPENSE' : 'PENDING EXPENSE',
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 0.8,
                      color: isSaved ? Colors.green : theme.colorScheme.primary,
                    ),
                  ),
                ],
              ),
              if (savedExpenseId != null)
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 8,
                    vertical: 2,
                  ),
                  decoration: BoxDecoration(
                    color: Colors.green.withValues(alpha: 0.2),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    '#$savedExpenseId',
                    style: const TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                      color: Colors.green,
                    ),
                  ),
                ),
            ],
          ),
          const SizedBox(height: 10),

          // Description & Amount Highlight
          Row(
            crossAxisAlignment: CrossAxisAlignment.baseline,
            textBaseline: TextBaseline.alphabetic,
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Text(
                  draft.description,
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                  ),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              const SizedBox(width: 8),
              Text(
                currencyFormatter.format(draft.amount),
                style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                  color: isSaved
                      ? Colors.green.shade700
                      : theme.colorScheme.primary,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),

          // Metadata row: Category & Date chips
          Wrap(
            spacing: 8,
            runSpacing: 4,
            children: [
              Chip(
                materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                padding: EdgeInsets.zero,
                labelPadding: const EdgeInsets.symmetric(horizontal: 8),
                avatar: Icon(_getCategoryIcon(draft.category), size: 14),
                label: Text(
                  draft.category,
                  style: const TextStyle(fontSize: 12),
                ),
                backgroundColor: theme.colorScheme.surface,
                side: BorderSide(
                  color: theme.dividerColor.withValues(alpha: 0.3),
                ),
              ),
              Chip(
                materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                padding: EdgeInsets.zero,
                labelPadding: const EdgeInsets.symmetric(horizontal: 8),
                avatar: const Icon(Icons.calendar_today, size: 13),
                label: Text(draft.date, style: const TextStyle(fontSize: 12)),
                backgroundColor: theme.colorScheme.surface,
                side: BorderSide(
                  color: theme.dividerColor.withValues(alpha: 0.3),
                ),
              ),
            ],
          ),

          // Action Buttons if awaiting confirmation
          if (isAwaitingConfirmation && onConfirm != null) ...[
            const SizedBox(height: 14),
            Row(
              children: [
                Expanded(
                  flex: 3,
                  child: ElevatedButton.icon(
                    onPressed: onConfirm,
                    icon: const Icon(Icons.check_circle_outline, size: 18),
                    label: const Text('Confirm & Save to DB'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.green.shade600,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(vertical: 10),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(10),
                      ),
                    ),
                  ),
                ),
                if (onCancel != null) ...[
                  const SizedBox(width: 8),
                  Expanded(
                    flex: 2,
                    child: OutlinedButton.icon(
                      onPressed: onCancel,
                      icon: const Icon(Icons.close, size: 16),
                      label: const Text('Cancel'),
                      style: OutlinedButton.styleFrom(
                        foregroundColor: Colors.redAccent,
                        side: BorderSide(
                          color: Colors.redAccent.withValues(alpha: 0.5),
                        ),
                        padding: const EdgeInsets.symmetric(vertical: 10),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(10),
                        ),
                      ),
                    ),
                  ),
                ],
              ],
            ),

            // Quick suggestion chips
            if (onSuggestionTap != null) ...[
              const SizedBox(height: 10),
              const Text(
                'Suggestions to update:',
                style: TextStyle(fontSize: 11, color: Colors.grey),
              ),
              const SizedBox(height: 4),
              SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: Row(
                  children: [
                    _buildSuggestionChip('Change date to yesterday'),
                    const SizedBox(width: 6),
                    _buildSuggestionChip('Change category to Food'),
                    const SizedBox(width: 6),
                    _buildSuggestionChip('Change category to Groceries'),
                    const SizedBox(width: 6),
                    _buildSuggestionChip('Change amount'),
                  ],
                ),
              ),
            ],
          ],
        ],
      ),
    );
  }

  Widget _buildSuggestionChip(String label) {
    return ActionChip(
      materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
      labelPadding: const EdgeInsets.symmetric(horizontal: 6),
      label: Text(label, style: const TextStyle(fontSize: 11)),
      onPressed: () => onSuggestionTap?.call(label),
    );
  }
}
