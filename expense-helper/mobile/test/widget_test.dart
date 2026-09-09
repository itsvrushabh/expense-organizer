import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:expense_helper/main.dart';
import 'package:expense_helper/models/chat_models.dart';
import 'package:expense_helper/widgets/expense_draft_card.dart';

void main() {
  testWidgets('Expense Helper App renders chat screen and welcome message', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(const ExpenseHelperApp());
    await tester.pump();

    // Verify AppBar title
    expect(find.text('Expense Helper'), findsOneWidget);

    // Verify welcome message is displayed
    expect(find.textContaining('AI Expense Helper'), findsOneWidget);

    // Verify input textfield and send icon
    expect(find.byType(TextField), findsOneWidget);
    expect(find.byIcon(Icons.send), findsOneWidget);

    // Verify quick prompt chips
    expect(find.text('Spent \$45 on groceries today'), findsOneWidget);
  });

  testWidgets(
    'ExpenseDraftCard displays draft fields and confirmation buttons',
    (WidgetTester tester) async {
      bool confirmed = false;
      bool cancelled = false;
      String tappedSuggestion = '';

      final draft = ExpenseDraft(
        description: 'Dinner with team',
        amount: 65.50,
        category: 'Food',
        date: '2026-09-09',
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ExpenseDraftCard(
              draft: draft,
              isAwaitingConfirmation: true,
              onConfirm: () => confirmed = true,
              onCancel: () => cancelled = true,
              onSuggestionTap: (s) => tappedSuggestion = s,
            ),
          ),
        ),
      );

      // Verify draft details
      expect(find.text('Dinner with team'), findsOneWidget);
      expect(find.text('\$65.50'), findsOneWidget);
      expect(find.text('Food'), findsOneWidget);
      expect(find.text('2026-09-09'), findsOneWidget);

      // Verify action buttons
      expect(find.text('Confirm & Save to DB'), findsOneWidget);
      expect(find.text('Cancel'), findsOneWidget);

      // Tap confirm button
      await tester.tap(find.text('Confirm & Save to DB'));
      await tester.pump();
      expect(confirmed, isTrue);

      // Tap cancel button
      await tester.tap(find.text('Cancel'));
      await tester.pump();
      expect(cancelled, isTrue);

      // Tap suggestion chip
      await tester.tap(find.text('Change date to yesterday'));
      await tester.pump();
      expect(tappedSuggestion, 'Change date to yesterday');
    },
  );

  testWidgets('ExpenseDraftCard shows saved badge when saved', (
    WidgetTester tester,
  ) async {
    final draft = ExpenseDraft(
      description: 'Coffee',
      amount: 4.50,
      category: 'Food',
      date: '2026-09-09',
    );

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: ExpenseDraftCard(
            draft: draft,
            isAwaitingConfirmation: false,
            isSaved: true,
            savedExpenseId: 105,
          ),
        ),
      ),
    );

    expect(find.text('SAVED EXPENSE'), findsOneWidget);
    expect(find.text('#105'), findsOneWidget);
    expect(find.text('Confirm & Save to DB'), findsNothing);
  });
}
