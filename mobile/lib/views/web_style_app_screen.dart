import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../models/expense.dart';
import '../models/queue_item.dart';
import '../services/sync_service.dart';
import '../utils/currency.dart';
import 'day_excel_view.dart';
import 'excel_grid_view.dart';
import 'grid_6x6_view.dart';
import 'queue_screen.dart';
import 'server_settings_dialog.dart';

class WebStyleAppScreen extends StatefulWidget {
  final SyncService syncService;

  const WebStyleAppScreen({super.key, required this.syncService});

  @override
  State<WebStyleAppScreen> createState() => _WebStyleAppScreenState();
}

class _WebStyleAppScreenState extends State<WebStyleAppScreen> {
  String _viewMode = 'month'; // 'day', 'week', 'month', 'year'
  DateTime _selectedDate = DateTime.now();
  AppCurrency _currency = AppCurrency.inr;

  List<Expense> _expenses = [];
  bool _isLoading = false;
  String? _errorMessage;

  // Add Expense inline form controllers
  final _descController = TextEditingController();
  final _amountController = TextEditingController();
  final _catController = TextEditingController();
  final _dateController = TextEditingController(
    text: DateFormat('yyyy-MM-dd').format(DateTime.now()),
  );
  bool _isAdding = false;

  // Toggle between heatmap grid and spreadsheet table for month/year
  bool _showTableForMonthYear = false;

  @override
  void initState() {
    super.initState();
    widget.syncService.addListener(_onSyncChanged);
    _fetchExpenses();
  }

  @override
  void dispose() {
    widget.syncService.removeListener(_onSyncChanged);
    _descController.dispose();
    _amountController.dispose();
    _catController.dispose();
    _dateController.dispose();
    super.dispose();
  }

  void _onSyncChanged() {
    if (mounted) setState(() {});
  }

  Future<void> _fetchExpenses() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final api = widget.syncService.apiService;
      List<Expense> list = [];

      if (_viewMode == 'day') {
        final dateStr = DateFormat('yyyy-MM-dd').format(_selectedDate);
        final summary = await api.fetchDayExpenses(dateStr);
        list = summary.expenses;
      } else if (_viewMode == 'week') {
        final dateStr = DateFormat('yyyy-MM-dd').format(_selectedDate);
        final summary = await api.fetchWeekByDateExpenses(
          dateStr,
          startSunday: true,
        );
        list = summary.expenses;
      } else if (_viewMode == 'month') {
        final summary = await api.fetchMonthExpenses(
          _selectedDate.year,
          _selectedDate.month,
        );
        list = summary.expenses;
      } else {
        // year
        final summary = await api.fetchYearExpenses(_selectedDate.year);
        list = summary.expenses;
      }

