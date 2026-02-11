import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../../../../config/api_config.dart';
import '../../../data/services/api_service.dart';
import '../../../data/services/log_service.dart';
import '../../../models/domain_agent.dart';
import '../../../models/user_model.dart';


class UserManagementController extends GetxController {
  final ApiService _apiService = Get.find<ApiService>();
  final LogService _logger = LogService.instance;
  
  final RxBool isLoading = false.obs;
  final RxList<User> users = <User>[].obs;
  final RxList<DomainAgent> allAgents = <DomainAgent>[].obs;
  final Rx<Map<int, List<String>>> userAgentAssignments = Rx<Map<int, List<String>>>({});
  
  @override
  void onInit() {
    super.onInit();
    loadUsers();
    loadAgents();
  }
  
  Future<void> loadUsers() async {
    isLoading.value = true;
    
    try {
      final response = await _apiService.get(ApiConfig.users);
      
      if (response.statusCode == 200) {
        users.value = (response.data as List)
            .map((json) => User.fromJson(json))
            .toList();
        
        // Build user-agent map
        final map = <int, List<String>>{};
        for (final user in users) {
          map[user.id] = user.domainAgents;
        }
        userAgentAssignments.value = map;
        
        _logger.info('Loaded ${users.length} users', source: 'UserMgmt');
      }
    } catch (e) {
      _logger.error('Failed to load users: $e', source: 'UserMgmt');
    } finally {
      isLoading.value = false;
    }
  }
  
  Future<void> loadAgents() async {
    try {
      final response = await _apiService.get(ApiConfig.agents);
      
      if (response.statusCode == 200) {
        allAgents.value = (response.data as List)
            .map((json) => DomainAgent.fromJson(json))
            .toList();
      }
    } catch (e) {
      _logger.error('Failed to load agents: $e', source: 'UserMgmt');
    }
  }
  
  Future<void> toggleAgentForUser(int userId, String agentCode, bool assign) async {
    try {
      if (assign) {
        await _apiService.post(
          ApiConfig.assignAgent,
          data: {'user_id': userId, 'agent_code': agentCode},
        );
      } else {
        await _apiService.delete(
          ApiConfig.revokeAgent,
          data: {'user_id': userId, 'agent_code': agentCode},
        );
      }
      
      // Update local state
      final currentAgents = userAgentAssignments.value[userId] ?? [];
      if (assign) {
        if (!currentAgents.contains(agentCode)) {
          currentAgents.add(agentCode);
        }
      } else {
        currentAgents.remove(agentCode);
      }
      userAgentAssignments.value[userId] = currentAgents;
      userAgentAssignments.refresh();
      
      Get.snackbar(
        'Success',
        assign ? 'Agent assigned' : 'Agent revoked',
        backgroundColor: Colors.green,
        colorText: Colors.white,
        snackPosition: SnackPosition.TOP,
      );
      
      _logger.info('${assign ? "Assigned" : "Revoked"} $agentCode for user $userId', source: 'UserMgmt');
    } catch (e) {
      _logger.error('Failed to update agent: $e', source: 'UserMgmt');
      Get.snackbar(
        'Error',
        'Failed to update agent assignment',
        backgroundColor: Colors.red,
        colorText: Colors.white,
        snackPosition: SnackPosition.TOP,
      );
    }
  }
  
  bool userHasAgent(int userId, String agentCode) {
    return userAgentAssignments.value[userId]?.contains(agentCode) ?? false;
  }
  
  Future<void> createUser(String username, String email, String password, String role) async {
    isLoading.value = true;
    try {
      final response = await _apiService.post(
        ApiConfig.register,
        data: {
          'username': username,
          'email': email,
          'password': password,
          'role': role,
        },
      );
      
      if (response.statusCode == 200 || response.statusCode == 201) {
        Get.back(); // Close dialog
        Get.snackbar(
          'Success',
          'User created successfully',
          backgroundColor: Colors.green,
          colorText: Colors.white,
        );
        refresh();
      }
    } catch (e) {
      Get.snackbar(
        'Error',
        'Failed to create user: $e',
        backgroundColor: Colors.red,
        colorText: Colors.white,
      );
    } finally {
      isLoading.value = false;
    }
  }

  Future<void> resetPassword(int userId, String newPassword) async {
    try {
      final response = await _apiService.post(
        ApiConfig.resetUserPassword(userId),
        data: {'new_password': newPassword},
      );
      
      if (response.statusCode == 200) {
        Get.back(); // Close dialog
        Get.snackbar(
          'Success',
          'Password reset successfully',
          backgroundColor: Colors.green,
          colorText: Colors.white,
        );
      }
    } catch (e) {
      Get.snackbar(
        'Error',
        'Failed to reset password: $e',
        backgroundColor: Colors.red,
        colorText: Colors.white,
      );
    }
  }

  Future<void> refresh() async {
    await loadUsers();
    await loadAgents();
  }
}
