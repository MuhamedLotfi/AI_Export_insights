import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'app/routes/app_pages.dart';
import 'core/theme/app_theme.dart';
import 'app/data/services/log_service.dart';
import 'app/data/services/api_service.dart';
import 'app/services/auth_service.dart';
import 'app/controllers/theme_controller.dart';

void main() async {
  // Ensure Flutter binding is initialized
  WidgetsFlutterBinding.ensureInitialized();

  // Initialize services in correct order
  Get.put(LogService());
  
  // Register ApiService (must be before AuthService)
  Get.put(ApiService());
  
  // Initialize ThemeController for dark/light mode
  Get.put(ThemeController());
  
  // Initialize AuthService for authentication and await it
  // This ensures token is loaded before run app
  final authService = await Get.putAsync(() => AuthService().init());
  
  final logger = LogService.instance;
  logger.info('Application starting', source: 'Main');
  
  // Load user theme preference after auth
  if (authService.isAuthenticated.value) {
    Get.find<ThemeController>().loadUserTheme();
  }
  
  // Determine the correct initial route based on auth state
  String initialRoute = AppPages.initial;
  if (authService.isAuthenticated.value) {
     initialRoute = authService.getInitialRoute();
  }
  
  runApp(MyApp(initialRoute: initialRoute));
}

class MyApp extends StatelessWidget {
  final String initialRoute;
  
  const MyApp({Key? key, required this.initialRoute}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return GetX<ThemeController>(
      builder: (themeController) {
        return GetMaterialApp(
          title: 'AI Export Insights',
          theme: AppTheme.lightTheme,
          darkTheme: AppTheme.darkTheme,
          themeMode: themeController.currentThemeMode,
          debugShowCheckedModeBanner: false,
          initialRoute: initialRoute,
          getPages: AppPages.routes,
        );
      },
    );
  }
}
