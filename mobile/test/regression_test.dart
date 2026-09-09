import 'package:flutter_test/flutter_test.dart';
import 'package:expense_organizer_mobile/models/expense.dart';
import 'package:expense_organizer_mobile/models/expense_summary.dart';
import 'package:expense_organizer_mobile/models/queue_item.dart';
import 'package:expense_organizer_mobile/services/api_service.dart';

void main() {
  group('Mobile Regression Suite', () {
    test('Expense model safely ignores new backend fields without error', () {
      final backendEnrichedJson = {
        'id': 42,
        'description': 'Hosting Subscription',
        'amount': 25.00,
        'category': 'Online',
        'date': '2026-02-15',
        'currency': 'USD',
        'currency_symbol': '\$',
        'amount_usd': 25.00,
        'category_id': 11,
        'category_icon': 'globe',
        'category_color': '#009688',
      };

      final expense = Expense.fromJson(backendEnrichedJson);
      expect(expense.id, 42);
      expect(expense.description, 'Hosting Subscription');
      expect(expense.amount, 25.00);
      expect(expense.category, 'Online');
      expect(expense.date, '2026-02-15');
      expect(expense.parsedDate, DateTime(2026, 2, 15));
    });

    test('ExpenseSummary handles empty and null lists safely', () {
      final emptyJson = {'total': 0.0, 'count': 0, 'expenses': null};

      final summary = ExpenseSummary.fromJson(emptyJson);
      expect(summary.total, 0.0);
      expect(summary.count, 0);
      expect(summary.expenses, isEmpty);
      expect(ExpenseSummary.empty.total, 0.0);
    });

    test('QueueItem serializes to and from JSON preserving retry status', () {
      final json = {
        'id': 'retry-test-1',
        'description': 'Pending item',
        'amount': 12.0,
        'category': 'Food',
        'date': '2026-09-10',
        'status': 'pending',
        'retry_count': 2,
        'created_at': '2026-09-10T00:00:00Z',
        'last_error': 'Connection timed out',
      };

      final item = QueueItem.fromJson(json);
      expect(item.id, 'retry-test-1');
      expect(item.retryCount, 2);
      expect(item.lastError, 'Connection timed out');
      expect(item.isPending, true);
      expect(item.isFailed, false);
      expect(item.isSynced, false);

      final outJson = item.toJson();
      expect(outJson['retry_count'], 2);
      expect(outJson['last_error'], 'Connection timed out');
    });

    test('ApiService sanitizes various malformed server URLs', () {
      expect(
        ApiService.sanitizeUrl('   localhost:13000   '),
        'http://localhost:13000',
      );
      expect(
        ApiService.sanitizeUrl('http://myserver.com:8000////'),
        'http://myserver.com:8000',
      );
      expect(
        ApiService.sanitizeUrl('https://secure.api.org/api/'),
        'https://secure.api.org/api',
      );
    });
  });
}
