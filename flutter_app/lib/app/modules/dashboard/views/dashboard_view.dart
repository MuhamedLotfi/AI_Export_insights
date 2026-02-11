import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:fl_chart/fl_chart.dart';
import '../controllers/dashboard_controller.dart';
import '../../../../core/theme/app_theme.dart';

class DashboardView extends GetView<DashboardController> {
  const DashboardView({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final screenWidth = MediaQuery.of(context).size.width;
    final isWideScreen = screenWidth > 900;
    
    return Scaffold(
      body: Row(
        children: [
          // Side Navigation
          if (isWideScreen) _buildSideNav(),
          
          // Main Content
          Expanded(
            child: Column(
              children: [
                // Top Bar
                _buildTopBar(context),
                
                // Dashboard Content
                Expanded(
                  child: Obx(() {
                    if (controller.isLoading.value) {
                      return const Center(
                        child: CircularProgressIndicator(color: AppTheme.primaryColor),
                      );
                    }
                    
                    return RefreshIndicator(
                      onRefresh: controller.loadDashboard,
                      child: SingleChildScrollView(
                        padding: const EdgeInsets.all(24),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            _buildWelcomeSection(),
                            const SizedBox(height: 24),
                            _buildKPICards(),
                            const SizedBox(height: 24),
                            _buildChartsSection(),
                            const SizedBox(height: 24),
                            _buildQuickActions(),
                          ],
                        ),
                      ),
                    );
                  }),
                ),
              ],
            ),
          ),
        ],
      ),
      // Bottom Nav for mobile
      bottomNavigationBar: isWideScreen ? null : _buildBottomNav(),
    );
  }
  
  Widget _buildSideNav() {
    return Container(
      width: 240,
      decoration: BoxDecoration(
        color: AppTheme.darkSurface,
        border: Border(
          right: BorderSide(color: Colors.white.withOpacity(0.1)),
        ),
      ),
      child: Column(
        children: [
          // Logo
          Container(
            padding: const EdgeInsets.all(24),
            child: Row(
              children: [
                Container(
                  width: 40,
                  height: 40,
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      colors: [AppTheme.primaryColor, AppTheme.secondaryColor],
                    ),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: const Icon(Icons.insights, color: Colors.white, size: 24),
                ),
                const SizedBox(width: 12),
                const Text(
                  'AI Insights',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
          ),
          
          const Divider(height: 1, color: Colors.white12),
          
          // Nav Items
          Expanded(
            child: Obx(() => ListView(
              padding: const EdgeInsets.symmetric(vertical: 16),
              children: [
                _buildNavItem(
                  icon: Icons.dashboard_outlined,
                  label: 'Dashboard',
                  isSelected: controller.selectedNavIndex.value == 0,
                  onTap: () => controller.selectNavItem(0),
                ),
                _buildNavItem(
                  icon: Icons.chat_outlined,
                  label: 'AI Assistant',
                  isSelected: controller.selectedNavIndex.value == 1,
                  onTap: () => controller.selectNavItem(1),
                ),
                _buildNavItem(
                  icon: Icons.settings_outlined,
                  label: 'Settings',
                  isSelected: controller.selectedNavIndex.value == 2,
                  onTap: () => controller.selectNavItem(2),
                ),
                if (controller.isAdmin)
                  _buildNavItem(
                    icon: Icons.people_outlined,
                    label: 'User Management',
                    isSelected: controller.selectedNavIndex.value == 3,
                    onTap: () => controller.selectNavItem(3),
                  ),
              ],
            )),
          ),
          
          // Logout
          Container(
            padding: const EdgeInsets.all(16),
            child: _buildNavItem(
              icon: Icons.logout,
              label: 'Logout',
              isSelected: false,
              onTap: controller.logout,
              isDanger: true,
            ),
          ),
        ],
      ),
    );
  }
  
  Widget _buildNavItem({
    required IconData icon,
    required String label,
    required bool isSelected,
    required VoidCallback onTap,
    bool isDanger = false,
  }) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
      child: Material(
        color: isSelected ? AppTheme.primaryColor.withOpacity(0.15) : Colors.transparent,
        borderRadius: BorderRadius.circular(12),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(12),
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            child: Row(
              children: [
                Icon(
                  icon,
                  color: isDanger
                      ? AppTheme.errorColor
                      : isSelected
                          ? AppTheme.primaryColor
                          : Colors.white.withOpacity(0.6),
                  size: 22,
                ),
                const SizedBox(width: 12),
                Text(
                  label,
                  style: TextStyle(
                    color: isDanger
                        ? AppTheme.errorColor
                        : isSelected
                            ? AppTheme.primaryColor
                            : Colors.white.withOpacity(0.8),
                    fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
  
  Widget _buildTopBar(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
      decoration: BoxDecoration(
        color: AppTheme.darkSurface,
        border: Border(
          bottom: BorderSide(color: Colors.white.withOpacity(0.1)),
        ),
      ),
      child: Row(
        children: [
          if (MediaQuery.of(context).size.width <= 900)
            IconButton(
              icon: const Icon(Icons.menu, color: Colors.white),
              onPressed: () {
                // TODO: Open drawer
              },
            ),
          
          const Spacer(),
          
          // User Menu
          PopupMenuButton<String>(
            offset: const Offset(0, 50),
            color: AppTheme.darkCard,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            child: Row(
              children: [
                CircleAvatar(
                  backgroundColor: AppTheme.primaryColor,
                  radius: 18,
                  child: Text(
                    controller.username.substring(0, 1).toUpperCase(),
                    style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                  ),
                ),
                const SizedBox(width: 8),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      controller.username,
                      style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w500),
                    ),
                    Text(
                      controller.userRole.toUpperCase(),
                      style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 11),
                    ),
                  ],
                ),
                const SizedBox(width: 8),
                Icon(Icons.keyboard_arrow_down, color: Colors.white.withOpacity(0.5)),
              ],
            ),
            itemBuilder: (context) => [
              PopupMenuItem(
                value: 'settings',
                child: Row(
                  children: const [
                    Icon(Icons.settings, color: Colors.white70, size: 20),
                    SizedBox(width: 12),
                    Text('Settings', style: TextStyle(color: Colors.white)),
                  ],
                ),
              ),
              PopupMenuItem(
                value: 'logout',
                child: Row(
                  children: const [
                    Icon(Icons.logout, color: AppTheme.errorColor, size: 20),
                    SizedBox(width: 12),
                    Text('Logout', style: TextStyle(color: AppTheme.errorColor)),
                  ],
                ),
              ),
            ],
            onSelected: (value) {
              if (value == 'logout') controller.logout();
              if (value == 'settings') controller.goToSettings();
            },
          ),
        ],
      ),
    );
  }
  
  Widget _buildWelcomeSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Welcome back, ${controller.username}! 👋',
          style: const TextStyle(
            fontSize: 28,
            fontWeight: FontWeight.bold,
            color: Colors.white,
          ),
        ),
        const SizedBox(height: 8),
        Text(
          'Here\'s what\'s happening with your AI insights today.',
          style: TextStyle(
            fontSize: 16,
            color: Colors.white.withOpacity(0.6),
          ),
        ),
      ],
    );
  }
  
  Widget _buildKPICards() {
    return Obx(() {
      if (controller.kpis.isEmpty) {
        return _buildEmptyState('No KPIs available');
      }
      
      return GridView.builder(
        shrinkWrap: true,
        physics: const NeverScrollableScrollPhysics(),
        gridDelegate: const SliverGridDelegateWithMaxCrossAxisExtent(
          maxCrossAxisExtent: 300,
          mainAxisSpacing: 16,
          crossAxisSpacing: 16,
          childAspectRatio: 1.5,
        ),
        itemCount: controller.kpis.length,
        itemBuilder: (context, index) {
          final kpi = controller.kpis[index];
          return _buildKPICard(kpi);
        },
      );
    });
  }
  
  Widget _buildKPICard(Map<String, dynamic> kpi) {
    final color = Color(int.parse(kpi['color']?.replaceFirst('#', '0xFF') ?? '0xFF6366F1'));
    final change = kpi['change'] as num?;
    final changeType = kpi['change_type'] as String?;
    
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            AppTheme.darkCard,
            color.withOpacity(0.1),
          ],
        ),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: color.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(
                  _getIconFromString(kpi['icon'] ?? 'analytics'),
                  color: color,
                  size: 24,
                ),
              ),
              if (change != null)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: changeType == 'increase'
                        ? Colors.green.withOpacity(0.2)
                        : changeType == 'decrease'
                            ? Colors.red.withOpacity(0.2)
                            : Colors.grey.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(
                        changeType == 'increase'
                            ? Icons.arrow_upward
                            : changeType == 'decrease'
                                ? Icons.arrow_downward
                                : Icons.remove,
                        size: 14,
                        color: changeType == 'increase'
                            ? Colors.green
                            : changeType == 'decrease'
                                ? Colors.red
                                : Colors.grey,
                      ),
                      const SizedBox(width: 4),
                      Text(
                        '${change.abs()}%',
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                          color: changeType == 'increase'
                              ? Colors.green
                              : changeType == 'decrease'
                                  ? Colors.red
                                  : Colors.grey,
                        ),
                      ),
                    ],
                  ),
                ),
            ],
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                kpi['value'] ?? '-',
                style: const TextStyle(
                  fontSize: 28,
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                kpi['title'] ?? '',
                style: TextStyle(
                  fontSize: 14,
                  color: Colors.white.withOpacity(0.6),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
  
  IconData _getIconFromString(String iconName) {
    switch (iconName) {
      case 'trending_up':
        return Icons.trending_up;
      case 'inventory_2':
        return Icons.inventory_2;
      case 'chat':
        return Icons.chat;
      case 'people':
        return Icons.people;
      case 'shopping_cart':
        return Icons.shopping_cart;
      case 'account_balance':
        return Icons.account_balance;
      default:
        return Icons.analytics;
    }
  }
  
  Widget _buildChartsSection() {
    return Obx(() {
      if (controller.charts.isEmpty) {
        return const SizedBox.shrink();
      }
      
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Analytics Overview',
            style: TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.bold,
              color: Colors.white,
            ),
          ),
          const SizedBox(height: 16),
          Container(
            height: 300,
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: AppTheme.darkCard,
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: Colors.white.withOpacity(0.1)),
            ),
            child: _buildBarChart(controller.charts.first),
          ),
        ],
      );
    });
  }
  
  Widget _buildBarChart(Map<String, dynamic> chartData) {
    final labels = List<String>.from(chartData['labels'] ?? []);
    final datasets = chartData['datasets'] as List?;
    final values = datasets != null && datasets.isNotEmpty
        ? List<double>.from((datasets[0]['data'] as List).map((e) => (e as num).toDouble()))
        : <double>[];
    
    if (labels.isEmpty || values.isEmpty) {
      return const Center(
        child: Text('No chart data', style: TextStyle(color: Colors.white54)),
      );
    }
    
    return BarChart(
      BarChartData(
        barTouchData: BarTouchData(
          touchTooltipData: BarTouchTooltipData(
            tooltipBgColor: AppTheme.darkSurface,
            getTooltipItem: (group, groupIndex, rod, rodIndex) {
              return BarTooltipItem(
                '${labels[group.x]}\n${values[group.x].toStringAsFixed(2)}',
                const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
              );
            },
          ),
        ),
        titlesData: FlTitlesData(
          show: true,
          bottomTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              getTitlesWidget: (value, meta) {
                final index = value.toInt();
                if (index < 0 || index >= labels.length) return const SizedBox();
                return Padding(
                  padding: const EdgeInsets.only(top: 8),
                  child: Text(
                    labels[index].length > 8 ? '${labels[index].substring(0, 8)}...' : labels[index],
                    style: TextStyle(color: Colors.white.withOpacity(0.6), fontSize: 10),
                  ),
                );
              },
            ),
          ),
          leftTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              reservedSize: 40,
              getTitlesWidget: (value, meta) {
                return Text(
                  value.toInt().toString(),
                  style: TextStyle(color: Colors.white.withOpacity(0.6), fontSize: 10),
                );
              },
            ),
          ),
          topTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
          rightTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
        ),
        borderData: FlBorderData(show: false),
        gridData: FlGridData(
          show: true,
          drawHorizontalLine: true,
          drawVerticalLine: false,
          horizontalInterval: values.isNotEmpty ? values.reduce((a, b) => a > b ? a : b) / 5 : 1,
          getDrawingHorizontalLine: (value) => FlLine(
            color: Colors.white.withOpacity(0.1),
            strokeWidth: 1,
          ),
        ),
        barGroups: List.generate(values.length, (index) {
          return BarChartGroupData(
            x: index,
            barRods: [
              BarChartRodData(
                toY: values[index],
                gradient: LinearGradient(
                  begin: Alignment.bottomCenter,
                  end: Alignment.topCenter,
                  colors: [AppTheme.primaryColor, AppTheme.secondaryColor],
                ),
                borderRadius: const BorderRadius.vertical(top: Radius.circular(6)),
                width: 20,
              ),
            ],
          );
        }),
      ),
    );
  }
  
  Widget _buildQuickActions() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Quick Actions',
          style: TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.bold,
            color: Colors.white,
          ),
        ),
        const SizedBox(height: 16),
        Wrap(
          spacing: 16,
          runSpacing: 16,
          children: [
            _buildActionCard(
              icon: Icons.chat,
              title: 'Ask AI',
              subtitle: 'Get instant insights',
              color: AppTheme.primaryColor,
              onTap: controller.goToAiAssistant,
            ),
            _buildActionCard(
              icon: Icons.settings,
              title: 'Settings',
              subtitle: 'Configure preferences',
              color: AppTheme.secondaryColor,
              onTap: controller.goToSettings,
            ),
          ],
        ),
      ],
    );
  }
  
  Widget _buildActionCard({
    required IconData icon,
    required String title,
    required String subtitle,
    required Color color,
    required VoidCallback onTap,
  }) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: Container(
          width: 200,
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: AppTheme.darkCard,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: color.withOpacity(0.3)),
          ),
          child: Row(
            children: [
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: color.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(icon, color: color, size: 24),
              ),
              const SizedBox(width: 16),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: const TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.w600,
                      fontSize: 16,
                    ),
                  ),
                  Text(
                    subtitle,
                    style: TextStyle(
                      color: Colors.white.withOpacity(0.5),
                      fontSize: 12,
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
  
  Widget _buildEmptyState(String message) {
    return Container(
      padding: const EdgeInsets.all(40),
      child: Center(
        child: Text(
          message,
          style: TextStyle(color: Colors.white.withOpacity(0.5)),
        ),
      ),
    );
  }
  
  Widget _buildBottomNav() {
    return Obx(() => NavigationBar(
      backgroundColor: AppTheme.darkSurface,
      selectedIndex: controller.selectedNavIndex.value,
      onDestinationSelected: controller.selectNavItem,
      destinations: [
        const NavigationDestination(
          icon: Icon(Icons.dashboard_outlined),
          selectedIcon: Icon(Icons.dashboard),
          label: 'Dashboard',
        ),
        const NavigationDestination(
          icon: Icon(Icons.chat_outlined),
          selectedIcon: Icon(Icons.chat),
          label: 'AI Chat',
        ),
        const NavigationDestination(
          icon: Icon(Icons.settings_outlined),
          selectedIcon: Icon(Icons.settings),
          label: 'Settings',
        ),
      ],
    ));
  }
}
