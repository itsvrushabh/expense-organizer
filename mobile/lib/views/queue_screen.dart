import 'package:flutter/material.dart';

import '../services/sync_service.dart';
import '../utils/currency.dart';
import 'server_settings_dialog.dart';

class QueueScreen extends StatefulWidget {
  final SyncService syncService;
  final AppCurrency currency;

  const QueueScreen({
    super.key,
    required this.syncService,
    this.currency = AppCurrency.usd,
  });

  @override
  State<QueueScreen> createState() => _QueueScreenState();
}

class _QueueScreenState extends State<QueueScreen> {
  @override
  Widget build(BuildContext context) {
    final sync = widget.syncService;
    final items = sync.queueItems;
    final pendingCount = sync.pendingCount;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Offline Sync Queue'),
        actions: [
          IconButton(
            icon: const Icon(Icons.dns_outlined),
            tooltip: 'Server Settings',
            onPressed: () {
              ServerSettingsDialog.show(context, widget.syncService);
            },
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Refresh Queue',
            onPressed: () => setState(() {}),
          ),
        ],
      ),
      body: ListenableBuilder(
        listenable: sync,
        builder: (context, _) {
          return Column(
            children: [
              // Queue Summary Card
              Container(
                margin: const EdgeInsets.all(16),
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.grey.shade100,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: Colors.grey.shade300),
                ),
                child: Column(
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              '$pendingCount Pending',
                              style: TextStyle(
                                fontSize: 20,
                                fontWeight: FontWeight.bold,
                                color: pendingCount > 0
                                    ? Colors.amber.shade900
                                    : Colors.green.shade800,
                              ),
                            ),
                            Text(
                              sync.isOnline
                                  ? 'Server is online'
                                  : 'Server is offline (queuing)',
                              style: TextStyle(
                                fontSize: 12,
                                color: sync.isOnline
                                    ? Colors.green.shade700
                                    : Colors.deepOrange.shade700,
                              ),
                            ),
                          ],
                        ),
                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 8,
                            vertical: 4,
                          ),
                          decoration: BoxDecoration(
                            color: sync.rustBridge.isNativeAvailable
                                ? Colors.deepPurple.shade50
                                : Colors.blue.shade50,
                            borderRadius: BorderRadius.circular(6),
                            border: Border.all(
                              color: sync.rustBridge.isNativeAvailable
                                  ? Colors.deepPurple.shade200
                                  : Colors.blue.shade200,
                            ),
                          ),
                          child: Text(
                            sync.rustBridge.isNativeAvailable
                                ? '⚡ Rust Engine'
                                : 'Dart Engine',
                            style: TextStyle(
                              fontSize: 11,
                              fontWeight: FontWeight.bold,
                              color: sync.rustBridge.isNativeAvailable
                                  ? Colors.deepPurple
                                  : Colors.blue.shade800,
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    Row(
                      children: [
                        Expanded(
                          child: ElevatedButton.icon(
                            onPressed:
                                sync.isOnline &&
                                    !sync.isSyncing &&
                                    pendingCount > 0
                                ? () => sync.syncPending()
                                : null,
                            icon: sync.isSyncing
                                ? const SizedBox(
                                    width: 16,
                                    height: 16,
                                    child: CircularProgressIndicator(
                                      strokeWidth: 2,
                                    ),
                                  )
                                : const Icon(Icons.sync, size: 18),
                            label: Text(
                              sync.isSyncing ? 'Syncing...' : 'Sync Now',
                            ),
                          ),
                        ),
                        const SizedBox(width: 8),
                        OutlinedButton(
                          onPressed: items.any((i) => i.isSynced)
                              ? () => sync.clearSynced()
                              : null,
                          child: const Text('Clear Synced'),
                        ),
                      ],
                    ),
                    if (sync.lastError != null) ...[
                      const SizedBox(height: 8),
                      Text(
                        'Last Sync Error: ${sync.lastError}',
                        style: const TextStyle(fontSize: 11, color: Colors.red),
                      ),
                    ],
                  ],
                ),
              ),

              // Items List
              Expanded(
                child: items.isEmpty
                    ? const Center(
                        child: Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(
                              Icons.inbox_outlined,
                              size: 48,
                              color: Colors.grey,
                            ),
                            SizedBox(height: 8),
                            Text(
                              'Offline queue is empty',
                              style: TextStyle(
                                color: Colors.grey,
                                fontSize: 16,
                              ),
                            ),
                          ],
                        ),
                      )
                    : ListView.builder(
                        itemCount: items.length,
                        itemBuilder: (context, index) {
                          // Show newest first
                          final item = items[items.length - 1 - index];
                          return Card(
                            margin: const EdgeInsets.symmetric(
                              horizontal: 16,
                              vertical: 4,
                            ),
                            child: ListTile(
                              leading: Icon(
                                item.isSynced
                                    ? Icons.check_circle
                                    : (item.isFailed
                                          ? Icons.error
                                          : Icons.schedule),
                                color: item.isSynced
                                    ? Colors.green
                                    : (item.isFailed
                                          ? Colors.red
                                          : Colors.amber.shade800),
                              ),
                              title: Text(
                                item.description,
                                style: const TextStyle(
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                              subtitle: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text('${item.category} • ${item.date}'),
                                  if (item.lastError != null)
                                    Text(
                                      'Error: ${item.lastError}',
                                      style: const TextStyle(
                                        color: Colors.red,
                                        fontSize: 11,
                                      ),
                                    ),
                                ],
                              ),
                              trailing: Column(
                                mainAxisAlignment: MainAxisAlignment.center,
                                crossAxisAlignment: CrossAxisAlignment.end,
                                children: [
                                  Text(
                                    widget.currency.format(item.amount),
                                    style: const TextStyle(
                                      fontWeight: FontWeight.bold,
                                      fontSize: 15,
                                    ),
                                  ),
                                  Text(
                                    item.status.toUpperCase(),
                                    style: TextStyle(
                                      fontSize: 10,
                                      fontWeight: FontWeight.bold,
                                      color: item.isSynced
                                          ? Colors.green
                                          : (item.isFailed
                                                ? Colors.red
                                                : Colors.amber.shade800),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          );
                        },
                      ),
              ),
            ],
          );
        },
      ),
    );
  }
}
