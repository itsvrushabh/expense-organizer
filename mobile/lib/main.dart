import 'package:flutter/material.dart';
import 'services/sync_service.dart';
import 'views/web_style_app_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  final syncService = SyncService();
  await syncService.initialize();

  runApp(ExpenseOrganizerMobileApp(syncService: syncService));
}

class ExpenseOrganizerMobileApp extends StatelessWidget {
  final SyncService syncService;

  const ExpenseOrganizerMobileApp({super.key, required this.syncService});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Expense Organizer',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF6366F1), // Indigo
          brightness: Brightness.light,
        ),
        appBarTheme: const AppBarTheme(
          centerTitle: false,
          elevation: 0,
        ),
        cardTheme: CardThemeData(
          elevation: 0,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
          ),
        ),
      ),
      home: WebStyleAppScreen(syncService: syncService),
    );
  }
}
