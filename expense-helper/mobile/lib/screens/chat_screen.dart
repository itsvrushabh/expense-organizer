import 'package:flutter/material.dart';
import '../models/chat_models.dart';
import '../services/ai_chat_service.dart';
import '../widgets/chat_bubble.dart';

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final TextEditingController _textController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final List<ChatMessage> _messages = [];
  final String _sessionId = 'session_${DateTime.now().millisecondsSinceEpoch}';
  bool _isLoading = false;
  bool _isBackendReachable = true;

  @override
  void initState() {
    super.initState();
    _checkBackendStatus();
    _sendWelcomeMessage();
  }

  void _sendWelcomeMessage() {
    _messages.add(
      ChatMessage(
        id: 'msg_welcome',
        text: '👋 Hi! I am your AI Expense Helper. Tell me about any expense, for example:\n'
            '• "Spent \$45 on groceries today"\n'
            '• "Paid \$14 for lunch with team yesterday"\n'
            '• "Uber ride \$22"\n\n'
            'I will parse the details and ask for your confirmation before adding it to the database!',
        isUser: false,
        timestamp: DateTime.now(),
      ),
    );
  }

  Future<void> _checkBackendStatus() async {
    try {
      await AIChatService().checkHealth();
      if (mounted) setState(() => _isBackendReachable = true);
    } catch (_) {
      if (mounted) setState(() => _isBackendReachable = false);
    }
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent + 60,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  Future<void> _handleSubmitted(String text) async {
    final trimmed = text.trim();
    if (trimmed.isEmpty || _isLoading) return;

    _textController.clear();

    final userMsg = ChatMessage(
      id: 'msg_${DateTime.now().millisecondsSinceEpoch}',
      text: trimmed,
      isUser: true,
      timestamp: DateTime.now(),
    );

    final loadingMsgId = 'loading_${DateTime.now().millisecondsSinceEpoch}';
    final loadingMsg = ChatMessage(
      id: loadingMsgId,
      text: '',
      isUser: false,
      timestamp: DateTime.now(),
      isLoading: true,
    );

    setState(() {
      _messages.add(userMsg);
      _messages.add(loadingMsg);
      _isLoading = true;
    });
    _scrollToBottom();

    try {
      final response = await AIChatService().sendMessage(trimmed, _sessionId);
      if (mounted) {
        setState(() {
          _messages.removeWhere((m) => m.id == loadingMsgId);
          _messages.add(
            ChatMessage(
              id: 'resp_${DateTime.now().millisecondsSinceEpoch}',
              text: response.message,
              isUser: false,
              timestamp: DateTime.now(),
              draft: response.draft,
              actionRequired: response.actionRequired,
              savedExpenseId: response.savedExpenseId,
            ),
          );
          _isLoading = false;
          _isBackendReachable = true;
        });
        _scrollToBottom();
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _messages.removeWhere((m) => m.id == loadingMsgId);
          _messages.add(
            ChatMessage(
              id: 'err_${DateTime.now().millisecondsSinceEpoch}',
              text: '⚠️ Could not connect to AI backend: $e\n'
                  'Please check that aibackend is running on ${AIChatService().baseUrl}',
              isUser: false,
              timestamp: DateTime.now(),
            ),
          );
          _isLoading = false;
          _isBackendReachable = false;
        });
        _scrollToBottom();
      }
    }
  }

  Future<void> _handleConfirmDraft() async {
    if (_isLoading) return;
    setState(() => _isLoading = true);

    try {
      final response = await AIChatService().confirmDraft(_sessionId);
      if (mounted) {
        setState(() {
          _messages.add(
            ChatMessage(
              id: 'confirm_${DateTime.now().millisecondsSinceEpoch}',
              text: response.message,
              isUser: false,
              timestamp: DateTime.now(),
              savedExpenseId: response.savedExpenseId,
            ),
          );
          _isLoading = false;
        });
        _scrollToBottom();
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _messages.add(
            ChatMessage(
              id: 'err_confirm_${DateTime.now().millisecondsSinceEpoch}',
              text: '⚠️ Confirmation failed: $e',
              isUser: false,
              timestamp: DateTime.now(),
            ),
          );
          _isLoading = false;
        });
        _scrollToBottom();
      }
    }
  }

  Future<void> _handleCancelDraft() async {
    if (_isLoading) return;
    setState(() => _isLoading = true);

    try {
      final response = await AIChatService().cancelDraft(_sessionId);
      if (mounted) {
        setState(() {
          _messages.add(
            ChatMessage(
              id: 'cancel_${DateTime.now().millisecondsSinceEpoch}',
              text: response.message,
              isUser: false,
              timestamp: DateTime.now(),
            ),
          );
          _isLoading = false;
        });
        _scrollToBottom();
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _messages.add(
            ChatMessage(
              id: 'err_cancel_${DateTime.now().millisecondsSinceEpoch}',
              text: '⚠️ Cancel failed: $e',
              isUser: false,
              timestamp: DateTime.now(),
            ),
          );
          _isLoading = false;
        });
        _scrollToBottom();
      }
    }
  }

  void _showSettingsDialog() {
    final urlController = TextEditingController(text: AIChatService().baseUrl);
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('AI Backend Connection'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Set the host and port of the aibackend service:',
              style: TextStyle(fontSize: 13),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: urlController,
              decoration: const InputDecoration(
                border: OutlineInputBorder(),
                labelText: 'Server Base URL',
                hintText: 'http://10.0.2.2:8001 or http://localhost:8001',
              ),
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              children: [
                ActionChip(
                  label: const Text('Android (10.0.2.2)'),
                  onPressed: () => urlController.text = 'http://10.0.2.2:8001',
                ),
                ActionChip(
                  label: const Text('Localhost (127.0.0.1)'),
                  onPressed: () => urlController.text = 'http://127.0.0.1:8001',
                ),
              ],
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () {
              AIChatService().updateBaseUrl(urlController.text.trim());
              _checkBackendStatus();
              Navigator.pop(ctx);
            },
            child: const Text('Save'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(6),
              decoration: BoxDecoration(
                color: theme.colorScheme.primaryContainer,
                shape: BoxShape.circle,
              ),
              child: Icon(Icons.smart_toy, size: 20, color: theme.colorScheme.primary),
            ),
            const SizedBox(width: 10),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Expense Helper',
                  style: TextStyle(fontSize: 17, fontWeight: FontWeight.bold),
                ),
                Row(
                  children: [
                    Container(
                      width: 8,
                      height: 8,
                      decoration: BoxDecoration(
                        color: _isBackendReachable ? Colors.green : Colors.orange,
                        shape: BoxShape.circle,
                      ),
                    ),
                    const SizedBox(width: 5),
                    Text(
                      _isBackendReachable ? 'AI Connected' : 'AI Offline',
                      style: TextStyle(
                        fontSize: 11,
                        color: _isBackendReachable ? Colors.green : Colors.orange,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.settings_outlined),
            tooltip: 'Server Connection Settings',
            onPressed: _showSettingsDialog,
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Clear Chat',
            onPressed: () {
              setState(() {
                _messages.clear();
                _sendWelcomeMessage();
              });
            },
          ),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: [
            // Message List
            Expanded(
              child: ListView.builder(
                controller: _scrollController,
                padding: const EdgeInsets.symmetric(vertical: 12),
                itemCount: _messages.length,
                itemBuilder: (context, index) {
                  final message = _messages[index];
                  return ChatBubble(
                    message: message,
                    onConfirm: _handleConfirmDraft,
                    onCancel: _handleCancelDraft,
                    onSuggestionTap: (suggestion) => _handleSubmitted(suggestion),
                  );
                },
              ),
            ),

            // Starter Quick Chips (when only welcome message is visible)
            if (_messages.length <= 1)
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                child: SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: Row(
                    children: [
                      _buildQuickPromptChip('Spent \$45 on groceries today'),
                      const SizedBox(width: 8),
                      _buildQuickPromptChip('Paid \$12.50 for coffee at Starbucks'),
                      const SizedBox(width: 8),
                      _buildQuickPromptChip('Uber ride \$28 yesterday'),
                      const SizedBox(width: 8),
                      _buildQuickPromptChip('Internet bill \$60'),
                    ],
                  ),
                ),
              ),

            // Input Row
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              decoration: BoxDecoration(
                color: theme.colorScheme.surface,
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withValues(alpha: 0.05),
                    offset: const Offset(0, -2),
                    blurRadius: 4,
                  ),
                ],
              ),
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _textController,
                      textCapitalization: TextCapitalization.sentences,
                      enabled: !_isLoading,
                      decoration: InputDecoration(
                        hintText: 'e.g. Spent 35 on pizza today...',
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(24),
                          borderSide: BorderSide(color: theme.dividerColor),
                        ),
                        contentPadding: const EdgeInsets.symmetric(
                          horizontal: 18,
                          vertical: 10,
                        ),
                        filled: true,
                        fillColor: theme.colorScheme.surfaceContainerHighest.withValues(alpha: 0.3),
                      ),
                      onSubmitted: _handleSubmitted,
                    ),
                  ),
                  const SizedBox(width: 8),
                  IconButton.filled(
                    onPressed: _isLoading
                        ? null
                        : () => _handleSubmitted(_textController.text),
                    icon: const Icon(Icons.send),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildQuickPromptChip(String prompt) {
    return ActionChip(
      avatar: const Icon(Icons.bolt, size: 14, color: Colors.amber),
      label: Text(prompt, style: const TextStyle(fontSize: 12)),
      onPressed: () => _handleSubmitted(prompt),
    );
  }
}
