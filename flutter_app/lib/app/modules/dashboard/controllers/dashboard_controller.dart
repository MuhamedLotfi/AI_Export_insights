import 'package:get/get.dart';
import '../../../../config/api_config.dart';
import '../../../data/services/api_service.dart';
import '../../../data/services/log_service.dart';
import '../../../routes/app_routes.dart';
import '../../../services/auth_service.dart';


class DashboardController extends GetxController {
  final ApiService _apiService = Get.find<ApiService>();
  final AuthService _authService = Get.find<AuthService>();
  final LogService _logger = LogService.instance;
  
  final RxBool isLoading = false.obs;
  final RxInt selectedNavIndex = 0.obs;
  
  // Dashboard Data
  final RxList<Map<String, dynamic>> kpis = <Map<String, dynamic>>[].obs;
  final RxList<Map<String, dynamic>> charts = <Map<String, dynamic>>[].obs;
  final RxList<Map<String, dynamic>> recentActivity = <Map<String, dynamic>>[].obs;
  final Rx<Map<String, dynamic>> systemStatus = Rx<Map<String, dynamic>>({});
  
  @override
  void onInit() {
    super.onInit();
    loadDashboard();
  }
  
  Future<void> loadDashboard() async {
    isLoading.value = true;
    
    try {
      final response = await _apiService.get(ApiConfig.dashboard);
      
      if (response.statusCode == 200) {
        final data = response.data;
        
        kpis.value = List<Map<String, dynamic>>.from(data['kpis'] ?? []);
        charts.value = List<Map<String, dynamic>>.from(data['charts'] ?? []);
        recentActivity.value = List<Map<String, dynamic>>.from(data['recent_activity'] ?? []);
        systemStatus.value = Map<String, dynamic>.from(data['system_status'] ?? {});
        
        _logger.info('Dashboard loaded successfully', source: 'Dashboard');
      }
    } catch (e) {
      _logger.error('Failed to load dashboard: $e', source: 'Dashboard');
    } finally {
      isLoading.value = false;
    }
  }
  
  void selectNavItem(int index) {
    selectedNavIndex.value = index;
    
    switch (index) {
      case 0:
        // Dashboard - already here
        break;
      case 1:
        Get.toNamed(AppRoutes.aiAssistant);
        break;
      case 2:
        Get.toNamed(AppRoutes.settings);
        break;
      case 3:
        if (_authService.currentUser.value?.isAdmin ?? false) {
          Get.toNamed(AppRoutes.userManagement);
        }
        break;
    }
  }
  
  void goToAiAssistant() {
    Get.toNamed(AppRoutes.aiAssistant);
  }
  
  void goToSettings() {
    Get.toNamed(AppRoutes.settings);
  }
  
  Future<void> logout() async {
    await _authService.logout();
  }
  
  String get username => _authService.currentUser.value?.username ?? 'User';
  String get userRole => _authService.currentUser.value?.role ?? 'user';
  bool get isAdmin => _authService.currentUser.value?.isAdmin ?? false;
}
