import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:expense_organizer_mobile/main.dart';
import 'package:expense_organizer_mobile/services/sync_service.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  testWidgets('Smoke test: App launches and renders without crashing', (WidgetTester tester) async {
    SharedPreferences.setMockInitialValues({});
    final syncService = SyncService();

    await tester.pumpWidget(ExpenseOrganizerMobileApp(syncService: syncService));
    await tester.pumpAndSettle();

    expect(find.byType(MaterialApp), findsOneWidget);
    expect(find.text('Day'), findsOneWidget);
  });
}
