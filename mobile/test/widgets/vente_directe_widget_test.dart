import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:autopieces_pro/features/commandes/presentation/screens/vente_directe_screen.dart';
import 'package:autopieces_pro/core/theme/app_theme.dart';

void main() {
  testWidgets('L\'écran VenteDirecte affiche l\'état initial correct', (
    WidgetTester tester,
  ) async {
    // Build our screen inside a MaterialApp
    await tester.pumpWidget(
      MaterialApp(theme: AppTheme.lightTheme, home: const VenteDirecteScreen()),
    );

    // Vérification du titre
    expect(find.text('Vente au Comptoir'), findsOneWidget);

    // Vérification de l'état panier vide
    expect(find.text('Le panier est vide'), findsOneWidget);
    expect(find.byIcon(Icons.shopping_basket_outlined), findsOneWidget);

    // Le bouton de scan doit avoir été supprimé
    expect(find.text('Scanner un article'), findsNothing);
    expect(find.byIcon(Icons.qr_code_scanner), findsNothing);
  });
}
