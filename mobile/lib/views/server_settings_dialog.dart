import 'package:flutter/material.dart';
import '../services/sync_service.dart';

class ServerSettingsDialog extends StatefulWidget {
  final SyncService syncService;
  final VoidCallback? onServerChanged;

  const ServerSettingsDialog({
    super.key,
    required this.syncService,
    this.onServerChanged,
  });

  static Future<void> show(BuildContext context, SyncService syncService, {VoidCallback? onServerChanged}) {
    return showDialog(
      context: context,
      builder: (ctx) => ServerSettingsDialog(
        syncService: syncService,
        onServerChanged: onServerChanged,
      ),
    );
  }

  @override
  State<ServerSettingsDialog> createState() => _ServerSettingsDialogState();
}

class _ServerSettingsDialogState extends State<ServerSettingsDialog> {
  late final TextEditingController _urlController;
  bool _isTesting = false;
  Map<String, dynamic>? _testResult;

  @override
  void initState() {
    super.initState();
    _urlController = TextEditingController(text: widget.syncService.apiService.baseUrl);
  }

  @override
  void dispose() {
    _urlController.dispose();
    super.dispose();
  }

  Future<void> _testConnection() async {
    final url = _urlController.text.trim();
    if (url.isEmpty) return;

    setState(() {
      _isTesting = true;
      _testResult = null;
    });

    final res = await widget.syncService.apiService.testConnection(url);

    if (mounted) {
      setState(() {
        _isTesting = false;
        _testResult = res;
      });
    }
  }

  Future<void> _saveAndConnect() async {
    final url = _urlController.text.trim();
    if (url.isEmpty) return;

    await widget.syncService.updateServerUrl(url);

    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            widget.syncService.isOnline
                ? 'Connected to server: $url'
                : 'Server URL saved. Server is currently offline.',
          ),
          backgroundColor: widget.syncService.isOnline ? Colors.green.shade700 : Colors.amber.shade800,
          behavior: SnackBarBehavior.floating,
        ),
      );

      widget.onServerChanged?.call();
      Navigator.of(context).pop();
    }
  }

  void _applyPreset(String presetUrl) {
    setState(() {
      _urlController.text = presetUrl;
      _testResult = null;
    });
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      title: const Row(
        children: [
          Icon(Icons.dns, color: Color(0xFF6366F1)),
          SizedBox(width: 8),
          Text('Server Details', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        ],
      ),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Enter the backend FastAPI server URL to connect from your device:',
              style: TextStyle(fontSize: 13, color: Colors.black87),
            ),
            const SizedBox(height: 14),

            // URL input field
            TextField(
              controller: _urlController,
              keyboardType: TextInputType.url,
              autocorrect: false,
              decoration: InputDecoration(
                labelText: 'Server Base URL',
                hintText: 'http://192.168.1.50:8000',
                prefixIcon: const Icon(Icons.link),
                suffixIcon: IconButton(
                  icon: const Icon(Icons.clear, size: 18),
                  onPressed: () => _urlController.clear(),
                ),
                border: const OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 10),

            // Quick Preset Chips
            const Text(
              'Quick Presets:',
              style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Colors.grey),
            ),
            const SizedBox(height: 6),
            Wrap(
              spacing: 6,
              runSpacing: 4,
              children: [
                ActionChip(
                  label: const Text('Localhost (:8000)', style: TextStyle(fontSize: 11)),
                  avatar: const Icon(Icons.computer, size: 14),
                  onPressed: () => _applyPreset('http://localhost:8000'),
                ),
                ActionChip(
                  label: const Text('Android Emulator (10.0.2.2)', style: TextStyle(fontSize: 11)),
                  avatar: const Icon(Icons.phone_android, size: 14),
                  onPressed: () => _applyPreset('http://10.0.2.2:8000'),
                ),
                ActionChip(
                  label: const Text('Wi-Fi IP Prefix', style: TextStyle(fontSize: 11)),
                  avatar: const Icon(Icons.wifi, size: 14),
                  onPressed: () => _applyPreset('http://192.168.1.:8000'),
                ),
              ],
            ),
            const SizedBox(height: 14),

            // Test Connection Button & Indicator
            Row(
              children: [
                OutlinedButton.icon(
                  onPressed: _isTesting ? null : _testConnection,
                  icon: _isTesting
                      ? const SizedBox(width: 14, height: 14, child: CircularProgressIndicator(strokeWidth: 2))
                      : const Icon(Icons.network_check, size: 16),
                  label: const Text('Test Connection'),
                ),
              ],
            ),

            if (_testResult != null) ...[
              const SizedBox(height: 10),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                decoration: BoxDecoration(
                  color: (_testResult!['success'] == true) ? Colors.green.shade50 : Colors.red.shade50,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(
                    color: (_testResult!['success'] == true) ? Colors.green.shade300 : Colors.red.shade300,
                  ),
                ),
                child: Row(
                  children: [
                    Icon(
                      (_testResult!['success'] == true) ? Icons.check_circle : Icons.error_outline,
                      color: (_testResult!['success'] == true) ? Colors.green.shade700 : Colors.red.shade700,
                      size: 18,
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        _testResult!['message']?.toString() ?? '',
                        style: TextStyle(
                          fontSize: 12,
                          color: (_testResult!['success'] == true) ? Colors.green.shade900 : Colors.red.shade900,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],

            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: Colors.grey.shade100,
                borderRadius: BorderRadius.circular(6),
              ),
              child: const Text(
                '💡 Tip: On physical iPhone / Android devices connected to your home/office Wi-Fi, use your computer\'s IP address (e.g. http://192.168.1.x:8000).',
                style: TextStyle(fontSize: 11, color: Colors.black54),
              ),
            ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('Cancel'),
        ),
        ElevatedButton(
          style: ElevatedButton.styleFrom(
            backgroundColor: const Color(0xFF6366F1),
            foregroundColor: Colors.white,
          ),
          onPressed: _saveAndConnect,
          child: const Text('Save & Connect'),
        ),
      ],
    );
  }
}
