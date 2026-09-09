import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';
import '../models/queue_item.dart';
import 'api_service.dart';
import 'rust_bridge.dart';

class SyncService extends ChangeNotifier {
  final ApiService apiService;
  final RustBridge rustBridge;

  bool _isOnline = false;
  bool _isSyncing = false;
  String _queuePath = '';
  List<QueueItem> _queueItems = [];
  Timer? _heartbeatTimer;
  DateTime? _lastSyncTime;
  String? _lastError;

  SyncService({
    ApiService? apiService,
    RustBridge? rustBridge,
  })  : apiService = apiService ?? ApiService(),
        rustBridge = rustBridge ?? RustBridge.instance;

  bool get isOnline => _isOnline;
  bool get isSyncing => _isSyncing;
  int get pendingCount => _queueItems.where((i) => i.isPending || i.isFailed).length;
  List<QueueItem> get queueItems => List.unmodifiable(_queueItems);
  DateTime? get lastSyncTime => _lastSyncTime;
  String? get lastError => _lastError;
  String get queuePath => _queuePath;

  Future<void> initialize() async {
    rustBridge.initialize();
    await apiService.loadSavedBaseUrl();

    try {
      if (kIsWeb) {
        _queuePath = 'expense_queue.json';
      } else {
        final dir = await getApplicationDocumentsDirectory();
        _queuePath = p.join(dir.path, 'expense_queue.json');
      }
    } catch (_) {
      _queuePath = 'expense_queue.json';
    }

    await reloadQueue();
    await checkConnectivity();

    // Start background heartbeat every 4 seconds
    _heartbeatTimer?.cancel();
    _heartbeatTimer = Timer.periodic(const Duration(seconds: 4), (_) async {
      await checkConnectivity();
    });
  }

  Future<void> updateServerUrl(String newUrl) async {
    await apiService.updateBaseUrl(newUrl);
    await checkConnectivity();
    notifyListeners();
  }

  @override
  void dispose() {
    _heartbeatTimer?.cancel();
    super.dispose();
  }

  Future<void> reloadQueue() async {
    if (rustBridge.isNativeAvailable) {
      _queueItems = rustBridge.getQueue(_queuePath);
    } else {
      _queueItems = await _loadQueueFromDisk();
    }
    notifyListeners();
  }

  Future<bool> checkConnectivity() async {
    // Non-blocking async Dart HTTP health check for periodic heartbeats
    // prevents any UI thread freezes when server is unreachable.
    final online = await apiService.checkHealth(timeout: const Duration(milliseconds: 2000));

    final changed = online != _isOnline;
    _isOnline = online;

    if (changed) {
      debugPrint('Connectivity changed: ${_isOnline ? "ONLINE" : "OFFLINE"}');
      notifyListeners();
    }

    // If online and there are pending items, automatically trigger drain
    if (_isOnline && pendingCount > 0 && !_isSyncing) {
      syncPending();
    }

    return _isOnline;
  }

  Future<Map<String, dynamic>> addExpense({
    required String description,
    required double amount,
    required String category,
    required String date,
  }) async {
    // 1. If currently online, attempt direct post
    if (_isOnline) {
      try {
        final expense = await apiService.createExpense(
          description: description,
          amount: amount,
          category: category,
          date: date,
        );
        return {
          'status': 'synced_immediately',
          'expense': expense,
          'message': 'Expense recorded directly to server.',
        };
      } catch (e) {
        debugPrint('Direct post failed ($e), falling back to offline queue');
        _isOnline = false;
        notifyListeners();
      }
    }

    // 2. Server offline or failed post: enqueue into persistent queue
    final item = await _enqueueRecord(
      description: description,
      amount: amount,
      category: category,
      date: date,
    );

    return {
      'status': 'queued',
      'item': item,
      'message': 'Server offline: expense safely queued locally. Will push automatically when online.',
    };
  }

