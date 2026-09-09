import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import '../models/expense.dart';
import '../models/expense_summary.dart';

import 'package:shared_preferences/shared_preferences.dart';

class ApiService {
  static const String prefKey = 'expense_organizer_server_url';
  String baseUrl;

  ApiService({String? baseUrl})
      : baseUrl = baseUrl ?? _defaultBaseUrl;

  static String get _defaultBaseUrl {
    if (!kIsWeb && Platform.isAndroid) {
      // 10.0.2.2 is the host loopback IP in the standard Android emulator
      return 'http://10.0.2.2:8000';
    }
    return 'http://localhost:8000';
  }

  static String sanitizeUrl(String url) {
    var trimmed = url.trim();
    if (!trimmed.startsWith('http://') && !trimmed.startsWith('https://')) {
      trimmed = 'http://$trimmed';
    }
    return trimmed.replaceAll(RegExp(r'/+$'), '');
  }

  Future<void> loadSavedBaseUrl() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final saved = prefs.getString(prefKey);
      if (saved != null && saved.trim().isNotEmpty) {
        baseUrl = sanitizeUrl(saved);
        debugPrint('Loaded saved server URL: $baseUrl');
      }
    } catch (e) {
      debugPrint('Could not load saved server URL: $e');
    }
  }

  Future<void> updateBaseUrl(String newUrl) async {
    baseUrl = sanitizeUrl(newUrl);
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(prefKey, baseUrl);
      debugPrint('Persisted server URL: $baseUrl');
    } catch (e) {
      debugPrint('Could not save server URL: $e');
    }
  }

  String get _cleanBaseUrl => sanitizeUrl(baseUrl);

  Future<Map<String, dynamic>> testConnection([String? testUrl]) async {
    final target = sanitizeUrl(testUrl ?? baseUrl);
    try {
      final stopwatch = Stopwatch()..start();
      final uri = Uri.parse('$target/');
      final response = await http.get(uri).timeout(const Duration(seconds: 4));
      stopwatch.stop();

      if (response.statusCode >= 200 && response.statusCode < 300) {
        String msg = 'FastAPI server online';
        try {
          final json = jsonDecode(response.body);
          if (json is Map && json['message'] != null) {
            msg = json['message'].toString();
          }
        } catch (_) {}
        return {
          'success': true,
          'message': 'Connected: $msg (${stopwatch.elapsedMilliseconds}ms)',
          'status': response.statusCode,
        };
      } else {
        return {
          'success': false,
          'message': 'Server responded with HTTP ${response.statusCode}',
          'status': response.statusCode,
        };
      }
    } catch (e) {
      return {
        'success': false,
        'message': 'Connection failed: ${e.toString().replaceAll('Exception:', '').trim()}',
      };
    }
  }

  Future<bool> checkHealth({Duration timeout = const Duration(milliseconds: 2500)}) async {
    try {
      final uri = Uri.parse('$_cleanBaseUrl/');
      final response = await http.get(uri).timeout(timeout);
      return response.statusCode >= 200 && response.statusCode < 300;
    } catch (_) {
      return false;
    }
  }

  Future<ExpenseSummary> fetchAllExpenses() async {
    final uri = Uri.parse('$_cleanBaseUrl/expenses');
    final response = await http.get(uri).timeout(const Duration(seconds: 5));
    if (response.statusCode == 200) {
      final json = jsonDecode(response.body) as Map<String, dynamic>;
      return ExpenseSummary.fromJson(json);
    }
    throw HttpException('Failed to load expenses (${response.statusCode})');
  }

  Future<ExpenseSummary> fetchDayExpenses(String dateStr) async {
    final uri = Uri.parse('$_cleanBaseUrl/expenses/day/$dateStr');
    final response = await http.get(uri).timeout(const Duration(seconds: 5));
    if (response.statusCode == 200) {
      final json = jsonDecode(response.body) as Map<String, dynamic>;
      return ExpenseSummary.fromJson(json);
    }
    throw HttpException('Failed to load day expenses (${response.statusCode})');
  }

  Future<ExpenseSummary> fetchWeekExpenses(int year, int week) async {
    final uri = Uri.parse('$_cleanBaseUrl/expenses/week/$year/$week');
    final response = await http.get(uri).timeout(const Duration(seconds: 5));
    if (response.statusCode == 200) {
      final json = jsonDecode(response.body) as Map<String, dynamic>;
      return ExpenseSummary.fromJson(json);
    }
    throw HttpException('Failed to load week expenses (${response.statusCode})');
  }

  Future<ExpenseSummary> fetchWeekByDateExpenses(String dateStr, {bool startSunday = true}) async {
    final query = startSunday ? '?start_sunday=true' : '';
    final uri = Uri.parse('$_cleanBaseUrl/expenses/week/date/$dateStr$query');
    final response = await http.get(uri).timeout(const Duration(seconds: 5));
    if (response.statusCode == 200) {
      final json = jsonDecode(response.body) as Map<String, dynamic>;
      return ExpenseSummary.fromJson(json);
    }
    throw HttpException('Failed to load week expenses (${response.statusCode})');
  }

  Future<ExpenseSummary> fetchMonthExpenses(int year, int month) async {
    final uri = Uri.parse('$_cleanBaseUrl/expenses/month/$year/$month');
    final response = await http.get(uri).timeout(const Duration(seconds: 5));
    if (response.statusCode == 200) {
      final json = jsonDecode(response.body) as Map<String, dynamic>;
      return ExpenseSummary.fromJson(json);
    }
    throw HttpException('Failed to load month expenses (${response.statusCode})');
  }

  Future<ExpenseSummary> fetchYearExpenses(int year) async {
    final uri = Uri.parse('$_cleanBaseUrl/expenses/year/$year');
    final response = await http.get(uri).timeout(const Duration(seconds: 5));
    if (response.statusCode == 200) {
      final json = jsonDecode(response.body) as Map<String, dynamic>;
      return ExpenseSummary.fromJson(json);
    }
    throw HttpException('Failed to load year expenses (${response.statusCode})');
  }

  Future<Expense> createExpense({
    required String description,
    required double amount,
    required String category,
    required String date,
  }) async {
    final uri = Uri.parse('$_cleanBaseUrl/expenses');
    final payload = {
      'description': description,
      'amount': amount,
      'category': category,
      'date': date,
    };
    final response = await http.post(
      uri,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(payload),
    ).timeout(const Duration(seconds: 8));

    if (response.statusCode == 200 || response.statusCode == 201) {
      final json = jsonDecode(response.body) as Map<String, dynamic>;
      return Expense.fromJson(json);
    }
    throw HttpException('Failed to create expense: HTTP ${response.statusCode} - ${response.body}');
  }

  Future<Expense> updateExpense(
    int id, {
    required String description,
    required double amount,
    required String category,
    required String date,
  }) async {
    final uri = Uri.parse('$_cleanBaseUrl/expenses/$id');
    final payload = {
      'description': description,
      'amount': amount,
      'category': category,
      'date': date,
    };
    final response = await http.put(
      uri,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(payload),
    ).timeout(const Duration(seconds: 8));

    if (response.statusCode == 200) {
      final json = jsonDecode(response.body) as Map<String, dynamic>;
      return Expense.fromJson(json);
    }
    throw HttpException('Failed to update expense: HTTP ${response.statusCode}');
  }

  Future<void> deleteExpense(int id) async {
    final uri = Uri.parse('$_cleanBaseUrl/expenses/$id');
    final response = await http.delete(uri).timeout(const Duration(seconds: 8));
    if (response.statusCode != 200) {
      throw HttpException('Failed to delete expense: HTTP ${response.statusCode}');
    }
  }
}
