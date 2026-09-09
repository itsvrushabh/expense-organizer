import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../models/expense_summary.dart';
import '../models/queue_item.dart';
import '../services/sync_service.dart';
import 'add_expense_screen.dart';
import 'queue_screen.dart';
import 'widgets/expense_tile.dart';
import 'widgets/period_selector.dart';
import 'widgets/status_indicator.dart';
import 'widgets/summary_card.dart';

class ExpensesScreen extends StatefulWidget {
  final SyncService syncService;

  const ExpensesScreen({super.key, required this.syncService});

  @override
  State<ExpensesScreen> createState() => _ExpensesScreenState();
}

class _ExpensesScreenState extends State<ExpensesScreen> {
  PeriodType _period = PeriodType.day;
  DateTime _selectedDate = DateTime.now();

  bool _isLoading = false;
  String? _errorMessage;
  ExpenseSummary _summary = ExpenseSummary.empty;

  @override
  void initState() {
    super.initState();
    widget.syncService.addListener(_onSyncStateChanged);
    _loadExpenses();
  }

  @override
  void dispose() {
    widget.syncService.removeListener(_onSyncStateChanged);
    super.dispose();
  }

  void _onSyncStateChanged() {
    // When sync completes or connectivity changes, reload if mounted
    if (mounted) {
      setState(() {});
    }
  }

  Future<void> _loadExpenses() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final api = widget.syncService.apiService;
      ExpenseSummary summary;

      switch (_period) {
        case PeriodType.day:
          final dateStr = DateFormat('yyyy-MM-dd').format(_selectedDate);
          summary = await api.fetchDayExpenses(dateStr);
          break;
        case PeriodType.week:
          final week = PeriodSelector.isoWeekNumber(_selectedDate);
          summary = await api.fetchWeekExpenses(_selectedDate.year, week);
          break;
        case PeriodType.month:
          summary = await api.fetchMonthExpenses(_selectedDate.year, _selectedDate.month);
          break;
        case PeriodType.year:
          summary = await api.fetchYearExpenses(_selectedDate.year);
          break;
      }