      if (mounted) {
        setState(() {
          _expenses = list;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _errorMessage = widget.syncService.isOnline
              ? 'Could not load expenses: $e'
              : null;
          _isLoading = false;
        });
      }
    }
  }

  void _stepDate(int delta) {
    setState(() {
      if (_viewMode == 'day') {
        _selectedDate = _selectedDate.add(Duration(days: delta));
      } else if (_viewMode == 'week') {
        _selectedDate = _selectedDate.add(Duration(days: 7 * delta));
      } else if (_viewMode == 'month') {
        _selectedDate = DateTime(
          _selectedDate.year,
          _selectedDate.month + delta,
          1,
        );
      } else {
        _selectedDate = DateTime(_selectedDate.year + delta, 1, 1);
      }
      _dateController.text = DateFormat('yyyy-MM-dd').format(_selectedDate);
    });
    _fetchExpenses();
  }

  Future<void> _addExpense() async {
    final desc = _descController.text.trim();
    final cat = _catController.text.trim();
    final rawAmount = double.tryParse(_amountController.text.trim());
    final date = _dateController.text.trim();

    if (desc.isEmpty ||
        cat.isEmpty ||
        date.isEmpty ||
        rawAmount == null ||
        rawAmount <= 0) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please fill all fields with valid data')),
      );
      return;
    }

    setState(() => _isAdding = true);

    try {
      final baseAmount = _currency.toBase(rawAmount);
      final res = await widget.syncService.addExpense(
        description: desc,
        amount: baseAmount,
        category: cat,
        date: date,
      );

      _descController.clear();
      _amountController.clear();
      _catController.clear();

      if (mounted) {
        final isQueued = res['status'] == 'queued';
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              isQueued
                  ? 'Offline: Expense queued locally.'
                  : 'Expense added successfully!',
            ),
            backgroundColor: isQueued
                ? Colors.amber.shade800
                : Colors.green.shade700,
          ),
        );
      }

      await _fetchExpenses();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error adding expense: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _isAdding = false);
    }
  }

  Future<void> _updateExpense(
    int id,
    String desc,
    double baseAmount,
    String cat,
    String date,
  ) async {
    try {
      await widget.syncService.apiService.updateExpense(
        id,
        description: desc,
        amount: baseAmount,
        category: cat,
        date: date,
      );
      await _fetchExpenses();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error updating expense: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  Future<void> _deleteExpense(int id) async {
    try {
      await widget.syncService.apiService.deleteExpense(id);
      await _fetchExpenses();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error deleting expense: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  List<QueueItem> _filterPendingExpenses() {
    return widget.syncService.queueItems.where((item) {
      if (!item.isPending && !item.isFailed) return false;
      final d = DateTime.tryParse(item.date);
      if (d == null) return false;

      if (_viewMode == 'day') {
        return d.year == _selectedDate.year &&
            d.month == _selectedDate.month &&
            d.day == _selectedDate.day;
      } else if (_viewMode == 'week') {
        final start = _selectedDate.subtract(
          Duration(days: _selectedDate.weekday % 7),
        );
        final startDate = DateTime(start.year, start.month, start.day);
        final endDate = startDate.add(const Duration(days: 7));
        return (d.isAfter(startDate) || d.isAtSameMomentAs(startDate)) &&
            d.isBefore(endDate);
      } else if (_viewMode == 'month') {
        return d.year == _selectedDate.year && d.month == _selectedDate.month;
      } else {
        return d.year == _selectedDate.year;
      }
    }).toList();
  }

  @override
  Widget build(BuildContext context) {
    final pending = _filterPendingExpenses();
    final isOnline = widget.syncService.isOnline;
    final totalPendingCount = widget.syncService.pendingCount;

    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: () async {
            await widget.syncService.checkConnectivity();
            await _fetchExpenses();
          },
          child: SingleChildScrollView(
            physics: const AlwaysScrollableScrollPhysics(),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // ============ Gradient Web-Style Header ============
                Container(
                  padding: const EdgeInsets.fromLTRB(20, 20, 20, 24),
                  decoration: const BoxDecoration(
                    gradient: LinearGradient(
                      colors: [
                        Color(0xFF6366F1), // indigo
                        Color(0xFF8B5CF6), // purple
                        Color(0xFFD946EF), // fuchsia
                        Color(0xFFEC4899), // pink
                      ],
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                    ),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black26,
                        blurRadius: 16,
                        offset: Offset(0, 6),
                      ),
                    ],
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Top Row: Title & Actions
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          const Expanded(
                            child: Text(
                              'Expense Organizer',
                              style: TextStyle(
                                color: Colors.white,
                                fontSize: 22,
                                fontWeight: FontWeight.w900,
                                letterSpacing: -0.5,
                              ),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                          const SizedBox(width: 8),
                          Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              // Currency Selector
                              Container(
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 8,
                                  vertical: 2,
                                ),
                                decoration: BoxDecoration(
                                  color: Colors.white.withValues(alpha: 0.22),
                                  borderRadius: BorderRadius.circular(8),
                                  border: Border.all(
                                    color: Colors.white.withValues(alpha: 0.5),
                                  ),
                                ),
                                child: DropdownButtonHideUnderline(
                                  child: DropdownButton<AppCurrency>(
                                    value: _currency,
                                    dropdownColor: const Color(0xFF312E81),
                                    icon: const Icon(
                                      Icons.arrow_drop_down,
                                      color: Colors.white,
                                      size: 18,
                                    ),
                                    style: const TextStyle(
                                      color: Colors.white,
                                      fontWeight: FontWeight.bold,
                                      fontSize: 13,
                                    ),
                                    selectedItemBuilder: (context) {
                                      return AppCurrency.values.map((c) {
                                        return Center(
                                          child: Text(
                                            '${c.symbol} ${c.code}',
                                            style: const TextStyle(
                                              color: Colors.white,
                                              fontWeight: FontWeight.bold,
                                              fontSize: 13,
                                            ),
                                          ),
                                        );
                                      }).toList();
                                    },
                                    items: AppCurrency.values.map((c) {
                                      return DropdownMenuItem(
                                        value: c,
                                        child: Text('🌍 ${c.label}'),
                                      );
                                    }).toList(),
                                    onChanged: (val) {
                                      if (val != null)
                                        setState(() => _currency = val);
                                    },
                                  ),
                                ),
                              ),
                              const SizedBox(width: 8),
                              // Server Settings Button
                              IconButton(
                                constraints: const BoxConstraints(),
                                padding: EdgeInsets.zero,
                                icon: const Icon(
                                  Icons.dns_outlined,
                                  color: Colors.white,
                                  size: 22,
                                ),
                                tooltip: 'Server Details',
                                onPressed: () {
                                  ServerSettingsDialog.show(
                                    context,
                                    widget.syncService,
                                    onServerChanged: _fetchExpenses,
                                  );
                                },
                              ),
                              const SizedBox(width: 8),
                              // Queue Badge / Sync Button
                              IconButton(
                                constraints: const BoxConstraints(),
                                padding: EdgeInsets.zero,
                                icon: Badge(
                                  isLabelVisible: totalPendingCount > 0,
                                  label: Text('$totalPendingCount'),
                                  backgroundColor: Colors.amber.shade400,
                                  textColor: Colors.black87,
                                  child: const Icon(
                                    Icons.cloud_sync_outlined,
                                    color: Colors.white,
                                    size: 26,
                                  ),
                                ),
                                tooltip: 'Sync Queue',
                                onPressed: () {
                                  Navigator.of(context).push(
                                    MaterialPageRoute(
                                      builder: (_) => QueueScreen(
                                        syncService: widget.syncService,
                                        currency: _currency,
                                      ),
                                    ),
                                  );
                                },
                              ),
                            ],
                          ),
                        ],
                      ),
                      const SizedBox(height: 18),

                      // View Selector Pills: [Day] [Week] [Month] [Year]
                      SingleChildScrollView(
                        scrollDirection: Axis.horizontal,
                        child: Row(
                          children: ['day', 'week', 'month', 'year'].map((
                            mode,
                          ) {
                            final isActive = _viewMode == mode;
                            return Padding(
                              padding: const EdgeInsets.only(right: 8),
                              child: InkWell(
                                onTap: () {
                                  setState(() => _viewMode = mode);
                                  _fetchExpenses();
                                },
                                borderRadius: BorderRadius.circular(20),
                                child: Container(
                                  padding: const EdgeInsets.symmetric(
                                    horizontal: 16,
                                    vertical: 8,
                                  ),
                                  decoration: BoxDecoration(
                                    color: isActive
                                        ? Colors.white
                                        : Colors.white.withValues(alpha: 0.18),
                                    borderRadius: BorderRadius.circular(20),
                                    boxShadow: isActive
                                        ? [
                                            BoxShadow(
                                              color: Colors.black.withValues(
                                                alpha: 0.15,
                                              ),
                                              blurRadius: 6,
                                            ),
                                          ]
                                        : null,
                                  ),
                                  child: Text(
                                    mode[0].toUpperCase() + mode.substring(1),
                                    style: TextStyle(
                                      color: isActive
                                          ? const Color(0xFF4F46E5)
                                          : Colors.white,
                                      fontWeight: FontWeight.bold,
                                      fontSize: 13,
                                    ),
                                  ),
                                ),
                              ),
                            );
                          }).toList(),
                        ),
                      ),
                      const SizedBox(height: 14),

                      // Date Navigator Row: [◀] [ Date Input / Picker ] [▶]
                      Row(
                        children: [
                          IconButton(
                            visualDensity: VisualDensity.compact,
                            icon: const Icon(
                              Icons.arrow_left,
                              color: Colors.white,
                              size: 26,
                            ),
                            onPressed: () => _stepDate(-1),
                          ),
                          Expanded(
                            child: InkWell(
                              onTap: () async {
                                final picked = await showDatePicker(
                                  context: context,
                                  initialDate: _selectedDate,
                                  firstDate: DateTime(2020),
                                  lastDate: DateTime(2060),
                                );
                                if (picked != null) {
                                  setState(() {
                                    _selectedDate = picked;
                                    _dateController.text = DateFormat(
                                      'yyyy-MM-dd',
                                    ).format(picked);
                                  });
                                  _fetchExpenses();
                                }
                              },
                              child: Container(
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 8,
                                  vertical: 8,
                                ),
                                decoration: BoxDecoration(
                                  color: Colors.white.withValues(alpha: 0.2),
                                  borderRadius: BorderRadius.circular(8),
                                  border: Border.all(
                                    color: Colors.white.withValues(alpha: 0.4),
                                  ),
                                ),
                                child: Row(
                                  mainAxisAlignment: MainAxisAlignment.center,
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    const Icon(
                                      Icons.calendar_month,
                                      color: Colors.white,
                                      size: 16,
                                    ),
                                    const SizedBox(width: 6),
                                    Flexible(
                                      child: Text(
                                        DateFormat('yyyy-MM-dd')
                                            .format(_selectedDate),
                                        style: const TextStyle(
                                          color: Colors.white,
                                          fontWeight: FontWeight.bold,
                                        ),
                                        overflow: TextOverflow.ellipsis,
                                        maxLines: 1,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ),
                          ),
                          IconButton(
                            visualDensity: VisualDensity.compact,
                            icon: const Icon(
                              Icons.arrow_right,
                              color: Colors.white,
                              size: 26,
                            ),
                            onPressed: () => _stepDate(1),
                          ),
                          TextButton(
                            style: TextButton.styleFrom(
                              foregroundColor: Colors.white,
                              visualDensity: VisualDensity.compact,
                              padding: const EdgeInsets.symmetric(
                                horizontal: 8,
                              ),
                            ),
                            onPressed: () {
                              setState(() {
                                _selectedDate = DateTime.now();
                                _dateController.text = DateFormat('yyyy-MM-dd')
                                    .format(DateTime.now());
                              });
                              _fetchExpenses();
                            },
                            child: const Text(
                              'Today',
                              style: TextStyle(fontWeight: FontWeight.bold),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),

                // ============ Server Connection Pill Banner ============
                InkWell(
                  onTap: () {
                    ServerSettingsDialog.show(
                      context,
                      widget.syncService,
                      onServerChanged: _fetchExpenses,
                    );
                  },
                  child: Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 16,
                      vertical: 8,
                    ),
                    color: isOnline
                        ? (totalPendingCount > 0
                              ? Colors.amber.shade50
                              : Colors.green.shade50)
                        : Colors.deepOrange.shade50,
                    child: Row(
                      children: [
                        Container(
                          width: 8,
                          height: 8,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            color: isOnline ? Colors.green : Colors.deepOrange,
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Row(
                            children: [
                              Flexible(
                                child: Text(
                                  isOnline
                                      ? 'Online: ${widget.syncService.apiService.baseUrl}'
                                      : 'Offline: Tap to edit server',
                                  style: TextStyle(
                                    fontSize: 12,
                                    fontWeight: FontWeight.bold,
                                    color: isOnline
                                        ? Colors.green.shade800
                                        : Colors.deepOrange.shade900,
                                  ),
                                  overflow: TextOverflow.ellipsis,
                                ),
                              ),
                              const SizedBox(width: 4),
                              Icon(
                                Icons.edit,
                                size: 13,
                                color: isOnline
                                    ? Colors.green.shade700
                                    : Colors.deepOrange.shade700,
                              ),
                            ],
                          ),
                        ),
                        if (widget
                            .syncService
                            .rustBridge
                            .isNativeAvailable) ...[
                          Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 6,
                              vertical: 2,
                            ),
                            decoration: BoxDecoration(
                              color: Colors.deepPurple.shade50,
                              borderRadius: BorderRadius.circular(4),
                              border: Border.all(
                                color: Colors.deepPurple.shade200,
                              ),
                            ),
                            child: const Text(
                              '⚡ Rust Engine',
                              style: TextStyle(
                                fontSize: 10,
                                fontWeight: FontWeight.bold,
                                color: Colors.deepPurple,
                              ),
                            ),
                          ),
                          const SizedBox(width: 8),
                        ],
                        if (totalPendingCount > 0)
                          Text(
                            '$totalPendingCount queued',
                            style: TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.bold,
                              color: Colors.amber.shade900,
                            ),
                          ),
                      ],
                    ),
                  ),
                ),

                if (_errorMessage != null)
                  Container(
                    margin: const EdgeInsets.all(16),
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: const Color(0xFFFEF2F2),
                      border: Border.all(color: const Color(0xFFFECACA)),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Row(
                      children: [
                        Expanded(
                          child: Text(
                            _errorMessage!,
                            style: const TextStyle(
                              color: Color(0xFF9B1C1C),
                              fontSize: 13,
                            ),
                          ),
                        ),
                        TextButton(
                          onPressed: () {
                            ServerSettingsDialog.show(
                              context,
                              widget.syncService,
                              onServerChanged: _fetchExpenses,
                            );
                          },
                          child: const Text(
                            'Edit Server',
                            style: TextStyle(fontWeight: FontWeight.bold),
                          ),
                        ),
                      ],
                    ),
                  ),

                // ============ Add Expense Form (Day View) ============
                if (_viewMode == 'day') ...[
                  Container(
                    margin: const EdgeInsets.all(16),
                    padding: const EdgeInsets.all(18),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(12),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black.withValues(alpha: 0.04),
                          blurRadius: 8,
                          offset: const Offset(0, 2),
                        ),
                      ],
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'Add New Expense',
                          style: TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                            color: Color(0xFF1E293B),
                          ),
                        ),
                        const SizedBox(height: 14),
                        TextField(
                          controller: _descController,
                          decoration: const InputDecoration(
                            hintText: 'Description',
                            contentPadding: EdgeInsets.symmetric(
                              horizontal: 12,
                              vertical: 10,
                            ),
                            border: OutlineInputBorder(),
                          ),
                        ),
                        const SizedBox(height: 10),
                        Row(
                          children: [
                            Expanded(
                              child: TextField(
                                controller: _amountController,
                                keyboardType:
                                    const TextInputType.numberWithOptions(
                                      decimal: true,
                                    ),
                                decoration: InputDecoration(
                                  hintText: 'Amount (${_currency.symbol})',
                                  contentPadding: const EdgeInsets.symmetric(
                                    horizontal: 12,
                                    vertical: 10,
                                  ),
                                  border: const OutlineInputBorder(),
                                ),
                              ),
                            ),
                            const SizedBox(width: 10),
                            Expanded(
                              child: TextField(
                                controller: _catController,
                                decoration: const InputDecoration(
                                  hintText: 'Category',
                                  contentPadding: EdgeInsets.symmetric(
                                    horizontal: 12,
                                    vertical: 10,
                                  ),
                                  border: OutlineInputBorder(),
                                ),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 10),
                        Row(
                          children: [
                            Expanded(
                              child: TextField(
                                controller: _dateController,
                                decoration: const InputDecoration(
                                  hintText: 'Date (YYYY-MM-DD)',
                                  contentPadding: EdgeInsets.symmetric(
                                    horizontal: 12,
                                    vertical: 10,
                                  ),
                                  border: OutlineInputBorder(),
                                ),
                              ),
                            ),
                            const SizedBox(width: 10),
                            ElevatedButton(
                              style: ElevatedButton.styleFrom(
                                backgroundColor: const Color(0xFF4F46E5),
                                foregroundColor: Colors.white,
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 20,
                                  vertical: 12,
                                ),
                                shape: RoundedRectangleBorder(
                                  borderRadius: BorderRadius.circular(8),
                                ),
                              ),
                              onPressed: _isAdding ? null : _addExpense,
                              child: _isAdding
                                  ? const SizedBox(
                                      width: 18,
                                      height: 18,
                                      child: CircularProgressIndicator(
                                        strokeWidth: 2,
                                        color: Colors.white,
                                      ),
                                    )
                                  : const Text(
                                      'Add Expense',
                                      style: TextStyle(
                                        fontWeight: FontWeight.bold,
                                      ),
                                    ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ],

                // ============ View Mode Toggle for Month / Year ============
                if (_viewMode == 'month' || _viewMode == 'year')
                  Padding(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 16,
                      vertical: 4,
                    ),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Expanded(
                          child: Text(
                            _showTableForMonthYear
                                ? 'Spreadsheet Table View'
                                : 'Spend Grid Heatmap',
                            style: const TextStyle(
                              fontWeight: FontWeight.bold,
                              fontSize: 13,
                              color: Color(0xFF64748B),
                            ),
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                        TextButton.icon(
                          onPressed: () => setState(
                            () => _showTableForMonthYear =
                                !_showTableForMonthYear,
                          ),
                          icon: Icon(
                            _showTableForMonthYear
                                ? Icons.grid_view
                                : Icons.table_chart,
                            size: 16,
                          ),
                          label: Text(
                            _showTableForMonthYear
                                ? 'Switch to Grid'
                                : 'Switch to Table',
                          ),
                        ),
                      ],
                    ),
                  ),

                // ============ Content Container ============
                if (_isLoading)
                  const Padding(
                    padding: EdgeInsets.all(40),
                    child: Center(child: CircularProgressIndicator()),
                  )
                else if (_viewMode == 'day')
                  DayExcelView(
                    expenses: _expenses,
                    pendingExpenses: pending,
                    currency: _currency,
                    onUpdate: _updateExpense,
                    onDelete: _deleteExpense,
                  )
                else if (_viewMode == 'week')
                  ExcelGridView(
                    expenses: _expenses,
                    pendingExpenses: pending,
                    selectedDate: _selectedDate,
                    mode: 'week',
                    currency: _currency,
                  )
                else if (_showTableForMonthYear)
                  ExcelGridView(
                    expenses: _expenses,
                    pendingExpenses: pending,
                    selectedDate: _selectedDate,
                    mode: _viewMode,
                    currency: _currency,
                  )
                else
                  Grid6x6View(
                    expenses: _expenses,
                    pendingExpenses: pending,
                    selectedDate: _selectedDate,
                    mode: _viewMode,
                    currency: _currency,
                  ),

                const SizedBox(height: 80),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
