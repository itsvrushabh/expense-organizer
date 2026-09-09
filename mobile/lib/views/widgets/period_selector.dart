import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

enum PeriodType { day, week, month, year }

class PeriodSelector extends StatelessWidget {
  final PeriodType period;
  final DateTime selectedDate;
  final ValueChanged<PeriodType> onPeriodChanged;
  final ValueChanged<DateTime> onDateChanged;

  const PeriodSelector({
    super.key,
    required this.period,
    required this.selectedDate,
    required this.onPeriodChanged,
    required this.onDateChanged,
  });

  static int isoWeekNumber(DateTime date) {
    final dayOfYear = int.parse(DateFormat('D').format(date));
    final woy = ((dayOfYear - date.weekday + 10) / 7).floor();
    if (woy < 1) {
      return 52;
    } else if (woy > 52) {
      if (DateTime(date.year, 12, 28).weekday < 4) {
        return 1;
      }
    }
    return woy;
  }

  void _shift(int delta) {
    switch (period) {
      case PeriodType.day:
        onDateChanged(selectedDate.add(Duration(days: delta)));
        break;
      case PeriodType.week:
        onDateChanged(selectedDate.add(Duration(days: 7 * delta)));
        break;
      case PeriodType.month:
        onDateChanged(DateTime(selectedDate.year, selectedDate.month + delta, 1));
        break;
      case PeriodType.year:
        onDateChanged(DateTime(selectedDate.year + delta, 1, 1));
        break;
    }
  }

  String _getDisplayLabel() {
    switch (period) {
      case PeriodType.day:
        return DateFormat('EEE, MMM d, yyyy').format(selectedDate);
      case PeriodType.week:
        final monday = selectedDate.subtract(Duration(days: selectedDate.weekday - 1));
        final sunday = monday.add(const Duration(days: 6));
        final week = isoWeekNumber(selectedDate);
        return 'Week $week (${DateFormat('MMM d').format(monday)} - ${DateFormat('MMM d').format(sunday)})';
      case PeriodType.month:
        return DateFormat('MMMM yyyy').format(selectedDate);
      case PeriodType.year:
        return DateFormat('yyyy').format(selectedDate);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Column(
      children: [
        // Tab / Segment Selector: Day | Week | Month | Year
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          child: SegmentedButton<PeriodType>(
            segments: const [
              ButtonSegment(value: PeriodType.day, label: Text('Day')),
              ButtonSegment(value: PeriodType.week, label: Text('Week')),
              ButtonSegment(value: PeriodType.month, label: Text('Month')),
              ButtonSegment(value: PeriodType.year, label: Text('Year')),
            ],
            selected: {period},
            onSelectionChanged: (set) {
              if (set.isNotEmpty) onPeriodChanged(set.first);
            },
            showSelectedIcon: false,
            style: const ButtonStyle(
              visualDensity: VisualDensity.compact,
            ),
          ),
        ),

        // Navigation Row: [ < ] [ Label ] [ > ] [ Today ]
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 8),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              IconButton(
                icon: const Icon(Icons.chevron_left),
                tooltip: 'Previous',
                onPressed: () => _shift(-1),
              ),
              Expanded(
                child: Center(
                  child: InkWell(
                    onTap: () async {
                      final picked = await showDatePicker(
                        context: context,
                        initialDate: selectedDate,
                        firstDate: DateTime(2020),
                        lastDate: DateTime(2060),
                      );
                      if (picked != null) onDateChanged(picked);
                    },
                    borderRadius: BorderRadius.circular(8),
                    child: Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Flexible(
                            child: Text(
                              _getDisplayLabel(),
                              style: theme.textTheme.titleMedium?.copyWith(
                                fontWeight: FontWeight.bold,
                              ),
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                          const SizedBox(width: 4),
                          const Icon(Icons.calendar_today, size: 14, color: Colors.grey),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
              IconButton(
                icon: const Icon(Icons.chevron_right),
                tooltip: 'Next',
                onPressed: () => _shift(1),
              ),
              TextButton(
                onPressed: () => onDateChanged(DateTime.now()),
                child: const Text('Today'),
              ),
            ],
          ),
        ),
      ],
    );
  }
}
