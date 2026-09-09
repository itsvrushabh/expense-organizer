import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:expense_organizer_mobile/views/widgets/period_selector.dart';

void main() {
  group('Mobile UI Widget Tests', () {
    testWidgets('PeriodSelector renders Day, Week, Month, Year tabs and allows selection', (WidgetTester tester) async {
      PeriodType selectedPeriod = PeriodType.month;
      DateTime selectedDate = DateTime(2026, 9, 10);

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: StatefulBuilder(
              builder: (context, setState) {
                return PeriodSelector(
                  period: selectedPeriod,
                  selectedDate: selectedDate,
                  onPeriodChanged: (newPeriod) {
                    setState(() {
                      selectedPeriod = newPeriod;
                    });
                  },
                  onDateChanged: (newDate) {
                    setState(() {
                      selectedDate = newDate;
                    });
                  },
                );
              },
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();

      // Verify tabs are rendered
      expect(find.text('Day'), findsOneWidget);
      expect(find.text('Week'), findsOneWidget);
      expect(find.text('Month'), findsOneWidget);
      expect(find.text('Year'), findsOneWidget);

      // Tap 'Day' tab
      await tester.tap(find.text('Day'));
      await tester.pumpAndSettle();
      expect(selectedPeriod, PeriodType.day);

      // Tap 'Week' tab
      await tester.tap(find.text('Week'));
      await tester.pumpAndSettle();
      expect(selectedPeriod, PeriodType.week);

      // Tap 'Year' tab
      await tester.tap(find.text('Year'));
      await tester.pumpAndSettle();
      expect(selectedPeriod, PeriodType.year);
    });

    testWidgets('PeriodSelector navigation arrows step dates forward and backward', (WidgetTester tester) async {
      DateTime currentDate = DateTime(2026, 9, 10);

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: StatefulBuilder(
              builder: (context, setState) {
                return PeriodSelector(
                  period: PeriodType.day,
                  selectedDate: currentDate,
                  onPeriodChanged: (_) {},
                  onDateChanged: (newDate) {
                    setState(() {
                      currentDate = newDate;
                    });
                  },
                );
              },
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();

      // Find forward and backward arrow buttons
      final backButton = find.byIcon(Icons.chevron_left);
      final forwardButton = find.byIcon(Icons.chevron_right);

      expect(backButton, findsOneWidget);
      expect(forwardButton, findsOneWidget);

      // Tap back button (steps back 1 day)
      await tester.tap(backButton);
      await tester.pumpAndSettle();
      expect(currentDate.day, 9);

      // Tap forward button twice (steps forward to 10 then 11)
      await tester.tap(forwardButton);
      await tester.pumpAndSettle();
      await tester.tap(forwardButton);
      await tester.pumpAndSettle();
      expect(currentDate.day, 11);
    });
  });
}