  Future<QueueItem> _enqueueRecord({
    required String description,
    required double amount,
    required String category,
    required String date,
  }) async {
    if (rustBridge.isNativeAvailable) {
      final item = rustBridge.enqueueExpense(
        queuePath: _queuePath,
        description: description,
        amount: amount,
        category: category,
        date: date,
      );
      if (item != null) {
        await reloadQueue();
        return item;
      }
    }

    // Dart fallback
    final item = QueueItem(
      id: DateTime.now().microsecondsSinceEpoch.toString(),
      description: description.trim(),
      amount: amount,
      category: category.trim(),
      date: date.trim(),
      status: 'pending',
      retryCount: 0,
      createdAt: DateTime.now().toIso8601String(),
    );

    final current = await _loadQueueFromDisk();
    current.add(item);
    await _saveQueueToDisk(current);
    _queueItems = current;
    notifyListeners();
    return item;
  }

  Future<void> syncPending() async {
    if (_isSyncing || pendingCount == 0) return;

    _isSyncing = true;
    _lastError = null;
    notifyListeners();

    try {
      if (rustBridge.isNativeAvailable) {
        final res = rustBridge.syncQueue(
          queuePath: _queuePath,
          apiUrl: apiService.baseUrl,
        );
        debugPrint('Rust Sync Result: $res');
        _lastSyncTime = DateTime.now();
        if (res['errors'] != null && (res['errors'] as List).isNotEmpty) {
          _lastError = (res['errors'] as List).join('; ');
        }
      } else {
        await _syncPendingWithDart();
      }
    } catch (e) {
      _lastError = e.toString();
      debugPrint('Sync failed: $e');
    } finally {
      _isSyncing = false;
      await reloadQueue();
    }
  }

  Future<void> _syncPendingWithDart() async {
    final items = await _loadQueueFromDisk();
    for (int i = 0; i < items.length; i++) {
      final item = items[i];
      if (item.status == 'pending' || item.status == 'failed') {
        try {
          await apiService.createExpense(
            description: item.description,
            amount: item.amount,
            category: item.category,
            date: item.date,
          );
          items[i] = QueueItem(
            id: item.id,
            description: item.description,
            amount: item.amount,
            category: item.category,
            date: item.date,
            status: 'synced',
            retryCount: item.retryCount,
            createdAt: item.createdAt,
          );
        } catch (e) {
          items[i] = QueueItem(
            id: item.id,
            description: item.description,
            amount: item.amount,
            category: item.category,
            date: item.date,
            status: 'failed',
            retryCount: item.retryCount + 1,
            createdAt: item.createdAt,
            lastError: e.toString(),
          );
        }
      }
    }
    await _saveQueueToDisk(items);
    _lastSyncTime = DateTime.now();
  }

  Future<void> clearSynced() async {
    if (rustBridge.isNativeAvailable) {
      rustBridge.clearSynced(_queuePath);
    } else {
      final items = await _loadQueueFromDisk();
      items.removeWhere((i) => i.status == 'synced');
      await _saveQueueToDisk(items);
    }
    await reloadQueue();
  }

  Future<List<QueueItem>> _loadQueueFromDisk() async {
    try {
      final file = File(_queuePath);
      if (!file.existsSync()) return [];
      final content = await file.readAsString();
      final list = jsonDecode(content);
      if (list is List) {
        return list.map((e) => QueueItem.fromJson(e as Map<String, dynamic>)).toList();
      }
    } catch (e) {
      debugPrint('Error reading queue file: $e');
    }
    return [];
  }

  Future<void> _saveQueueToDisk(List<QueueItem> items) async {
    try {
      final file = File(_queuePath);
      final parent = file.parent;
      if (!parent.existsSync()) {
        parent.createSync(recursive: true);
      }
      await file.writeAsString(jsonEncode(items.map((i) => i.toJson()).toList()));
    } catch (e) {
      debugPrint('Error writing queue file: $e');
    }
  }
}
