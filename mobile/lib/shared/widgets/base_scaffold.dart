import 'package:flutter/material.dart';
import 'package:autopieces_pro/core/theme/app_theme.dart';

class BaseScaffold extends StatelessWidget {
  final String title;
  final Widget body;
  final List<Widget>? actions;
  final Widget? floatingActionButton;
  final Widget? bottomNavigationBar;
  final Widget? drawer;
  final bool showLogoBackground;

  const BaseScaffold({
    super.key,
    required this.title,
    required this.body,
    this.actions,
    this.floatingActionButton,
    this.bottomNavigationBar,
    this.drawer,
    this.showLogoBackground = true,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      extendBodyBehindAppBar: true,
      appBar: AppBar(
        title: Text(title, style: const TextStyle(fontWeight: FontWeight.bold)),
        centerTitle: true,
        actions: actions,
        backgroundColor: Colors.transparent,
      ),
      drawer: drawer,
      body: Stack(
        children: [
          // Background - Deep Black
          Positioned.fill(child: Container(color: AppTheme.backgroundColor)),
          
          // Subtle Watermark Logo
          if (showLogoBackground)
            Positioned(
              bottom: -150,
              right: -150,
              child: Opacity(
                opacity: 0.05,
                child: Image.asset(
                  'assets/images/bsg_logo.png',
                  width: 500,
                  height: 500,
                  fit: BoxFit.contain,
                  errorBuilder: (context, error, stackTrace) => const SizedBox(),
                ),
              ),
            ),
            
          // Main Content
          SafeArea(child: body),
        ],
      ),
      floatingActionButton: floatingActionButton,
      bottomNavigationBar: bottomNavigationBar,
    );
  }
}
