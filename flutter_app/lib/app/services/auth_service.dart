import 'package:dio/dio.dart';
import 'package:get/get.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../data/services/api_service.dart';
import '../data/services/log_service.dart';
import '../routes/app_routes.dart';
import '../../config/api_config.dart';
import '../models/user_model.dart';
import '../models/domain_agent.dart';

class AuthService extends GetxService {
  late final SharedPreferences _prefs;
  final _logger = LogService.instance;
  
  final RxString token = ''.obs;
  final Rx<User?> currentUser = Rx<User?>(null);
  final RxBool isAuthenticated = false.obs;
  final RxList<String> userAgents = <String>[].obs;
  final RxBool isLoading = false.obs;
  
  Future<AuthService> init() async {
    // Use SharedPreferences (persists to localStorage on web)
    _prefs = await SharedPreferences.getInstance();
    
    // Load saved token
    final savedToken = _prefs.getString('auth_token');
    _logger.info('Token from storage: ${savedToken != null ? "found (${savedToken.length} chars)" : "not found"}', source: 'Auth');
    if (savedToken != null && savedToken.isNotEmpty) {
      token.value = savedToken;
      _logger.info('Token set on service, calling /auth/me...', source: 'Auth');
      await _loadCurrentUser(navigate: false);
    } else {
      _logger.info('No saved token, user needs to login', source: 'Auth');
    }
    return this;
  }
  
  Future<bool> login(String username, String password) async {
    isLoading.value = true;
    
    try {
      final apiService = Get.find<ApiService>();
      
      final response = await apiService.post(
        ApiConfig.login,
        data: {
          'username': username,
          'password': password,
        },
        options: Options(
          contentType: Headers.formUrlEncodedContentType,
        ),
      );
      
      if (response.statusCode == 200) {
        final data = response.data;
        token.value = data['access_token'];
        
        // Save token
        await _prefs.setString('auth_token', token.value);
        
        // Load user data
        currentUser.value = User.fromJson(data['user']);
        userAgents.value = List<String>.from(data['user']['domain_agents'] ?? []);
        isAuthenticated.value = true;
        
        _logger.info('Login successful: ${username}', source: 'Auth');
        return true;
      }
    } catch (e) {
      _logger.error('Login failed: $e', source: 'Auth');
    } finally {
      isLoading.value = false;
    }
    
    return false;
  }
  
  Future<bool> register(String username, String email, String password) async {
    isLoading.value = true;
    
    try {
      final apiService = Get.find<ApiService>();
      
      final response = await apiService.post(
        ApiConfig.register,
        data: {
          'username': username,
          'email': email,
          'password': password,
        },
      );
      
      if (response.statusCode == 200) {
        _logger.info('Registration successful: $username', source: 'Auth');
        return true;
      }
    } catch (e) {
      _logger.error('Registration failed: $e', source: 'Auth');
    } finally {
      isLoading.value = false;
    }
    
    return false;
  }
  
  Future<void> _loadCurrentUser({bool navigate = true}) async {
    try {
      final apiService = Get.find<ApiService>();
      
      final response = await apiService.get(ApiConfig.me);
      
      if (response.statusCode == 200) {
        currentUser.value = User.fromJson(response.data);
        userAgents.value = List<String>.from(response.data['domain_agents'] ?? []);
        isAuthenticated.value = true;
        _logger.info('User loaded: ${currentUser.value?.username}', source: 'Auth');
      } else {
        // If status is not 200, we might have an invalid token
        _logger.warning('Failed to load user, status: ${response.statusCode}', source: 'Auth');
        if (response.statusCode == 401) {
          await logout(navigate: navigate);
        }
      }
    } catch (e) {
      _logger.error('Failed to load user: $e', source: 'Auth');
      // Only logout if it's an auth error, not a network error
      if (e is DioException && e.response?.statusCode == 401) {
        await logout(navigate: navigate);
      }
    }
  }
  
  Future<void> logout({bool navigate = true}) async {
    token.value = '';
    currentUser.value = null;
    userAgents.value = [];
    isAuthenticated.value = false;
    
    await _prefs.remove('auth_token');
    
    _logger.info('User logged out', source: 'Auth');
    
    if (navigate && Get.context != null) {
      Get.offAllNamed(AppRoutes.login);
    }
  }
  
  String getInitialRoute() {
    return isAuthenticated.value ? AppRoutes.dashboard : AppRoutes.login;
  }
  
  bool hasAgentAccess(String agentCode) {
    return userAgents.contains(agentCode);
  }
  
  // Domain Agent Management
  Future<List<DomainAgent>> getDomainAgents() async {
    try {
      final apiService = Get.find<ApiService>();
      final response = await apiService.get(ApiConfig.agents);
      
      if (response.statusCode == 200) {
        return (response.data as List)
            .map((json) => DomainAgent.fromJson(json))
            .toList();
      }
    } catch (e) {
      _logger.error('Failed to get domain agents: $e', source: 'Auth');
    }
    return [];
  }
  
  Future<List<String>> getMyDomainAgents() async {
    try {
      final apiService = Get.find<ApiService>();
      final response = await apiService.get(ApiConfig.myAgents);
      
      if (response.statusCode == 200) {
        return List<String>.from(response.data);
      }
    } catch (e) {
      _logger.error('Failed to get my agents: $e', source: 'Auth');
    }
    return [];
  }
  
  Future<bool> assignDomainAgent(int userId, String agentCode) async {
    try {
      final apiService = Get.find<ApiService>();
      final response = await apiService.post(
        ApiConfig.assignAgent,
        data: {'user_id': userId, 'agent_code': agentCode},
      );
      return response.statusCode == 200;
    } catch (e) {
      _logger.error('Failed to assign agent: $e', source: 'Auth');
      return false;
    }
  }
  
  Future<bool> revokeDomainAgent(int userId, String agentCode) async {
    try {
      final apiService = Get.find<ApiService>();
      final response = await apiService.delete(
        ApiConfig.revokeAgent,
        data: {'user_id': userId, 'agent_code': agentCode},
      );
      return response.statusCode == 200;
    } catch (e) {
      _logger.error('Failed to revoke agent: $e', source: 'Auth');
      return false;
    }
  }
}


