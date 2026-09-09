import 'package:flutter/material.dart';

import '../../services/sync_service.dart';
import '../queue_screen.dart';

class StatusIndicator extends StatelessWidget {
  final SyncService syncService;

  const StatusIndicator({super.key, required this.syncService});

  @override
  Widget build(BuildContext context) {
    final isOnline = syncService.isOnline;
    final isSyncing = syncService.isSyncing;
    final pending = syncService.pendingCount;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        color: isOnline
            ? (pending > 0 ? Colors.amber.shade50 : Colors.green.shade50)
            : Colors.deepOrange.shade50,
        border: Border(
          bottom: BorderSide(
            color: isOnline
                ? (pending > 0 ? Colors.amber.shade200 : Colors.green.shade200)
                : Colors.deepOrange.shade200,
          ),
        ),
      ),
      child: Row(
        children: [
          // Pulse / Status Dot
          AnimatedContainer(
            duration: const Duration(milliseconds: 300),
            width: 10,
            height: 10,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: isOnline ? Colors.green : Colors.deepOrange,
              boxShadow: [
                BoxShadow(
                  color: (isOnline ? Colors.green : Colors.deepOrange)
                      .withValues(alpha: 0.4),
                  blurRadius: 6,
                  spreadRadius: 2,
                ),
              ],
            ),
          ),
          const SizedBox(width: 8),

          // Label
          Text(
            isOnline ? 'Server Online' : 'Server Offline',
            style: TextStyle(
              fontWeight: FontWeight.bold,
              fontSize: 13,
              color: isOnline
                  ? Colors.green.shade800
                  : Colors.deepOrange.shade900,
            ),
          ),

          const Spacer(),

          // Sync / Queue Status
          if (isSyncing) ...[
            const SizedBox(
              width: 14,
              height: 14,
              child: CircularProgressIndicator(strokeWidth: 2),
            ),
            const SizedBox(width: 8),
            const Text(
              'Pushing queue...',
              style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
            ),
          ] else if (pending > 0) ...[
            InkWell(
              borderRadius: BorderRadius.circular(12),
              onTap: () {
                Navigator.of(context).push(
                  MaterialPageRoute(
                    builder: (_) => QueueScreen(syncService: syncService),
                  ),
                );
              },
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: Colors.amber.shade200,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(
                      Icons.cloud_upload_outlined,
                      size: 14,
                      color: Colors.brown,
                    ),
                    const SizedBox(width: 4),
                    Text(
                      '$pending Queued',
                      style: const TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.bold,
                        color: Colors.brown,
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(width: 8),
            if (isOnline)
              IconButton(
                visualDensity: VisualDensity.compact,
                padding: EdgeInsets.zero,
                constraints: const BoxConstraints(),
                icon: const Icon(Icons.sync, size: 18),
                tooltip: 'Sync Now',
                onPressed: () => syncService.syncPending(),
              ),
          ] else ...[
            Text(
              isOnline ? 'In Sync' : 'Ready to queue',
              style: TextStyle(
                fontSize: 12,
                color: isOnline
                    ? Colors.green.shade700
                    : Colors.deepOrange.shade700,
              ),
            ),
          ],
        ],
      ),
    );
  }
}
