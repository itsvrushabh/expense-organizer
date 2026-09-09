import 'dart:convert';
import 'dart:ffi';
import 'dart:io';

import 'package:ffi/ffi.dart';
import 'package:flutter/foundation.dart';

import '../models/queue_item.dart';

// C function signatures
typedef _RustFreeStringC = Void Function(Pointer<Utf8>);
typedef _RustFreeStringDart = void Function(Pointer<Utf8>);

typedef _RustCheckOnlineC = Int32 Function(Pointer<Utf8>, Uint32);
typedef _RustCheckOnlineDart = int Function(Pointer<Utf8>, int);

typedef _RustEnqueueC = Pointer<Utf8> Function(
  Pointer<Utf8>,
  Pointer<Utf8>,
  Double,
  Pointer<Utf8>,
  Pointer<Utf8>,
);
typedef _RustEnqueueDart = Pointer<Utf8> Function(
  Pointer<Utf8>,
  Pointer<Utf8>,
  double,
  Pointer<Utf8>,
  Pointer<Utf8>,
);

typedef _RustGetStringC = Pointer<Utf8> Function(Pointer<Utf8>);
typedef _RustGetStringDart = Pointer<Utf8> Function(Pointer<Utf8>);

typedef _RustGetCountC = Int32 Function(Pointer<Utf8>);
typedef _RustGetCountDart = int Function(Pointer<Utf8>);

typedef _RustSyncQueueC = Pointer<Utf8> Function(Pointer<Utf8>, Pointer<Utf8>);
typedef _RustSyncQueueDart = Pointer<Utf8> Function(
  Pointer<Utf8>,
  Pointer<Utf8>,
);

class RustBridge {
  static final RustBridge instance = RustBridge._internal();
  DynamicLibrary? _dylib;
  bool _isInitialized = false;

  _RustFreeStringDart? _rustFreeString;
  _RustCheckOnlineDart? _rustCheckOnline;
  _RustEnqueueDart? _rustEnqueue;
  _RustGetStringDart? _rustGetQueue;
  _RustGetStringDart? _rustGetPendingQueue;
  _RustGetCountDart? _rustGetQueueCount;
  _RustSyncQueueDart? _rustSyncQueue;
  _RustGetCountDart? _rustClearSynced;

  RustBridge._internal();

  bool get isNativeAvailable => _dylib != null;

  void initialize([String? customLibraryPath]) {
    if (_isInitialized) return;
    _isInitialized = true;

    try {
      if (customLibraryPath != null && File(customLibraryPath).existsSync()) {
        _dylib = DynamicLibrary.open(customLibraryPath);
      } else if (Platform.isLinux) {
        final exeDir = File(Platform.resolvedExecutable).parent.path;
        final candidatePaths = [
          '$exeDir/lib/libexpense_sync_engine.so',
          './rust/target/release/libexpense_sync_engine.so',
          '../rust/target/release/libexpense_sync_engine.so',
          './mobile/rust/target/release/libexpense_sync_engine.so',
          'libexpense_sync_engine.so',
        ];
        for (final path in candidatePaths) {
          if (File(path).existsSync()) {
            _dylib = DynamicLibrary.open(path);
            debugPrint('Loaded Rust sync engine from: $path');
            break;
          }
        }
        _dylib ??= DynamicLibrary.process();
      } else if (Platform.isAndroid) {
        _dylib = DynamicLibrary.open('libexpense_sync_engine.so');
      } else if (Platform.isIOS || Platform.isMacOS) {
        _dylib = DynamicLibrary.process();
      } else if (Platform.isWindows) {
        _dylib = DynamicLibrary.open('expense_sync_engine.dll');
      }

      if (_dylib != null) {
        _bindFunctions();
      }
    } catch (e) {
      debugPrint(
        'Note: Rust native library not loaded ($e). Using Dart engine fallback.',
      );
      _dylib = null;
    }
  }

  void _bindFunctions() {
    final d = _dylib!;
    _rustFreeString = d
        .lookup<NativeFunction<_RustFreeStringC>>('rust_free_string')
        .asFunction<_RustFreeStringDart>();
    _rustCheckOnline = d
        .lookup<NativeFunction<_RustCheckOnlineC>>('rust_check_server_online')
        .asFunction<_RustCheckOnlineDart>();
    _rustEnqueue = d
        .lookup<NativeFunction<_RustEnqueueC>>('rust_enqueue_expense')
        .asFunction<_RustEnqueueDart>();
    _rustGetQueue = d
        .lookup<NativeFunction<_RustGetStringC>>('rust_get_queue')
        .asFunction<_RustGetStringDart>();
    _rustGetPendingQueue = d
        .lookup<NativeFunction<_RustGetStringC>>('rust_get_pending_queue')
        .asFunction<_RustGetStringDart>();
    _rustGetQueueCount = d
        .lookup<NativeFunction<_RustGetCountC>>('rust_get_queue_count')
        .asFunction<_RustGetCountDart>();
    _rustSyncQueue = d
        .lookup<NativeFunction<_RustSyncQueueC>>('rust_sync_queue')
        .asFunction<_RustSyncQueueDart>();
    _rustClearSynced = d
        .lookup<NativeFunction<_RustGetCountC>>('rust_clear_synced')
        .asFunction<_RustGetCountDart>();
  }

