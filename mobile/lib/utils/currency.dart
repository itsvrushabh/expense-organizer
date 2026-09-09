enum AppCurrency {
  usd('USD', '\$', 1.0, 'USD (\$)'),
  inr('INR', '₹', 84.0, 'INR (₹)'),
  cny('CNY', '¥', 7.2, 'CNY (¥)');

  final String code;
  final String symbol;
  final double rate;
  final String label;

  const AppCurrency(this.code, this.symbol, this.rate, this.label);

  double toBase(double amount) => amount / rate;

  double fromBase(double amount) => amount * rate;

  String format(double? amount) {
    if (amount == null) return '-';
    final converted = amount * rate;
    return '$symbol${converted.toStringAsFixed(2)}';
  }
}
