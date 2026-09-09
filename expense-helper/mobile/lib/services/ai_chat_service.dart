import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import '../models/chat_models.dart';

class AIChatResponse {
  final String sessionId;
  final String message;
  final String status;
  final ExpenseDraft? draft;
  final String actionRequired;
  final int? savedExpenseId;

  AIChatResponse({
    required this.sessionId,
    required this.message,
    required this.status,
    this.draft,
    required this.actionRequired,
    this.savedExpenseId,
  });

  factory AIChatResponse.fromJson(Map<String, dynamic> json) {
    return AIChatResponse(
      sessionId: json['session_id'] as String? ?? '',
      message: json['message'] as String? ?? '',
      status: json['status'] as String? ?? 'idle',
      draft: json['draft'] != null ? ExpenseDraft.fromJson(json['draft'] as Map<String, dynamic>) : null,
      actionRequired: json['action_required'] as String? ?? 'none',
      savedExpenseId: json['saved_expense_id'] as int?,
    );
  }
}

class AIChatService {
  static final AIChatService _instance = AIChatService._internal();
  factory AIChatService() => _instance;
  AIChatService._internal() {
    _initDefaultUrl();
  }

  late String baseUrl;

  void _initDefaultUrl() {
    try {
      if (Platform.isAndroid) {
        baseUrl = 'http://10.0.2.2:18001';
      } else {
        baseUrl = 'http://127.0.0.1:18001';
      }
    } catch (_) {
      baseUrl = 'http://127.0.0.1:18001';
    }
  }

  void updateBaseUrl(String newUrl) {
    baseUrl = newUrl.replaceAll(RegExp(r'/+$'), '');
  }

  Future<AIChatResponse> sendMessage(String message, String sessionId) async {
    final uri = Uri.parse('$baseUrl/api/chat/message');
    final res = await http.post(
      uri,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'message': message,
        'session_id': sessionId,
      }),
    ).timeout(const Duration(seconds: 20));

    if (res.statusCode == 200) {
      final data = jsonDecode(utf8.decode(res.bodyBytes)) as Map<String, dynamic>;
      return AIChatResponse.fromJson(data);
    } else {
      throw Exception('Server returned ${res.statusCode}: ${res.body}');
    }
  }

  Future<AIChatResponse> confirmDraft(String sessionId) async {
    final uri = Uri.parse('$baseUrl/api/chat/confirm');
    final res = await http.post(
      uri,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'session_id': sessionId,
      }),
    ).timeout(const Duration(seconds: 15));

    if (res.statusCode == 200) {
      final data = jsonDecode(utf8.decode(res.bodyBytes)) as Map<String, dynamic>;
      return AIChatResponse.fromJson(data);
    } else {
      throw Exception('Failed to confirm draft: ${res.statusCode}');
    }
  }

  Future<AIChatResponse> cancelDraft(String sessionId) async {
    final uri = Uri.parse('$baseUrl/api/chat/cancel');
    final res = await http.post(
      uri,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'session_id': sessionId,
      }),
    ).timeout(const Duration(seconds: 10));

    if (res.statusCode == 200) {
      final data = jsonDecode(utf8.decode(res.bodyBytes)) as Map<String, dynamic>;
      return AIChatResponse.fromJson(data);
    } else {
      throw Exception('Failed to cancel draft: ${res.statusCode}');
    }
  }

  Future<Map<String, dynamic>> checkHealth() async {
    final uri = Uri.parse('$baseUrl/health');
    final res = await http.get(uri).timeout(const Duration(seconds: 5));
    if (res.statusCode == 200) {
      return jsonDecode(utf8.decode(res.bodyBytes)) as Map<String, dynamic>;
    }
    throw Exception('Healthcheck failed: ${res.statusCode}');
  }
}
