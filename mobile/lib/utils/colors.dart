import 'package:flutter/material.dart';

final Map<String, double> _hueCache = {};

int _hashString(String value) {
  int hash = 0;
  for (int i = 0; i < value.length; i++) {
    hash = (hash * 31 + value.codeUnitAt(i)) & 0x7fffffff;
  }
  return hash;
}

double categoryHue(String category) {
  final cached = _hueCache[category];
  if (cached != null) return cached;
  final hue = (_hashString(category.toLowerCase()) * 137.508) % 360;
  _hueCache[category] = hue;
  return hue;
}

class CategoryColor {
  final Color bg;
  final Color fg;

  const CategoryColor({required this.bg, required this.fg});
}

CategoryColor categoryColor(String category) {
  final hue = categoryHue(category);
  final bg = HSLColor.fromAHSL(1.0, hue, 0.85, 0.93).toColor();
  final fg = HSLColor.fromAHSL(1.0, hue, 0.70, 0.30).toColor();
  return CategoryColor(bg: bg, fg: fg);
}
