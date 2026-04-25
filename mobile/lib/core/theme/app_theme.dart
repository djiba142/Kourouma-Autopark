import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class AppTheme {
  // Couleurs de la charte BSG Auto-Parts
  static const Color primaryColor = Color(0xFF5D3A9B); // Violet Améthyste
  static const Color primaryLightColor = Color(0xFF7D5BB6);
  static const Color backgroundColor = Color(
    0xFFF1F3F6,
  ); // Fond gris-blanc moderne
  static const Color surfaceColor = Color(0xFFFFFFFF); // Blanc pur
  static const Color accentColor = Color(0xFFD4AF37); // Or
  static const Color errorColor = Color(0xFFB71C1C);
  static const Color successColor = Color(0xFF1B5E20);
  static const Color warningColor = Color(0xFFE65100);

  /// Génère le thème complet avec une police dynamique
  static ThemeData getTheme(String fontName) {
    // On récupère le TextTheme de base de la police demandée
    TextTheme baseTextTheme;
    try {
      baseTextTheme = GoogleFonts.getTextTheme(fontName);
    } catch (e) {
      baseTextTheme = GoogleFonts.outfitTextTheme();
    }

    return ThemeData(
      useMaterial3: true,
      scaffoldBackgroundColor: backgroundColor,
      colorScheme: ColorScheme.fromSeed(
        seedColor: primaryColor,
        brightness: Brightness.light,
        primary: primaryColor,
        secondary: accentColor,
        surface: surfaceColor,
        error: errorColor,
        onPrimary: Colors.white,
        onSecondary: Colors.black,
        onSurface: Colors.black87,
        onError: Colors.white,
      ),
      textTheme: baseTextTheme.copyWith(
        displayLarge: GoogleFonts.getFont(
          fontName,
          fontSize: 32,
          fontWeight: FontWeight.bold,
          color: primaryColor,
        ),
        headlineMedium: GoogleFonts.getFont(
          fontName,
          fontSize: 24,
          fontWeight: FontWeight.bold,
          color: Colors.black87,
          letterSpacing: -0.5,
        ),
        titleMedium: GoogleFonts.getFont(
          fontName,
          fontSize: 18,
          fontWeight: FontWeight.w600,
          color: Colors.black87,
        ),
        bodyLarge: GoogleFonts.getFont(
          fontName,
          fontSize: 16,
          color: Colors.black87,
        ),
        bodyMedium: GoogleFonts.getFont(
          fontName,
          fontSize: 14,
          color: Colors.black54,
        ),
        bodySmall: GoogleFonts.getFont(
          fontName,
          fontSize: 13,
          color: Colors.grey,
        ),
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: Colors.transparent,
        foregroundColor: Colors.black87,
        elevation: 0,
        centerTitle: true,
        titleTextStyle: TextStyle(
          fontSize: 20,
          fontWeight: FontWeight.bold,
          color: Colors.black87,
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: primaryColor,
          foregroundColor: Colors.white,
          minimumSize: const Size(double.infinity, 56),
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
          textStyle: GoogleFonts.getFont(
            fontName,
            fontSize: 18,
            fontWeight: FontWeight.bold,
          ),
          elevation: 2,
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: surfaceColor,
        contentPadding: const EdgeInsets.symmetric(
          horizontal: 20,
          vertical: 20,
        ),
        hintStyle: const TextStyle(color: Colors.black45, fontSize: 16),
        labelStyle: const TextStyle(
          color: primaryColor,
          fontWeight: FontWeight.bold,
        ),
        prefixIconColor: primaryColor,
        suffixIconColor: primaryColor,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: BorderSide.none,
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: BorderSide.none,
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: const BorderSide(color: primaryColor, width: 2),
        ),
      ),
    );
  }

  // Pour compatibilité descendante
  static ThemeData get lightTheme => getTheme('Outfit');
}
