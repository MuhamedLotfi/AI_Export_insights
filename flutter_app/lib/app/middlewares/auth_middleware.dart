import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../services/auth_service.dart';
import '../routes/app_routes.dart';

class AuthMiddleware extends GetMiddleware {
  @override
  RouteSettings? redirect(String? route) {
    final authService = Get.find<AuthService>();
    
    // If not authenticated, redirect to login
    if (!authService.isAuthenticated.value) {
      return const RouteSettings(name: AppRoutes.login);
    }
    
    return null;
  }
}
