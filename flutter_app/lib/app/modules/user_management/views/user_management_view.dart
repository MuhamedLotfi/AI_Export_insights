import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../controllers/user_management_controller.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../routes/app_routes.dart';
import '../../../models/user_model.dart';
import '../../../models/domain_agent.dart';

class UserManagementView extends GetView<UserManagementController> {
  const UserManagementView({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.darkBackground,
      appBar: AppBar(
        backgroundColor: AppTheme.darkSurface,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: Colors.white),
          onPressed: () => Get.offNamed(AppRoutes.dashboard),
        ),
        title: const Text('User Management', style: TextStyle(color: Colors.white)),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh, color: Colors.white),
            onPressed: controller.refresh,
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => _showCreateUserDialog(context, controller),
        backgroundColor: AppTheme.primaryColor,
        child: const Icon(Icons.add, color: Colors.white),
      ),
      body: Obx(() {
        if (controller.isLoading.value) {
          return const Center(
            child: CircularProgressIndicator(color: AppTheme.primaryColor),
          );
        }
        
        if (controller.users.isEmpty) {
          return _buildEmptyState();
        }
        
        return RefreshIndicator(
          onRefresh: controller.refresh,
          child: ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: controller.users.length,
            itemBuilder: (context, index) {
              return _buildUserCard(controller.users[index], context);
            },
          ),
        );
      }),
    );
  }
  
  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.people_outline, size: 60, color: Colors.white.withOpacity(0.3)),
          const SizedBox(height: 16),
          const Text(
            'No Users Found',
            style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.w600),
          ),
        ],
      ),
    );
  }
  
  Widget _buildUserCard(User user, BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      decoration: BoxDecoration(
        color: AppTheme.darkCard,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white.withOpacity(0.1)),
      ),
      child: ExpansionTile(
        tilePadding: const EdgeInsets.all(16),
        childrenPadding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
        leading: CircleAvatar(
          backgroundColor: _getRoleColor(user.role).withOpacity(0.2),
          foregroundColor: _getRoleColor(user.role),
          child: Text(
            user.username.substring(0, 1).toUpperCase(),
            style: const TextStyle(fontWeight: FontWeight.bold),
          ),
        ),
        title: Row(
          children: [
            Text(
              user.username,
              style: const TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(width: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
              decoration: BoxDecoration(
                color: _getRoleColor(user.role).withOpacity(0.2),
                borderRadius: BorderRadius.circular(4),
              ),
              child: Text(
                user.role.toUpperCase(),
                style: TextStyle(
                  color: _getRoleColor(user.role),
                  fontSize: 10,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ],
        ),
        subtitle: Text(
          user.email,
          style: TextStyle(color: Colors.white.withOpacity(0.5)),
        ),
        trailing: Obx(() {
          final agentCount = controller.userAgentAssignments.value[user.id]?.length ?? 0;
          return Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: AppTheme.primaryColor.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  '$agentCount agents',
                  style: const TextStyle(
                    color: AppTheme.primaryColor,
                    fontSize: 12,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ),
              const SizedBox(width: 8),
              PopupMenuButton<String>(
                icon: const Icon(Icons.more_vert, color: Colors.white70),
                onSelected: (value) {
                  if (value == 'reset_password') {
                     _showResetPasswordDialog(context, user, controller);
                  }
                },
                itemBuilder: (context) => [
                  const PopupMenuItem(
                    value: 'reset_password',
                    child: Row(
                      children: [
                        Icon(Icons.lock_reset, color: Colors.black87),
                        SizedBox(width: 8),
                        Text('Reset Password', style: TextStyle(color: Colors.black87)),
                      ],
                    ),
                  ),
                ],
              ),
            ],
          );
        }),
        iconColor: Colors.white.withOpacity(0.5),
        collapsedIconColor: Colors.white.withOpacity(0.5),
        children: [
          const Divider(color: Colors.white12),
          const SizedBox(height: 8),
          _buildAgentAssignments(user),
        ],
      ),
    );
  }
  
  Widget _buildAgentAssignments(User user) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Agent Assignments',
          style: TextStyle(
            color: Colors.white.withOpacity(0.7),
            fontSize: 14,
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 12),
        Obx(() => Wrap(
          spacing: 8,
          runSpacing: 8,
          children: controller.allAgents.map((agent) {
            final hasAgent = controller.userHasAgent(user.id, agent.code);
            
            return _buildAgentChip(
              agent: agent,
              isAssigned: hasAgent,
              onToggle: () => controller.toggleAgentForUser(user.id, agent.code, !hasAgent),
            );
          }).toList(),
        )),
      ],
    );
  }
  
  Widget _buildAgentChip({
    required DomainAgent agent,
    required bool isAssigned,
    required VoidCallback onToggle,
  }) {
    return InkWell(
      onTap: onToggle,
      borderRadius: BorderRadius.circular(12),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        decoration: BoxDecoration(
          color: isAssigned ? agent.getColor().withOpacity(0.2) : Colors.transparent,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: isAssigned ? agent.getColor() : Colors.white.withOpacity(0.2),
          ),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              agent.getIcon(),
              size: 18,
              color: isAssigned ? agent.getColor() : Colors.white.withOpacity(0.5),
            ),
            const SizedBox(width: 8),
            Text(
              agent.name,
              style: TextStyle(
                color: isAssigned ? agent.getColor() : Colors.white.withOpacity(0.5),
                fontWeight: isAssigned ? FontWeight.w600 : FontWeight.normal,
              ),
            ),
            const SizedBox(width: 8),
            Icon(
              isAssigned ? Icons.check_circle : Icons.circle_outlined,
              size: 16,
              color: isAssigned ? agent.getColor() : Colors.white.withOpacity(0.3),
            ),
          ],
        ),
      ),
    );
  }
  
  Color _getRoleColor(String role) {
    switch (role) {
      case 'admin':
        return AppTheme.errorColor;
      case 'manager':
        return AppTheme.warningColor;
      default:
        return AppTheme.primaryColor;
    }
  }
  }

  void _showCreateUserDialog(BuildContext context, UserManagementController controller) {
    final usernameController = TextEditingController();
    final emailController = TextEditingController();
    final passwordController = TextEditingController();
    final role = 'user'.obs;
    
    Get.dialog(
      Dialog(
        backgroundColor: AppTheme.darkCard,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('Create User', style: TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold)),
              const SizedBox(height: 16),
              TextField(
                controller: usernameController,
                style: const TextStyle(color: Colors.white),
                decoration: const InputDecoration(labelText: 'Username', labelStyle: TextStyle(color: Colors.white70)),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: emailController,
                style: const TextStyle(color: Colors.white),
                decoration: const InputDecoration(labelText: 'Email', labelStyle: TextStyle(color: Colors.white70)),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: passwordController,
                obscureText: true,
                style: const TextStyle(color: Colors.white),
                decoration: const InputDecoration(labelText: 'Password', labelStyle: TextStyle(color: Colors.white70)),
              ),
              const SizedBox(height: 12),
              Obx(() => DropdownButton<String>(
                value: role.value,
                dropdownColor: AppTheme.darkCard,
                style: const TextStyle(color: Colors.white),
                onChanged: (val) => role.value = val!,
                items: const [
                  DropdownMenuItem(value: 'user', child: Text('User')),
                  DropdownMenuItem(value: 'manager', child: Text('Manager')),
                  DropdownMenuItem(value: 'admin', child: Text('Admin')),
                ],
              )),
              const SizedBox(height: 24),
              Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                   TextButton(
                    onPressed: () => Get.back(),
                    child: const Text('Cancel', style: TextStyle(color: Colors.white54)),
                  ),
                  const SizedBox(width: 12),
                  ElevatedButton(
                    style: ElevatedButton.styleFrom(backgroundColor: AppTheme.primaryColor),
                    onPressed: () => controller.createUser(
                      usernameController.text,
                      emailController.text,
                      passwordController.text,
                      role.value,
                    ),
                    child: const Text('Create'),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _showResetPasswordDialog(BuildContext context, User user, UserManagementController controller) {
    final passwordController = TextEditingController();
    
    Get.dialog(
      Dialog(
        backgroundColor: AppTheme.darkCard,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Reset Password for ${user.username}', style: const TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold)),
              const SizedBox(height: 16),
              TextField(
                controller: passwordController,
                obscureText: true,
                style: const TextStyle(color: Colors.white),
                decoration: const InputDecoration(labelText: 'New Password', labelStyle: TextStyle(color: Colors.white70)),
              ),
              const SizedBox(height: 24),
              Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  TextButton(
                    onPressed: () => Get.back(),
                    child: const Text('Cancel', style: TextStyle(color: Colors.white54)),
                  ),
                  const SizedBox(width: 12),
                  ElevatedButton(
                    style: ElevatedButton.styleFrom(backgroundColor: AppTheme.primaryColor),
                    onPressed: () => controller.resetPassword(user.id, passwordController.text),
                    child: const Text('Reset'),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

