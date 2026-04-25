import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:autopieces_pro/main.dart';
import 'package:autopieces_pro/features/auth/presentation/screens/login_screen.dart';
import 'package:autopieces_pro/features/dashboard/presentation/screens/dashboard_screen.dart';
import 'package:autopieces_pro/features/produits/presentation/screens/catalog_screen.dart';

void main() {
  testWidgets('Integration PRO MAX - Parcours Complet Welcome-Login-Catalogue', (
    WidgetTester tester,
  ) async {
    // Configuration de la taille de l'écran (API moderne)
    tester.view.physicalSize = const Size(1080, 1920);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.resetPhysicalSize);

    // 1. Lancement de l'application
    await tester.pumpWidget(const MyApp());
    expect(find.text('BSG AUTO-PARTS'), findsOneWidget);

    // 2. Navigation vers l'écran de Login
    final loginBtn = find.text('ACCÈS PROFESSIONNEL');
    await tester.ensureVisible(loginBtn);
    await tester.tap(loginBtn);
    await tester.pumpAndSettle();
    expect(find.byType(LoginScreen), findsOneWidget);

    // 3. Simulation de Connexion (Accès direct pour la démo)
    await tester.tap(find.text('SE CONNECTER'));
    await tester.pumpAndSettle();
    expect(find.byType(DashboardScreen), findsOneWidget);

    // 4. Test du changement de rôle (Switch vers Boutique pour voir les produits)
    await tester.tap(find.byIcon(Icons.switch_account_outlined));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Mode Boutique (Vente)'));
    await tester.pumpAndSettle();

    // 5. Accès au Catalogue Produits
    await tester.tap(find.text('Produits'));
    await tester.pumpAndSettle();
    expect(find.byType(CatalogScreen), findsOneWidget);

    // 6. Vérification de la liste des produits (Mocks intégrés)
    expect(find.byType(ListView), findsOneWidget);
    expect(find.text('Plaquettes de frein Avant'), findsOneWidget);

    // Test de recherche simple
    await tester.enterText(find.byType(TextField), 'Filtre');
    await tester.pumpAndSettle();
    expect(find.text('Plaquettes de frein Avant'), findsNothing);
    expect(find.text('Filtre à Huile Corolla'), findsOneWidget);
  });
}
