import 'package:get/get.dart';
import '../modules/auth/views/login_view.dart';
import '../modules/auth/views/register_view.dart';
import '../modules/auth/bindings/auth_binding.dart';
import '../modules/dashboard/views/dashboard_view.dart';
import '../modules/dashboard/bindings/dashboard_binding.dart';
import '../modules/ai_assistant/views/ai_assistant_view.dart';
import '../modules/ai_assistant/bindings/ai_assistant_binding.dart';
import '../modules/settings/views/settings_view.dart';
import '../modules/settings/bindings/settings_binding.dart';
import '../modules/user_management/views/user_management_view.dart';
import '../modules/user_management/bindings/user_management_binding.dart';
import '../middlewares/auth_middleware.dart';
import 'app_routes.dart';

class AppPages {
  static const initial = AppRoutes.login;

  static final routes = [
    GetPage(
      name: AppRoutes.login,
      page: () => const LoginView(),
      binding: AuthBinding(),
    ),
    GetPage(
      name: AppRoutes.register,
      page: () => const RegisterView(),
      binding: AuthBinding(),
    ),
    GetPage(
      name: AppRoutes.dashboard,
      page: () => const DashboardView(),
      binding: DashboardBinding(),
      middlewares: [AuthMiddleware()],
    ),
    GetPage(
      name: AppRoutes.aiAssistant,
      page: () => const AiAssistantView(),
      binding: AiAssistantBinding(),
      middlewares: [AuthMiddleware()],
    ),
    GetPage(
      name: AppRoutes.settings,
      page: () => const SettingsView(),
      binding: SettingsBinding(),
      middlewares: [AuthMiddleware()],
    ),
    GetPage(
      name: AppRoutes.userManagement,
      page: () => const UserManagementView(),
      binding: UserManagementBinding(),
      middlewares: [AuthMiddleware()],
    ),
  ];
}
