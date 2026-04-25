import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class FontController extends ChangeNotifier {
  static final FontController _instance = FontController._internal();
  factory FontController() => _instance;
  FontController._internal();

  String _currentFont = 'Outfit';

  String get currentFont => _currentFont;

  void changeFont(String fontName) {
    _currentFont = fontName;
    notifyListeners();
  }

  TextStyle getTextStyle(TextStyle baseStyle) {
    try {
      return GoogleFonts.getFont(_currentFont, textStyle: baseStyle);
    } catch (e) {
      return GoogleFonts.outfit(textStyle: baseStyle);
    }
  }
}
