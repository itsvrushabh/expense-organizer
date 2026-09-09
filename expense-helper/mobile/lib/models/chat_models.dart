class ExpenseDraft {
  final String description;
  final double amount;
  final String category;
  final String date;

  ExpenseDraft({
    required this.description,
    required this.amount,
    required this.category,
    required this.date,
  });

  factory ExpenseDraft.fromJson(Map<String, dynamic> json) {
    return ExpenseDraft(
      description: json['description'] as String? ?? 'Expense',
      amount: (json['amount'] as num?)?.toDouble() ?? 0.0,
      category: json['category'] as String? ?? 'Other',
      date: json['date'] as String? ?? '',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'description': description,
      'amount': amount,
      'category': category,
      'date': date,
    };
  }

  ExpenseDraft copyWith({
    String? description,
    double? amount,
    String? category,
    String? date,
  }) {
    return ExpenseDraft(
      description: description ?? this.description,
      amount: amount ?? this.amount,
      category: category ?? this.category,
      date: date ?? this.date,
    );
  }
}

class ChatMessage {
  final String id;
  final String text;
  final bool isUser;
  final DateTime timestamp;
  final ExpenseDraft? draft;
  final String? actionRequired; // 'confirm', 'clarify', 'none'
  final int? savedExpenseId;
  final bool isLoading;

  ChatMessage({
    required this.id,
    required this.text,
    required this.isUser,
    required this.timestamp,
    this.draft,
    this.actionRequired,
    this.savedExpenseId,
    this.isLoading = false,
  });

  ChatMessage copyWith({
    String? text,
    ExpenseDraft? draft,
    String? actionRequired,
    int? savedExpenseId,
    bool? isLoading,
  }) {
    return ChatMessage(
      id: id,
      text: text ?? this.text,
      isUser: isUser,
      timestamp: timestamp,
      draft: draft ?? this.draft,
      actionRequired: actionRequired ?? this.actionRequired,
      savedExpenseId: savedExpenseId ?? this.savedExpenseId,
      isLoading: isLoading ?? this.isLoading,
    );
  }
}
