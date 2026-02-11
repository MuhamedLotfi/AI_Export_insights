import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:shared_preferences/shared_preferences.dart';

class ThemeController extends GetxController {
  final Rx<ThemeMode> _themeMode = ThemeMode.dark.obs;
  
  ThemeMode get currentThemeMode => _themeMode.value;
  bool get isDarkMode => _themeMode.value == ThemeMode.dark;
  
  @override
  void onInit() {
    super.onInit();
    loadTheme();
  }
  
  Future<void> loadTheme() async {
    final prefs = await SharedPreferences.getInstance();
    final savedTheme = prefs.getString('theme_mode') ?? 'dark';
    
    switch (savedTheme) {
      case 'light':
        _themeMode.value = ThemeMode.light;
        break;
      case 'system':
        _themeMode.value = ThemeMode.system;
        break;
      default:
        _themeMode.value = ThemeMode.dark;
    }
  }
  
  Future<void> loadUserTheme() async {
    // Load theme preference after user is authenticated
    await loadTheme();
  }
  
  Future<void> setThemeMode(ThemeMode mode) async {
    _themeMode.value = mode;
    
    final prefs = await SharedPreferences.getInstance();
    String themeValue;
    
    switch (mode) {
      case ThemeMode.light:
        themeValue = 'light';
        break;
      case ThemeMode.system:
        themeValue = 'system';
        break;
      default:
        themeValue = 'dark';
    }
    
    await prefs.setString('theme_mode', themeValue);
  }
  
  void toggleTheme() {
    if (_themeMode.value == ThemeMode.dark) {
      setThemeMode(ThemeMode.light);
    } else {
      setThemeMode(ThemeMode.dark);
    }
  }
}
