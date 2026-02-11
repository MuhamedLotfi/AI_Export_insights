import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../../../../config/api_config.dart';
import '../../../controllers/theme_controller.dart';
import '../../../data/services/api_service.dart';
import '../../../data/services/log_service.dart';
import '../../../services/auth_service.dart';

class SettingsController extends GetxController {
  final ApiService _apiService = Get.find<ApiService>();
  final AuthService _authService = Get.find<AuthService>();
  final ThemeController _themeController = Get.find<ThemeController>();
  final LogService _logger = LogService.instance;
  
  final RxBool isLoading = false.obs;
  
  // Settings
  final Rx<Map<String, dynamic>> settings = Rx<Map<String, dynamic>>({});
  final Rx<Map<String, dynamic>> aiConfig = Rx<Map<String, dynamic>>({});
  
  // Theme
  ThemeMode get currentTheme => _themeController.currentThemeMode;
  bool get isDarkMode => _themeController.isDarkMode;
  
  @override
  void onInit() {
    super.onInit();
    loadSettings();
    loadAiConfig();
  }
  
  Future<void> loadSettings() async {
    isLoading.value = true;
    
    try {
      final response = await _apiService.get(ApiConfig.settings);
      
      if (response.statusCode == 200) {
        settings.value = Map<String, dynamic>.from(response.data['settings'] ?? {});
        _logger.info('Settings loaded', source: 'Settings');
      }
    } catch (e) {
      _logger.error('Failed to load settings: $e', source: 'Settings');
    } finally {
      isLoading.value = false;
    }
  }
  
  Future<void> loadAiConfig() async {
    try {
      final response = await _apiService.get(ApiConfig.aiConfig);
      
      if (response.statusCode == 200) {
        aiConfig.value = Map<String, dynamic>.from(response.data);
      }
    } catch (e) {
      _logger.error('Failed to load AI config: $e', source: 'Settings');
    }
  }
  
  Future<void> updateSetting(String key, dynamic value) async {
    try {
      await _apiService.put(
        ApiConfig.settings,
        data: {'key': key, 'value': value},
      );
      
      settings.value[key] = value;
      settings.refresh();
      
      _logger.info('Setting updated: $key', source: 'Settings');
    } catch (e) {
      _logger.error('Failed to update setting: $e', source: 'Settings');
    }
  }
  
  void toggleTheme() {
    _themeController.toggleTheme();
  }
  
  void setTheme(ThemeMode mode) {
    _themeController.setThemeMode(mode);
  }
  
  Future<void> logout() async {
    await _authService.logout();
  }
  
  String get username => _authService.currentUser.value?.username ?? 'User';
  String get email => _authService.currentUser.value?.email ?? '';
  String get role => _authService.currentUser.value?.role ?? 'user';
  bool get isAdmin => _authService.currentUser.value?.isAdmin ?? false;
}
