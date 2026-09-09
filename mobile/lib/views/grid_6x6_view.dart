import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../models/expense.dart';
import '../models/queue_item.dart';
import '../utils/colors.dart';
import '../utils/currency.dart';

class Grid6x6View extends StatelessWidget {
  final List<Expense> expenses;
  final List<QueueItem> pendingExpenses;
  final DateTime selectedDate;
  final String mode; // 'month' or 'year'
  final AppCurrency currency;

  const Grid6x6View({
    super.key,
    required this.expenses,
    this.pendingExpenses = const [],
    required this.selectedDate,
    required this.mode,
    required this.currency,
  });

  void _openDetailSheet(
    BuildContext context,
    String title,
    List<Expense> serverItems,
    List<QueueItem> pendingItems,
  ) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) {
        final totalServer = serverItems.fold(0.0, (sum, e) => sum + e.amount);
        final totalPending = pendingItems.fold(0.0, (sum, e) => sum + e.amount);
        final grandTotal = totalServer + totalPending;

        return Container(
          decoration: const BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
          ),
          padding: const EdgeInsets.fromLTRB(20, 16, 20, 24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Header
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    title,
                    style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                  ),
                  IconButton(
                    icon: const Icon(Icons.close),
                    onPressed: () => Navigator.of(ctx).pop(),
                  ),
                ],
              ),
              const Divider(),

              // Items
              ConstrainedBox(
                constraints: BoxConstraints(maxHeight: MediaQuery.of(context).size.height * 0.45),
                child: ListView(
                  shrinkWrap: true,
                  children: [
                    if (pendingItems.isNotEmpty) ...[
                      Padding(
                        padding: const EdgeInsets.symmetric(vertical: 4),
                        child: Text(
                          'OFFLINE QUEUE (${pendingItems.length})',
                          style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Colors.amber.shade900),
                        ),
                      ),
                      ...pendingItems.map((item) {
                        final color = categoryColor(item.category);
                        return ListTile(
                          contentPadding: EdgeInsets.zero,
                          title: Text(item.description, style: const TextStyle(fontWeight: FontWeight.w600)),
                          subtitle: Row(
                            children: [
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                decoration: BoxDecoration(color: color.bg, borderRadius: BorderRadius.circular(4)),
                                child: Text(item.category, style: TextStyle(color: color.fg, fontSize: 11)),
                              ),
                              const SizedBox(width: 6),
                              const Text('⏳ Pending sync', style: TextStyle(fontSize: 11, color: Colors.amber)),
                            ],
                          ),
                          trailing: Text(currency.format(item.amount), style: const TextStyle(fontWeight: FontWeight.bold)),
                        );
                      }),
                      const Divider(),
                    ],

                    if (mode == 'year') ...[
                      // Group by category for year
                      ..._buildCategoryGroupedList(serverItems),
                    ] else ...[
                      // Itemized list for month
                      ...serverItems.map((exp) {
                        final color = categoryColor(exp.category);
                        return ListTile(
                          contentPadding: EdgeInsets.zero,
                          title: Text(exp.description, style: const TextStyle(fontWeight: FontWeight.w600)),
                          subtitle: Container(
                            alignment: Alignment.centerLeft,
                            child: Container(
                              margin: const EdgeInsets.only(top: 4),
                              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                              decoration: BoxDecoration(color: color.bg, borderRadius: BorderRadius.circular(4)),
                              child: Text(exp.category, style: TextStyle(color: color.fg, fontSize: 11)),
                            ),
                          ),
                          trailing: Text(currency.format(exp.amount), style: const TextStyle(fontWeight: FontWeight.bold)),
                        );
                      }),
                    ],
                  ],
                ),
              ),

              const Divider(),
              // Footer
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text('Grand Total', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                  Text(
                    currency.format(grandTotal),
                    style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w900, color: Colors.green),
                  ),
                ],
              ),
            ],
          ),
        );
      },
    );
  }

  List<Widget> _buildCategoryGroupedList(List<Expense> serverItems) {
    final Map<String, double> byCat = {};
    for (final e in serverItems) {
      byCat[e.category] = (byCat[e.category] ?? 0.0) + e.amount;
    }

    final sorted = byCat.entries.toList()..sort((a, b) => b.value.compareTo(a.value));

    return sorted.map((entry) {
      final color = categoryColor(entry.key);
      return ListTile(
        contentPadding: EdgeInsets.zero,
        title: Row(
          children: [
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(color: color.bg, borderRadius: BorderRadius.circular(6)),
              child: Text(entry.key, style: TextStyle(color: color.fg, fontWeight: FontWeight.bold, fontSize: 12)),
            ),
          ],
        ),
        trailing: Text(currency.format(entry.value), style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
      );
    }).toList();
  }

  @override
  Widget build(BuildContext context) {
    final isMonth = mode == 'month';
    final count = isMonth ? DateUtils.getDaysInMonth(selectedDate.year, selectedDate.month) : 12;

    // Bucket expenses
    final Map<int, List<Expense>> buckets = {};
    final Map<int, List<QueueItem>> pendingBuckets = {};

    for (final e in expenses) {
      final d = DateTime.tryParse(e.date);
      if (d == null) continue;
      if (isMonth) {
        if (d.year == selectedDate.year && d.month == selectedDate.month) {
          buckets.putIfAbsent(d.day, () => []).add(e);
        }
      } else {
        if (d.year == selectedDate.year) {
          buckets.putIfAbsent(d.month, () => []).add(e);
        }
      }
    }

    for (final e in pendingExpenses) {
      final d = DateTime.tryParse(e.date);
      if (d == null) continue;
      if (isMonth) {
        if (d.year == selectedDate.year && d.month == selectedDate.month) {
          pendingBuckets.putIfAbsent(d.day, () => []).add(e);
        }
      } else {
        if (d.year == selectedDate.year) {
          pendingBuckets.putIfAbsent(d.month, () => []).add(e);
        }
      }
    }

    // Calculate max cell total for heat map
    double maxCellTotal = 0.0;
    for (int i = 1; i <= count; i++) {
      final sTotal = (buckets[i] ?? []).fold(0.0, (s, e) => s + e.amount);
      final pTotal = (pendingBuckets[i] ?? []).fold(0.0, (s, e) => s + e.amount);
      final sum = sTotal + pTotal;
      if (sum > maxCellTotal) maxCellTotal = sum;
    }

    return LayoutBuilder(
      builder: (context, constraints) {
        final crossAxisCount = isMonth
            ? (constraints.maxWidth > 600 ? 7 : (constraints.maxWidth > 400 ? 5 : 4))
            : (constraints.maxWidth > 600 ? 4 : 3);

        return GridView.builder(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
            crossAxisCount: crossAxisCount,
            crossAxisSpacing: 10,
            mainAxisSpacing: 10,
            childAspectRatio: isMonth ? 1.05 : 1.3,
          ),
          itemCount: count,
          itemBuilder: (context, index) {
            final key = index + 1;
            final serverData = buckets[key] ?? [];
            final pendingData = pendingBuckets[key] ?? [];
            final sTotal = serverData.fold(0.0, (s, e) => s + e.amount);
            final pTotal = pendingData.fold(0.0, (s, e) => s + e.amount);
            final cellTotal = sTotal + pTotal;
            final entriesCount = serverData.length + pendingData.length;

            final hasData = entriesCount > 0;
            final label = isMonth ? key.toString() : DateFormat('MMMM').format(DateTime(selectedDate.year, key, 1));
            final title = isMonth
                ? DateFormat('EEEE, dd MMM yyyy').format(DateTime(selectedDate.year, selectedDate.month, key))
                : '$label ${selectedDate.year}';

            // Heat map color calculation
            Color cellBg = Colors.white;
            Color borderColor = Colors.grey.shade300;

            if (hasData && maxCellTotal > 0) {
              final ratio = (cellTotal / maxCellTotal).clamp(0.0, 1.0);
              // Violet/indigo heat scale matching web UI
              cellBg = Color.lerp(const Color(0xFFF5F3FF), const Color(0xFFDDD6FE), ratio)!;
              borderColor = Color.lerp(const Color(0xFFC4B5FD), const Color(0xFF8B5CF6), ratio)!;
            }

            return InkWell(
              onTap: hasData ? () => _openDetailSheet(context, title, serverData, pendingData) : null,
              borderRadius: BorderRadius.circular(12),
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 200),
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: cellBg,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: borderColor, width: hasData ? 1.5 : 1.0),
                  boxShadow: hasData
                      ? [
                          BoxShadow(
                            color: const Color(0xFF6366F1).withValues(alpha: 0.12),
                            blurRadius: 6,
                            offset: const Offset(0, 2),
                          ),
                        ]
                      : null,
                ),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text(
                      label,
                      style: TextStyle(
                        fontSize: isMonth ? 16 : 14,
                        fontWeight: FontWeight.bold,
                        color: hasData ? const Color(0xFF1E293B) : Colors.grey.shade400,
                      ),
                    ),
                    if (hasData) ...[
                      const SizedBox(height: 4),
                      Text(
                        currency.format(cellTotal),
                        style: const TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w800,
                          color: Color(0xFF4F46E5),
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                      const SizedBox(height: 2),
                      Text(
                        '$entriesCount ${entriesCount == 1 ? 'entry' : 'entries'}',
                        style: TextStyle(fontSize: 10, color: Colors.grey.shade600),
                      ),
                    ],
                  ],
                ),
              ),
            );
          },
        );
      },
    );
  }
}
