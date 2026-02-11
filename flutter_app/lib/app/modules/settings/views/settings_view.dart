import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../controllers/settings_controller.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../routes/app_routes.dart';

class SettingsView extends GetView<SettingsController> {
  const SettingsView({Key? key}) : super(key: key);

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
        title: const Text('Settings', style: TextStyle(color: Colors.white)),
      ),
      body: Obx(() {
        if (controller.isLoading.value) {
          return const Center(
            child: CircularProgressIndicator(color: AppTheme.primaryColor),
          );
        }
        
        return ListView(
          padding: const EdgeInsets.all(16),
          children: [
            // Profile Section
            _buildSection(
              title: 'Profile',
              children: [
                _buildProfileCard(),
              ],
            ),
            const SizedBox(height: 24),
            
            // Appearance Section
            _buildSection(
              title: 'Appearance',
              children: [
                _buildThemeSetting(),
              ],
            ),
            const SizedBox(height: 24),
            
            // AI Settings
            _buildSection(
              title: 'AI Configuration',
              children: [
                _buildAiSettings(),
              ],
            ),
            const SizedBox(height: 24),
            
            // About Section
            _buildSection(
              title: 'About',
              children: [
                _buildAboutCard(),
              ],
            ),
            const SizedBox(height: 24),
            
            // Logout
            _buildLogoutButton(),
          ],
        );
      }),
    );
  }
  
  Widget _buildSection({
    required String title,
    required List<Widget> children,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.only(left: 8, bottom: 12),
          child: Text(
            title,
            style: TextStyle(
              color: Colors.white.withOpacity(0.6),
              fontSize: 14,
              fontWeight: FontWeight.w600,
              letterSpacing: 0.5,
            ),
          ),
        ),
        ...children,
      ],
    );
  }
  
  Widget _buildProfileCard() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppTheme.darkCard,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white.withOpacity(0.1)),
      ),
      child: Row(
        children: [
          Container(
            width: 60,
            height: 60,
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [AppTheme.primaryColor, AppTheme.secondaryColor],
              ),
              borderRadius: BorderRadius.circular(16),
            ),
            child: Center(
              child: Text(
                controller.username.substring(0, 1).toUpperCase(),
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 24,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  controller.username,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 18,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  controller.email,
                  style: TextStyle(color: Colors.white.withOpacity(0.6)),
                ),
                const SizedBox(height: 8),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: AppTheme.primaryColor.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    controller.role.toUpperCase(),
                    style: const TextStyle(
                      color: AppTheme.primaryColor,
                      fontSize: 11,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
  
  Widget _buildThemeSetting() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.darkCard,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white.withOpacity(0.1)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  Icon(Icons.palette_outlined, color: Colors.white.withOpacity(0.8)),
                  const SizedBox(width: 12),
                  const Text(
                    'Theme',
                    style: TextStyle(color: Colors.white, fontSize: 16),
                  ),
                ],
              ),
              Obx(() => Switch(
                value: controller.isDarkMode,
                activeColor: AppTheme.primaryColor,
                onChanged: (_) => controller.toggleTheme(),
              )),
            ],
          ),
          const SizedBox(height: 12),
          Obx(() => Row(
            children: [
              _buildThemeOption(
                label: 'Light',
                icon: Icons.light_mode,
                isSelected: controller.currentTheme == ThemeMode.light,
                onTap: () => controller.setTheme(ThemeMode.light),
              ),
              const SizedBox(width: 12),
              _buildThemeOption(
                label: 'Dark',
                icon: Icons.dark_mode,
                isSelected: controller.currentTheme == ThemeMode.dark,
                onTap: () => controller.setTheme(ThemeMode.dark),
              ),
              const SizedBox(width: 12),
              _buildThemeOption(
                label: 'System',
                icon: Icons.settings_brightness,
                isSelected: controller.currentTheme == ThemeMode.system,
                onTap: () => controller.setTheme(ThemeMode.system),
              ),
            ],
          )),
        ],
      ),
    );
  }
  
  Widget _buildThemeOption({
    required String label,
    required IconData icon,
    required bool isSelected,
    required VoidCallback onTap,
  }) {
    return Expanded(
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 12),
          decoration: BoxDecoration(
            color: isSelected ? AppTheme.primaryColor.withOpacity(0.2) : Colors.transparent,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
              color: isSelected ? AppTheme.primaryColor : Colors.white.withOpacity(0.2),
            ),
          ),
          child: Column(
            children: [
              Icon(
                icon,
                color: isSelected ? AppTheme.primaryColor : Colors.white.withOpacity(0.6),
              ),
              const SizedBox(height: 4),
              Text(
                label,
                style: TextStyle(
                  color: isSelected ? AppTheme.primaryColor : Colors.white.withOpacity(0.6),
                  fontSize: 12,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
  
  Widget _buildAiSettings() {
    return Obx(() => Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.darkCard,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white.withOpacity(0.1)),
      ),
      child: Column(
        children: [
          _buildSettingRow(
            icon: Icons.smart_toy,
            label: 'Model Provider',
            value: controller.aiConfig.value['model_provider'] ?? 'Ollama',
          ),
          const Divider(color: Colors.white12),
          _buildSettingRow(
            icon: Icons.memory,
            label: 'Model',
            value: controller.aiConfig.value['model_name'] ?? 'llama3.2:latest',
          ),
          const Divider(color: Colors.white12),
          _buildSettingRow(
            icon: Icons.hub,
            label: 'LangGraph',
            value: controller.aiConfig.value['langgraph_enabled'] == true ? 'Enabled' : 'Disabled',
            valueColor: controller.aiConfig.value['langgraph_enabled'] == true
                ? AppTheme.accentColor
                : Colors.grey,
          ),
          const Divider(color: Colors.white12),
          _buildSettingRow(
            icon: Icons.route,
            label: 'Domain Routing',
            value: controller.aiConfig.value['domain_routing_enabled'] == true ? 'Enabled' : 'Disabled',
            valueColor: controller.aiConfig.value['domain_routing_enabled'] == true
                ? AppTheme.accentColor
                : Colors.grey,
          ),
        ],
      ),
    ));
  }
  
  Widget _buildSettingRow({
    required IconData icon,
    required String label,
    required String value,
    Color? valueColor,
  }) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        children: [
          Icon(icon, color: Colors.white.withOpacity(0.6), size: 20),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              label,
              style: const TextStyle(color: Colors.white),
            ),
          ),
          Text(
            value,
            style: TextStyle(
              color: valueColor ?? Colors.white.withOpacity(0.6),
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
      ),
    );
  }
  
  Widget _buildAboutCard() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppTheme.darkCard,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white.withOpacity(0.1)),
      ),
      child: Column(
        children: [
          Row(
            children: [
              Container(
                width: 48,
                height: 48,
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: [AppTheme.primaryColor, AppTheme.secondaryColor],
                  ),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Icon(Icons.insights, color: Colors.white, size: 28),
              ),
              const SizedBox(width: 16),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'AI Export Insights',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  Text(
                    'Version 1.0.0',
                    style: TextStyle(color: Colors.white.withOpacity(0.5)),
                  ),
                ],
              ),
            ],
          ),
          const SizedBox(height: 16),
          Text(
            'Multi-Domain AI Agent Platform with LangGraph-based architecture for intelligent data insights and visualization.',
            style: TextStyle(
              color: Colors.white.withOpacity(0.6),
              fontSize: 13,
            ),
          ),
        ],
      ),
    );
  }
  
  Widget _buildLogoutButton() {
    return ElevatedButton.icon(
      onPressed: controller.logout,
      icon: const Icon(Icons.logout),
      label: const Text('Logout'),
      style: ElevatedButton.styleFrom(
        backgroundColor: AppTheme.errorColor.withOpacity(0.2),
        foregroundColor: AppTheme.errorColor,
        padding: const EdgeInsets.symmetric(vertical: 16),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
          side: const BorderSide(color: AppTheme.errorColor),
        ),
      ),
    );
  }
}
