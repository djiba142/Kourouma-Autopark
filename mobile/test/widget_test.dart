import 'package:flutter_test/flutter_test.dart';
import 'package:autopieces_pro/main.dart';

void main() {
  testWidgets('App smoke test - WelcomeScreen shows correctly', (
    WidgetTester tester,
  ) async {
    // Build our app and trigger a frame.
    await tester.pumpWidget(const MyApp());

    // Verify that "BSG AUTO-PARTS" is displayed.
    expect(find.text('BSG AUTO-PARTS'), findsOneWidget);

    // Verify that "ACCÈS PROFESSIONNEL" button is displayed.
    expect(find.text('ACCÈS PROFESSIONNEL'), findsOneWidget);
  });
}
