import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:expense_organizer_mobile/models/expense.dart';
import 'package:expense_organizer_mobile/models/expense_summary.dart';
import 'package:expense_organizer_mobile/models/queue_item.dart';
import 'package:expense_organizer_mobile/services/api_service.dart';
import 'package:expense_organizer_mobile/services/sync_service.dart';
import 'package:expense_organizer_mobile/utils/currency.dart';
import 'package:expense_organizer_mobile/views/web_style_app_screen.dart';
import 'package:expense_organizer_mobile/views/widgets/period_selector.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  test('Expense model serialization and deserialization', () {
    final json = {
      'id': 101,
      'description': 'Electricity bill',
      'amount': 75.50,
      'category': 'Electricity',
      'date': '2026-09-07',
    };

    final exp = Expense.fromJson(json);
    expect(exp.id, 101);
    expect(exp.description, 'Electricity bill');
    expect(exp.amount, 75.50);
    expect(exp.category, 'Electricity');
    expect(exp.date, '2026-09-07');
    expect(exp.toJson(), json);
  });

  test('ExpenseSummary calculation', () {
    final json = {
      'total': 150.0,
      'count': 2,
      'expenses': [
        {
          'id': 1,
          'description': 'Dinner',
          'amount': 50.0,
          'category': 'Food',
          'date': '2026-09-07',
        },
        {
          'id': 2,
          'description': 'Train',
          'amount': 100.0,
          'category': 'Transport',
          'date': '2026-09-07',
        },
      ],
    };

    final summary = ExpenseSummary.fromJson(json);
    expect(summary.total, 150.0);
    expect(summary.count, 2);
    expect(summary.expenses.length, 2);
  });

  test('QueueItem status flags', () {
    final item = QueueItem(
      id: 'uuid-123',
      description: 'Coffee',
      amount: 4.50,
      category: 'Food',
      date: '2026-09-07',
      status: 'pending',
      retryCount: 0,
      createdAt: '2026-09-07T12:00:00Z',
    );

    expect(item.isPending, true);
    expect(item.isSynced, false);
    expect(item.isFailed, false);
  });

  test('PeriodSelector ISO week calculation', () {
    // 2026-09-07 is Monday of week 37
    final date = DateTime(2026, 9, 7);
    final week = PeriodSelector.isoWeekNumber(date);
    expect(week, 37);
  });

  test('ApiService sanitizeUrl formats addresses properly', () {
    expect(
      ApiService.sanitizeUrl('192.168.1.50:13000/api/'),
      'http://192.168.1.50:13000/api',
    );
    expect(
      ApiService.sanitizeUrl('https://api.myexpense.com///'),
      'https://api.myexpense.com',
    );
    expect(
      ApiService.sanitizeUrl('  http://localhost:13000/api  '),
      'http://localhost:13000/api',
    );
  });

  test(
    'ApiService loads and persists server URL via SharedPreferences',
    () async {
      SharedPreferences.setMockInitialValues({
        ApiService.prefKey: 'http://192.168.1.100:13000/api',
      });

      final api = ApiService();
      await api.loadSavedBaseUrl();
      expect(api.baseUrl, 'http://192.168.1.100:13000/api');

      await api.updateBaseUrl('http://myserver.lan:9000');
      expect(api.baseUrl, 'http://myserver.lan:9000');

      final prefs = await SharedPreferences.getInstance();
      expect(prefs.getString(ApiService.prefKey), 'http://myserver.lan:9000');
    },
  );

  test('AppCurrency formats correctly for USD, INR, and CNY', () {
    expect(AppCurrency.usd.format(10.0), '\$10.00');
    expect(AppCurrency.inr.format(10.0), '₹840.00');
    expect(AppCurrency.cny.format(10.0), '¥72.00');
    expect(AppCurrency.inr.toBase(840.0), 10.0);
  });

  testWidgets(
    'WebStyleAppScreen renders without RenderFlex overflow on small screens',
    (tester) async {
      tester.view.physicalSize = const Size(320, 568);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(() {
        tester.view.resetPhysicalSize();
        tester.view.resetDevicePixelRatio();
      });

      final sync = SyncService();
      await tester.pumpWidget(
        MaterialApp(home: WebStyleAppScreen(syncService: sync)),
      );
      await tester.pump();

      expect(tester.takeException(), isNull);
      expect(find.text('Expense Organizer'), findsOneWidget);
    },
  );
}