  bool checkServerOnline(String apiUrl, {int timeoutMs = 2500}) {
    if (_rustCheckOnline != null) {
      final urlPtr = apiUrl.toNativeUtf8();
      try {
        final result = _rustCheckOnline!(urlPtr, timeoutMs);
        return result == 1;
      } finally {
        calloc.free(urlPtr);
      }
    }
    return false;
  }

  QueueItem? enqueueExpense({
    required String queuePath,
    required String description,
    required double amount,
    required String category,
    required String date,
  }) {
    if (_rustEnqueue != null) {
      final pathPtr = queuePath.toNativeUtf8();
      final descPtr = description.toNativeUtf8();
      final catPtr = category.toNativeUtf8();
      final datePtr = date.toNativeUtf8();

      try {
        final resPtr = _rustEnqueue!(pathPtr, descPtr, amount, catPtr, datePtr);
        if (resPtr == nullptr) return null;
        final jsonStr = resPtr.toDartString();
        _rustFreeString!(resPtr);

        final map = jsonDecode(jsonStr) as Map<String, dynamic>;
        if (map.containsKey('error')) {
          debugPrint('Rust enqueue error: ${map['error']}');
          return null;
        }
        return QueueItem.fromJson(map);
      } finally {
        calloc.free(pathPtr);
        calloc.free(descPtr);
        calloc.free(catPtr);
        calloc.free(datePtr);
      }
    }
    return null;
  }

  List<QueueItem> getQueue(String queuePath) {
    if (_rustGetQueue != null) {
      final pathPtr = queuePath.toNativeUtf8();
      try {
        final resPtr = _rustGetQueue!(pathPtr);
        if (resPtr == nullptr) return [];
        final jsonStr = resPtr.toDartString();
        _rustFreeString!(resPtr);

        final list = jsonDecode(jsonStr);
        if (list is List) {
          return list
              .map((item) => QueueItem.fromJson(item as Map<String, dynamic>))
              .toList();
        }
      } catch (e) {
        debugPrint('Error getting queue from Rust: $e');
      } finally {
        calloc.free(pathPtr);
      }
    }
    return [];
  }

  List<QueueItem> getPendingQueue(String queuePath) {
    if (_rustGetPendingQueue != null) {
      final pathPtr = queuePath.toNativeUtf8();
      try {
        final resPtr = _rustGetPendingQueue!(pathPtr);
        if (resPtr == nullptr) return [];
        final jsonStr = resPtr.toDartString();
        _rustFreeString!(resPtr);

        final list = jsonDecode(jsonStr);
        if (list is List) {
          return list
              .map((item) => QueueItem.fromJson(item as Map<String, dynamic>))
              .toList();
        }
      } catch (e) {
        debugPrint('Error getting pending queue from Rust: $e');
      } finally {
        calloc.free(pathPtr);
      }
    }
    return [];
  }

  int getQueueCount(String queuePath) {
    if (_rustGetQueueCount != null) {
      final pathPtr = queuePath.toNativeUtf8();
      try {
        return _rustGetQueueCount!(pathPtr);
      } finally {
        calloc.free(pathPtr);
      }
    }
    return 0;
  }

  Map<String, dynamic> syncQueue({
    required String queuePath,
    required String apiUrl,
  }) {
    if (_rustSyncQueue != null) {
      final pathPtr = queuePath.toNativeUtf8();
      final urlPtr = apiUrl.toNativeUtf8();
      try {
        final resPtr = _rustSyncQueue!(pathPtr, urlPtr);
        if (resPtr == nullptr) {
          return {
            'success': false,
            'errors': ['Null pointer result'],
          };
        }
        final jsonStr = resPtr.toDartString();
        _rustFreeString!(resPtr);

        return jsonDecode(jsonStr) as Map<String, dynamic>;
      } catch (e) {
        return {
          'success': false,
          'errors': [e.toString()],
        };
      } finally {
        calloc.free(pathPtr);
        calloc.free(urlPtr);
      }
    }
    return {
      'success': false,
      'errors': ['Rust engine not available'],
    };
  }

  int clearSynced(String queuePath) {
    if (_rustClearSynced != null) {
      final pathPtr = queuePath.toNativeUtf8();
      try {
        return _rustClearSynced!(pathPtr);
      } finally {
        calloc.free(pathPtr);
      }
    }
    return 0;
  }
}
