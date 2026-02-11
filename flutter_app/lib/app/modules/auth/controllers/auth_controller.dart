import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../../../routes/app_routes.dart';
import '../../../services/auth_service.dart';


class AuthController extends GetxController {
  final AuthService _authService = Get.find<AuthService>();
  
  final usernameController = TextEditingController();
  final emailController = TextEditingController();
  final passwordController = TextEditingController();
  final confirmPasswordController = TextEditingController();
  
  final RxBool isLoading = false.obs;
  final RxBool obscurePassword = true.obs;
  final RxString errorMessage = ''.obs;
  
  /* 
  @override
  void onClose() {
    usernameController.dispose();
    emailController.dispose();
    passwordController.dispose();
    confirmPasswordController.dispose();
    super.onClose();
  }
  */
  
  void togglePasswordVisibility() {
    obscurePassword.toggle();
  }
  
  Future<void> login() async {
    if (usernameController.text.isEmpty || passwordController.text.isEmpty) {
      errorMessage.value = 'Please enter username and password';
      return;
    }
    
    errorMessage.value = '';
    isLoading.value = true;
    
    final success = await _authService.login(
      usernameController.text,
      passwordController.text,
    );
    
    isLoading.value = false;
    
    if (success) {
      Get.offAllNamed(AppRoutes.dashboard);
    } else {
      errorMessage.value = 'Invalid username or password';
    }
  }
  
  Future<void> register() async {
    if (usernameController.text.isEmpty ||
        emailController.text.isEmpty ||
        passwordController.text.isEmpty) {
      errorMessage.value = 'Please fill in all fields';
      return;
    }
    
    if (passwordController.text != confirmPasswordController.text) {
      errorMessage.value = 'Passwords do not match';
      return;
    }
    
    errorMessage.value = '';
    isLoading.value = true;
    
    final success = await _authService.register(
      usernameController.text,
      emailController.text,
      passwordController.text,
    );
    
    isLoading.value = false;
    
    if (success) {
      Get.snackbar(
        'Success',
        'Registration successful! Please login.',
        snackPosition: SnackPosition.TOP,
        backgroundColor: Colors.green,
        colorText: Colors.white,
      );
      Get.offNamed(AppRoutes.login);
    } else {
      errorMessage.value = 'Registration failed. Username may already exist.';
    }
  }
  
  void goToRegister() {
    Get.toNamed(AppRoutes.register);
  }
  
  void goToLogin() {
    Get.offNamed(AppRoutes.login);
  }
}
