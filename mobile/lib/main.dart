import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:autopieces_pro/core/theme/app_theme.dart';
import 'package:autopieces_pro/features/auth/presentation/screens/welcome_screen.dart';
import 'package:autopieces_pro/core/localization/language_controller.dart';
import 'package:autopieces_pro/core/theme/font_controller.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: Listenable.merge([LanguageController(), FontController()]),
      builder: (context, _) {
        return MaterialApp(
          title: 'BSG Auto Parts',
          debugShowCheckedModeBanner: false,
          theme: AppTheme.getTheme(FontController().currentFont),
          locale: LanguageController().currentLocale,
          supportedLocales: const [
            Locale('fr'),
            Locale('en'),
            Locale('ar'),
            Locale('zh'),
          ],
          localizationsDelegates: const [
            GlobalMaterialLocalizations.delegate,
            GlobalWidgetsLocalizations.delegate,
            GlobalCupertinoLocalizations.delegate,
          ],
          home: const WelcomeScreen(),
        );
      },
    );
  }
}
