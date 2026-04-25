import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:autopieces_pro/core/localization/language_controller.dart';
import 'package:autopieces_pro/core/theme/font_controller.dart';
import 'package:autopieces_pro/core/theme/app_theme.dart';

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundColor,
      appBar: AppBar(
        title: Text(LanguageController().translate('settings')),
        elevation: 0,
      ),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          _buildSectionHeader("Localisation"),
          _buildLanguageSelector(),
          const SizedBox(height: 30),
          _buildSectionHeader("Apparence"),
          _buildFontSelector(),
          const SizedBox(height: 30),
          _buildSectionHeader("Compte"),
          _buildSettingsItem(
            icon: Icons.notifications_none_rounded,
            title: "Notifications",
            onTap: () {},
          ),
          _buildSettingsItem(
            icon: Icons.security_rounded,
            title: "Sécurité",
            onTap: () {},
          ),
          const SizedBox(height: 40),
          ElevatedButton(
            onPressed: () => Navigator.pop(context),
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.grey[200],
              foregroundColor: Colors.black87,
              elevation: 0,
            ),
            child: const Text("RETOUR"),
          ),
        ],
      ),
    );
  }

  Widget _buildSectionHeader(String title) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 15, left: 5),
      child: Text(
        title.toUpperCase(),
        style: GoogleFonts.outfit(
          fontSize: 12,
          fontWeight: FontWeight.bold,
          color: AppTheme.primaryColor,
          letterSpacing: 1.2,
        ),
      ),
    );
  }

  Widget _buildSettingsItem({
    required IconData icon,
    required String title,
    required VoidCallback onTap,
  }) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
      ),
      child: ListTile(
        leading: Icon(icon, color: Colors.black87, size: 20),
        title: Text(
          title,
          style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w500),
        ),
        trailing: const Icon(Icons.chevron_right_rounded, size: 20),
        onTap: onTap,
      ),
    );
  }

  Widget _buildLanguageSelector() {
    return ListenableBuilder(
      listenable: LanguageController(),
      builder: (context, _) {
        final currentCode = LanguageController().currentLocale.languageCode;
        return GridView.count(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          crossAxisCount: 2,
          crossAxisSpacing: 10,
          mainAxisSpacing: 10,
          childAspectRatio: 2.5,
          children: ['fr', 'en', 'ar', 'zh'].map((code) {
            final isSelected = currentCode == code;
            return GestureDetector(
              onTap: () => LanguageController().changeLanguage(code),
              child: Container(
                decoration: BoxDecoration(
                  color: isSelected ? AppTheme.primaryColor : Colors.white,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(
                    color: isSelected
                        ? AppTheme.primaryColor
                        : Colors.grey.withValues(alpha: 0.2),
                    width: 2,
                  ),
                  boxShadow: isSelected
                      ? [
                          BoxShadow(
                            color: AppTheme.primaryColor.withValues(alpha: 0.3),
                            blurRadius: 8,
                            offset: const Offset(0, 4),
                          ),
                        ]
                      : null,
                ),
                alignment: Alignment.center,
                child: Text(
                  LanguageController().getLanguageName(code),
                  style: GoogleFonts.outfit(
                    fontSize: 14,
                    fontWeight: isSelected ? FontWeight.bold : FontWeight.w500,
                    color: isSelected ? Colors.white : Colors.black87,
                  ),
                ),
              ),
            );
          }).toList(),
        );
      },
    );
  }

  Widget _buildFontSelector() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
      ),
      child: ListenableBuilder(
        listenable: FontController(),
        builder: (context, _) {
          return DropdownButtonHideUnderline(
            child: DropdownButton<String>(
              value: FontController().currentFont,
              isExpanded: true,
              items: ['Outfit', 'Roboto', 'Open Sans', 'Lato'].map((font) {
                return DropdownMenuItem(
                  value: font,
                  child: Text(font, style: GoogleFonts.getFont(font)),
                );
              }).toList(),
              onChanged: (font) {
                if (font != null) FontController().changeFont(font);
              },
            ),
          );
        },
      ),
    );
  }
}
