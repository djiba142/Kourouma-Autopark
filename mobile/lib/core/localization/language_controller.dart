import 'package:flutter/material.dart';

class LanguageController extends ChangeNotifier {
  static final LanguageController _instance = LanguageController._internal();
  factory LanguageController() => _instance;
  LanguageController._internal();

  Locale _currentLocale = const Locale('fr'); // Défaut: Français

  Locale get currentLocale => _currentLocale;

  final Map<String, Map<String, String>> _translations = {
    'fr': {
      'dashboard': 'Tableau de Bord',
      'journal': 'Journal Financier',
      'payments': 'Paiements',
      'expenses': 'Dépenses',
      'profit': 'Profit Net',
      'stock': 'Stock Global',
      'settings': 'Paramètres',
      'language': 'Langue',
      'font': 'Police',
      'lang_fr': 'Français',
      'lang_en': 'English',
      'lang_ar': 'العربية',
      'lang_zh': '中文',
    },
    'en': {
      'dashboard': 'Dashboard',
      'journal': 'Financial Journal',
      'payments': 'Payments',
      'expenses': 'Expenses',
      'profit': 'Net Profit',
      'stock': 'Global Stock',
      'settings': 'Settings',
      'language': 'Language',
      'font': 'Font',
      'lang_fr': 'French',
      'lang_en': 'English',
      'lang_ar': 'Arabic',
      'lang_zh': 'Chinese',
    },
    'ar': {
      'dashboard': 'لوحة القيادة',
      'journal': 'السجل المالي',
      'payments': 'المدفوعات',
      'expenses': 'المصاريف',
      'profit': 'صافي الربح',
      'stock': 'المخزون العالمي',
      'settings': 'الإعدادات',
      'language': 'اللغة',
      'font': 'الخط',
      'lang_fr': 'الفرنسية',
      'lang_en': 'الإنجليزية',
      'lang_ar': 'العربية',
      'lang_zh': 'الصينية',
    },
    'zh': {
      'dashboard': '仪表板',
      'journal': '财务日志',
      'payments': '支付',
      'expenses': '支出',
      'profit': '净利润',
      'stock': '全球库存',
      'settings': '设置',
      'language': '语言',
      'font': '字体',
      'lang_fr': '法语',
      'lang_en': '英语',
      'lang_ar': '阿拉伯语',
      'lang_zh': '中文',
    },
  };

  String translate(String key) {
    return _translations[_currentLocale.languageCode]?[key] ?? key;
  }

  String getLanguageName(String code) {
    return _translations[_currentLocale.languageCode]?['lang_$code'] ?? code;
  }

  void changeLanguage(String languageCode) {
    _currentLocale = Locale(languageCode);
    notifyListeners();
  }
}
