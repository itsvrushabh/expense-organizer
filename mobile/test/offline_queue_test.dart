import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:expense_organizer_mobile/models/expense.dart';
import 'package:expense_organizer_mobile/services/api_service.dart';
import 'package:expense_organizer_mobile/services/rust_bridge.dart';
import 'package:expense_organizer_mobile/services/sync_service.dart';

class MockNetworkApiService extends ApiService {
  bool isOnline = false;
  final List<Map<String, dynamic>> syncedPayloads = [];

  @override
  Future<bool> checkHealth({
    Duration timeout = const Duration(milliseconds: 2500),
  }) async => isOnline;

  @override
  Future<Expense> createExpense({
    required String description,
    required double amount,
    required String category,
    required String date,
  }) async {
    if (!isOnline) {
      throw const SocketException('Network is unreachable');
    }
    final expense = Expense(
      id: syncedPayloads.length + 1,
      description: description,
      amount: amount,
      category: category,
      date: date,
    );
    syncedPayloads.add({
      'description': description,
      'amount': amount,
      'category': category,
      'date': date,
    });
    return expense;
  }
}

class FallbackRustBridge extends RustBridge {
  FallbackRustBridge() : super();

  @override
  bool get isNativeAvailable => false;
}

void _cleanQueueFiles() {
  for (final filename in ['expense_queue.json', 'mobile/expense_queue.json']) {
    final f = File(filename);
    if (f.existsSync()) {
      try {
        f.deleteSync();
      } catch (_) {}
    }
  }
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    SharedPreferences.setMockInitialValues({});
    _cleanQueueFiles();
  });

  tearDown(() {
    _cleanQueueFiles();
  });

  group('Offline Queue & Network Transition Tests', () {
    test('Dart Fallback: Queues expenses locally when offline and flushes via ApiService on reconnect', () async {
      final mockApi = MockNetworkApiService();
      mockApi.isOnline = false;

      final syncService = SyncService(
        apiService: mockApi,
        rustBridge: FallbackRustBridge(),
      );
      await syncService.initialize();

      // 1. Add 3 expenses while offline
      await syncService.addExpense(
        description: 'Morning Coffee',
        amount: 4.50,
        category: 'Food',
        date: '2026-09-10',
      );
      await syncService.addExpense(
        description: 'Train Ticket',
        amount: 15.00,
        category: 'Transport',
        date: '2026-09-10',
      );
      await syncService.addExpense(
        description: 'Office Supplies',
        amount: 22.00,
        category: 'Shopping',
        date: '2026-09-10',
      );

      // Assert 3 items pending and 0 sent to server
      expect(syncService.pendingCount, 3);
      expect(mockApi.syncedPayloads, isEmpty);

      // 2. Restore network connectivity and sync
      mockApi.isOnline = true;
      await syncService.syncPending();
      while (syncService.isSyncing) {
        await Future.delayed(const Duration(milliseconds: 10));
      }

      // 4. Assert all items flushed in FIFO order
      expect(syncService.pendingCount, 0);
      expect(mockApi.syncedPayloads.length, 3);
      expect(mockApi.syncedPayloads[0]['description'], 'Morning Coffee');
      expect(mockApi.syncedPayloads[1]['description'], 'Train Ticket');
      expect(mockApi.syncedPayloads[2]['description'], 'Office Supplies');

      for (final item in syncService.queueItems) {
        expect(item.isSynced, true);
      }

      syncService.dispose();
    });

    test('Queue persistence survives reload', () async {
      final mockApi = MockNetworkApiService();
      mockApi.isOnline = false;

      final syncService1 = SyncService(
        apiService: mockApi,
        rustBridge: FallbackRustBridge(),
      );
      await syncService1.initialize();

      await syncService1.addExpense(
        description: 'Persisted Lunch',
        amount: 18.0,
        category: 'Food',
        date: '2026-09-10',
      );
      expect(syncService1.pendingCount, 1);
      syncService1.dispose();

      // Second instance reloads queue from disk
      final syncService2 = SyncService(
        apiService: mockApi,
        rustBridge: FallbackRustBridge(),
      );
      await syncService2.initialize();
      expect(syncService2.pendingCount, 1);
      expect(syncService2.queueItems.first.description, 'Persisted Lunch');
      syncService2.dispose();
    });
  });
}