      if (mounted) {
        setState(() {
          _summary = summary;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _errorMessage = e.toString();
          _isLoading = false;
        });
      }
    }
  }

  bool _itemMatchesPeriod(String dateStr) {
    final parsed = DateTime.tryParse(dateStr);
    if (parsed == null) return false;

    switch (_period) {
      case PeriodType.day:
        return parsed.year == _selectedDate.year &&
            parsed.month == _selectedDate.month &&
            parsed.day == _selectedDate.day;
      case PeriodType.week:
        final week = PeriodSelector.isoWeekNumber(_selectedDate);
        final itemWeek = PeriodSelector.isoWeekNumber(parsed);
        return parsed.year == _selectedDate.year && itemWeek == week;
      case PeriodType.month:
        return parsed.year == _selectedDate.year && parsed.month == _selectedDate.month;
      case PeriodType.year:
        return parsed.year == _selectedDate.year;
    }
  }

  List<QueueItem> _getMatchingPendingItems() {
    return widget.syncService.queueItems
        .where((item) => (item.isPending || item.isFailed) && _itemMatchesPeriod(item.date))
        .toList();
  }

  void _showSettingsDialog() {
    final controller = TextEditingController(text: widget.syncService.apiService.baseUrl);

    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Server Configuration'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Specify the backend FastAPI server URL:',
              style: TextStyle(fontSize: 13),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: controller,
              decoration: const InputDecoration(
                labelText: 'API URL',
                hintText: 'http://localhost:8000',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              'Tip: For Android emulator use http://10.0.2.2:8000. For physical phone use your machine IP: http://192.168.x.x:8000',
              style: TextStyle(fontSize: 11, color: Colors.grey),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () {
              final newUrl = controller.text.trim();
              if (newUrl.isNotEmpty) {
                widget.syncService.apiService.baseUrl = newUrl;
                widget.syncService.checkConnectivity();
                _loadExpenses();
              }
              Navigator.of(ctx).pop();
            },
            child: const Text('Save & Reconnect'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final matchingPending = _getMatchingPendingItems();
    final pendingTotal = matchingPending.fold<double>(0.0, (sum, i) => sum + i.amount);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Expense Organizer'),
        actions: [
          IconButton(
            icon: const Icon(Icons.dns_outlined),
            tooltip: 'Server Settings',
            onPressed: _showSettingsDialog,
          ),
          IconButton(
            icon: Badge(
              isLabelVisible: widget.syncService.pendingCount > 0,
              label: Text('${widget.syncService.pendingCount}'),
              child: const Icon(Icons.cloud_sync_outlined),
            ),
            tooltip: 'Queue Manager',
            onPressed: () {
              Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (_) => QueueScreen(syncService: widget.syncService),
                ),
              );
            },
          ),
        ],
      ),
      body: Column(
        children: [
          // Online / Offline Status Bar
          StatusIndicator(syncService: widget.syncService),

          // Period Selector (Day / Week / Month / Year)
          PeriodSelector(
            period: _period,
            selectedDate: _selectedDate,
            onPeriodChanged: (newPeriod) {
              setState(() => _period = newPeriod);
              _loadExpenses();
            },
            onDateChanged: (newDate) {
              setState(() => _selectedDate = newDate);
              _loadExpenses();
            },
          ),

          // Summary Card (Total Amount & Count)
          SummaryCard(
            serverTotal: _summary.total,
            serverCount: _summary.count,
            pendingTotal: pendingTotal,
            pendingCount: matchingPending.length,
          ),

          // Expenses List
          Expanded(
            child: RefreshIndicator(
              onRefresh: () async {
                await widget.syncService.checkConnectivity();
                await _loadExpenses();
              },
              child: _buildExpensesList(matchingPending),
            ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () async {
          final added = await Navigator.of(context).push<bool>(
            MaterialPageRoute(
              builder: (_) => AddExpenseScreen(
                syncService: widget.syncService,
                onExpenseAdded: _loadExpenses,
              ),
            ),
          );
          if (added == true) {
            _loadExpenses();
          }
        },
        icon: const Icon(Icons.add),
        label: const Text('Add Expense'),
      ),
    );
  }

  Widget _buildExpensesList(List<QueueItem> matchingPending) {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    if (_errorMessage != null && !widget.syncService.isOnline && matchingPending.isEmpty) {
      return ListView(
        children: [
          const SizedBox(height: 40),
          Center(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                children: [
                  Icon(Icons.cloud_off, size: 56, color: Colors.grey.shade400),
                  const SizedBox(height: 12),
                  const Text(
                    'Server is offline',
                    style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Expenses saved while offline are stored in the queue and will push once connected.',
                    textAlign: TextAlign.center,
                    style: TextStyle(color: Colors.grey.shade600),
                  ),
                  const SizedBox(height: 16),
                  ElevatedButton.icon(
                    onPressed: () {
                      widget.syncService.checkConnectivity();
                      _loadExpenses();
                    },
                    icon: const Icon(Icons.refresh),
                    label: const Text('Retry Connection'),
                  ),
                ],
              ),
            ),
          ),
        ],
      );
    }

    final serverExpenses = _summary.expenses;
    if (serverExpenses.isEmpty && matchingPending.isEmpty) {
      return ListView(
        children: const [
          SizedBox(height: 60),
          Center(
            child: Column(
              children: [
                Icon(Icons.receipt_long_outlined, size: 56, color: Colors.grey),
                SizedBox(height: 12),
                Text(
                  'No expenses recorded for this period',
                  style: TextStyle(fontSize: 16, color: Colors.grey),
                ),
                SizedBox(height: 6),
                Text(
                  'Tap "+ Add Expense" to record a transaction.',
                  style: TextStyle(fontSize: 13, color: Colors.grey),
                ),
              ],
            ),
          ),
        ],
      );
    }

    return ListView(
      padding: const EdgeInsets.only(bottom: 80, top: 4),
      children: [
        // Pending Queue Items for this period
        if (matchingPending.isNotEmpty) ...[
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 6),
            child: Row(
              children: [
                Icon(Icons.access_time_filled, size: 14, color: Colors.amber.shade900),
                const SizedBox(width: 6),
                Text(
                  'PENDING SYNC (${matchingPending.length})',
                  style: TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.bold,
                    letterSpacing: 1.0,
                    color: Colors.amber.shade900,
                  ),
                ),
              ],
            ),
          ),
          ...matchingPending.map(
            (item) => ExpenseTile(
              description: item.description,
              amount: item.amount,
              category: item.category,
              date: item.date,
              isPending: item.isPending,
              isFailed: item.isFailed,
              errorText: item.lastError,
            ),
          ),
          const Divider(indent: 16, endIndent: 16, height: 20),
        ],

        // Server Confirmed Items
        if (serverExpenses.isNotEmpty) ...[
          if (matchingPending.isNotEmpty)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 4),
              child: Text(
                'CONFIRMED ON SERVER (${serverExpenses.length})',
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 1.0,
                  color: Colors.grey.shade600,
                ),
              ),
            ),
          ...serverExpenses.map(
            (exp) => ExpenseTile(
              description: exp.description,
              amount: exp.amount,
              category: exp.category,
              date: exp.date,
            ),
          ),
        ],
      ],
    );
  }
}
