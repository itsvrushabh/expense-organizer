class QueueItem {
  final String id;
  final String description;
  final double amount;
  final String category;
  final String date;
  final String status;
  final int retryCount;
  final String createdAt;
  final String? lastError;

  const QueueItem({
    required this.id,
    required this.description,
    required this.amount,
    required this.category,
    required this.date,
    required this.status,
    required this.retryCount,
    required this.createdAt,
    this.lastError,
  });

  factory QueueItem.fromJson(Map<String, dynamic> json) {
    return QueueItem(
      id: json['id'] as String? ?? '',
      description: json['description'] as String? ?? '',
      amount: (json['amount'] as num?)?.toDouble() ?? 0.0,
      category: json['category'] as String? ?? 'General',
      date: json['date'] as String? ?? '',
      status: json['status'] as String? ?? 'pending',
      retryCount: json['retry_count'] as int? ?? 0,
      createdAt: json['created_at'] as String? ?? '',
      lastError: json['last_error'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'description': description,
      'amount': amount,
      'category': category,
      'date': date,
      'status': status,
      'retry_count': retryCount,
      'created_at': createdAt,
      if (lastError != null) 'last_error': lastError,
    };
  }

  bool get isPending => status == 'pending';
  bool get isFailed => status == 'failed';
  bool get isSynced => status == 'synced';
}
