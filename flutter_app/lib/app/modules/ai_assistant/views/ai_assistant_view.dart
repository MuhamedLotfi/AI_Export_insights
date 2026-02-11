import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:get/get.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import '../controllers/ai_assistant_controller.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../models/chat_message.dart';
import '../../../routes/app_routes.dart';

class AiAssistantView extends GetView<AiAssistantController> {
  const AiAssistantView({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final isWideScreen = MediaQuery.of(context).size.width > 900;
    
    return Scaffold(
      backgroundColor: AppTheme.darkBackground,
      appBar: _buildAppBar(),
      body: isWideScreen
          ? Row(
              children: [
                // Conversation History Sidebar
                _buildHistorySidebar(),
                
                // Vertical Divider
                Container(
                  width: 1,
                  color: Colors.white.withOpacity(0.1),
                ),
                
                // Main Chat Area
                Expanded(
                  child: _buildMainContent(),
                ),
              ],
            )
          : Column(
              children: [
                // Tab Bar for mobile
                _buildTabBar(),
                
                // Tab Content
                Expanded(
                  child: TabBarView(
                    controller: controller.tabController,
                    children: [
                      _buildChatTab(),
                      _buildMemoryTab(),
                    ],
                  ),
                ),
              ],
            ),
    );
  }
  
  Widget _buildHistorySidebar() {
    return Container(
      width: 280,
      color: AppTheme.darkSurface,
      child: Column(
        children: [
          // New Chat Button
          Padding(
            padding: const EdgeInsets.all(16),
            child: SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: controller.startNewChat,
                icon: const Icon(Icons.add, size: 20),
                label: const Text('New Chat'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppTheme.primaryColor,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
              ),
            ),
          ),
          
          // Search (optional, for future)
          // Padding(
          //   padding: const EdgeInsets.symmetric(horizontal: 16),
          //   child: TextField(...),
          // ),
          
          // History List
          Expanded(
            child: Obx(() {
              if (controller.isLoadingHistory.value && controller.sessionHistory.isEmpty) {
                return const Center(
                  child: CircularProgressIndicator(color: AppTheme.primaryColor),
                );
              }
              
              if (controller.sessionHistory.isEmpty) {
                return Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.chat_bubble_outline, 
                          size: 48, 
                          color: Colors.white.withOpacity(0.3)),
                      const SizedBox(height: 12),
                      Text(
                        'No conversations yet',
                        style: TextStyle(color: Colors.white.withOpacity(0.5)),
                      ),
                    ],
                  ),
                );
              }
              
              return ListView.builder(
                padding: const EdgeInsets.symmetric(horizontal: 12),
                itemCount: controller.sessionHistory.length + (controller.hasMoreHistory.value ? 1 : 0),
                itemBuilder: (context, index) {
                  if (index >= controller.sessionHistory.length) {
                    // Load More button
                    return Padding(
                      padding: const EdgeInsets.symmetric(vertical: 8),
                      child: TextButton(
                        onPressed: controller.loadMoreHistory,
                        child: Obx(() => controller.isLoadingHistory.value
                            ? const SizedBox(
                                width: 20,
                                height: 20,
                                child: CircularProgressIndicator(strokeWidth: 2),
                              )
                            : const Text('Load More')),
                      ),
                    );
                  }
                  
                  return _buildSessionItem(controller.sessionHistory[index]);
                },
              );
            }),
          ),
        ],
      ),
    );
  }
  
  Widget _buildSessionItem(Map<String, dynamic> session) {
    final sessionId = session['session_id'] ?? '';
    final title = session['title'] ?? 'Conversation';
    final messageCount = session['message_count'] ?? 0;
    final firstMessage = session['first_message'] ?? '';
    final query = session['query'] ?? title;
    
    // Format date
    String formattedDate = '';
    if (firstMessage.isNotEmpty) {
      try {
        final date = DateTime.parse(firstMessage);
        final now = DateTime.now();
        final diff = now.difference(date);
        
        if (diff.inDays == 0) {
          formattedDate = 'Today';
        } else if (diff.inDays == 1) {
          formattedDate = 'Yesterday';
        } else if (diff.inDays < 7) {
          formattedDate = '${diff.inDays} days ago';
        } else {
          formattedDate = '${date.month}/${date.day}';
        }
      } catch (_) {}
    }
    
    return Obx(() {
      final isActive = controller.currentSessionId.value == sessionId;
      
      return Container(
        margin: const EdgeInsets.only(bottom: 6),
        child: Material(
          color: isActive 
              ? AppTheme.primaryColor.withOpacity(0.2)
              : Colors.transparent,
          borderRadius: BorderRadius.circular(10),
          child: InkWell(
            onTap: () => controller.loadSessionMessages(sessionId),
            borderRadius: BorderRadius.circular(10),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(10),
                border: isActive 
                    ? Border.all(color: AppTheme.primaryColor.withOpacity(0.5))
                    : null,
              ),
              child: Row(
                children: [
                  // Chat Icon
                  Container(
                    width: 36,
                    height: 36,
                    decoration: BoxDecoration(
                      color: isActive 
                          ? AppTheme.primaryColor.withOpacity(0.3)
                          : Colors.white.withOpacity(0.05),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Icon(
                      Icons.chat_bubble_outline,
                      size: 18,
                      color: isActive ? AppTheme.primaryColor : Colors.white54,
                    ),
                  ),
                  const SizedBox(width: 10),
                  
                  // Title and metadata
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          query.length > 30 ? '${query.substring(0, 30)}...' : query,
                          style: TextStyle(
                            color: isActive ? Colors.white : Colors.white.withOpacity(0.8),
                            fontWeight: isActive ? FontWeight.w600 : FontWeight.normal,
                            fontSize: 13,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                        const SizedBox(height: 2),
                        Row(
                          children: [
                            Text(
                              formattedDate,
                              style: TextStyle(
                                color: Colors.white.withOpacity(0.4),
                                fontSize: 11,
                              ),
                            ),
                            if (messageCount > 0) ...[
                              Text(
                                ' • ',
                                style: TextStyle(color: Colors.white.withOpacity(0.3)),
                              ),
                              Text(
                                '$messageCount msgs',
                                style: TextStyle(
                                  color: Colors.white.withOpacity(0.4),
                                  fontSize: 11,
                                ),
                              ),
                            ],
                          ],
                        ),
                      ],
                    ),
                  ),
                  
                  // Delete button on hover/active
                  if (isActive)
                    IconButton(
                      onPressed: () => _showDeleteConfirmation(sessionId),
                      icon: Icon(
                        Icons.delete_outline,
                        size: 18,
                        color: Colors.white.withOpacity(0.5),
                      ),
                      padding: EdgeInsets.zero,
                      constraints: const BoxConstraints(),
                    ),
                ],
              ),
            ),
          ),
        ),
      );
    });
  }
  
  void _showDeleteConfirmation(String sessionId) {
    Get.dialog(
      AlertDialog(
        backgroundColor: AppTheme.darkCard,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Text('Delete Conversation?', style: TextStyle(color: Colors.white)),
        content: const Text(
          'This conversation will be permanently deleted.',
          style: TextStyle(color: Colors.white70),
        ),
        actions: [
          TextButton(
            onPressed: () => Get.back(),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () {
              Get.back();
              controller.deleteSession(sessionId);
            },
            style: ElevatedButton.styleFrom(backgroundColor: AppTheme.errorColor),
            child: const Text('Delete'),
          ),
        ],
      ),
    );
  }
  
  Widget _buildMainContent() {
    return Column(
      children: [
        Expanded(child: _buildChatTab()),
      ],
    );
  }
  
  PreferredSizeWidget _buildAppBar() {
    return AppBar(
      backgroundColor: AppTheme.darkSurface,
      leading: IconButton(
        icon: const Icon(Icons.arrow_back, color: Colors.white),
        onPressed: () => Get.offNamed(AppRoutes.dashboard),
      ),
      title: Row(
        children: [
          Container(
            width: 36,
            height: 36,
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [AppTheme.primaryColor, AppTheme.secondaryColor],
              ),
              borderRadius: BorderRadius.circular(10),
            ),
            child: const Icon(Icons.smart_toy, color: Colors.white, size: 20),
          ),
          const SizedBox(width: 12),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'AI Assistant',
                style: TextStyle(color: Colors.white, fontWeight: FontWeight.w600, fontSize: 16),
              ),
              Obx(() => Text(
                controller.currentSessionId.value.isNotEmpty 
                    ? 'Session: ${controller.currentSessionId.value.substring(0, 12)}...'
                    : 'New Session',
                style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 11),
              )),
            ],
          ),
        ],
      ),
      actions: [
        // Agent Pills
        Obx(() => Padding(
          padding: const EdgeInsets.only(right: 8),
          child: Wrap(
            spacing: 8,
            children: controller.assignedAgents.take(3).map((agent) {
              return Chip(
                label: Text(
                  agent.toUpperCase(),
                  style: const TextStyle(fontSize: 10, color: Colors.white),
                ),
                backgroundColor: AppTheme.primaryColor.withOpacity(0.3),
                padding: EdgeInsets.zero,
                materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
              );
            }).toList(),
          ),
        )),
        
        // Settings
        PopupMenuButton<String>(
          icon: const Icon(Icons.more_vert, color: Colors.white),
          color: AppTheme.darkCard,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          itemBuilder: (context) => [
            PopupMenuItem(
              value: 'trace',
              child: Obx(() => Row(
                children: [
                  Icon(
                    controller.showThinkingTrace.value ? Icons.visibility : Icons.visibility_off,
                    color: Colors.white70,
                    size: 20,
                  ),
                  const SizedBox(width: 12),
                  Text(
                    controller.showThinkingTrace.value ? 'Hide Trace' : 'Show Trace',
                    style: const TextStyle(color: Colors.white),
                  ),
                ],
              )),
            ),
            PopupMenuItem(
              value: 'new',
              child: Row(
                children: const [
                  Icon(Icons.add_circle_outline, color: Colors.white70, size: 20),
                  SizedBox(width: 12),
                  Text('New Chat', style: TextStyle(color: Colors.white)),
                ],
              ),
            ),
            PopupMenuItem(
              value: 'clear',
              child: Row(
                children: const [
                  Icon(Icons.delete_outline, color: AppTheme.errorColor, size: 20),
                  SizedBox(width: 12),
                  Text('Clear All Memory', style: TextStyle(color: AppTheme.errorColor)),
                ],
              ),
            ),
          ],
          onSelected: (value) {
            if (value == 'trace') controller.toggleThinkingTrace();
            if (value == 'new') controller.startNewChat();
            if (value == 'clear') _showClearConfirmation();
          },
        ),
      ],
    );
  }
  
  void _showClearConfirmation() {
    Get.dialog(
      AlertDialog(
        backgroundColor: AppTheme.darkCard,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Text('Clear All Memory?', style: TextStyle(color: Colors.white)),
        content: const Text(
          'This will clear ALL conversation history. This action cannot be undone.',
          style: TextStyle(color: Colors.white70),
        ),
        actions: [
          TextButton(
            onPressed: () => Get.back(),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () {
              Get.back();
              controller.clearMemory();
            },
            style: ElevatedButton.styleFrom(backgroundColor: AppTheme.errorColor),
            child: const Text('Clear All'),
          ),
        ],
      ),
    );
  }
  
  Widget _buildTabBar() {
    return Container(
      color: AppTheme.darkSurface,
      child: TabBar(
        controller: controller.tabController,
        indicatorColor: AppTheme.primaryColor,
        indicatorWeight: 3,
        labelColor: AppTheme.primaryColor,
        unselectedLabelColor: Colors.white54,
        tabs: const [
          Tab(
            icon: Icon(Icons.chat_bubble_outline),
            text: 'Chat',
          ),
          Tab(
            icon: Icon(Icons.history),
            text: 'History',
          ),
        ],
      ),
    );
  }
  
  Widget _buildChatTab() {
    return Column(
      children: [
        // Chat Messages
        Expanded(
          child: Obx(() {
            if (controller.messages.isEmpty) {
              return _buildEmptyChat();
            }
            
            return ListView.builder(
              controller: controller.chatScrollController,
              padding: const EdgeInsets.all(16),
              itemCount: controller.messages.length,
              itemBuilder: (context, index) {
                return _buildMessageItem(controller.messages[index]);
              },
            );
          }),
        ),
        
        // Processing indicator
        Obx(() => controller.isProcessing.value
          ? Container(
              padding: const EdgeInsets.symmetric(vertical: 8),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      color: AppTheme.primaryColor,
                    ),
                  ),
                  const SizedBox(width: 8),
                  const SizedBox(width: 8),
                  Obx(() {
                    final duration = controller.processingDuration.value;
                    final text = duration > 1.0 
                        ? 'AI is thinking... (${duration.toStringAsFixed(1)}s)'
                        : 'AI is thinking...';
                    return Text(
                      text,
                      style: TextStyle(color: Colors.white.withOpacity(0.6)),
                    );
                  }),
                ],
              ),
            )
          : const SizedBox.shrink()
        ),
        
        // Input Area
        _buildInputArea(),
      ],
    );
  }
  
  Widget _buildEmptyChat() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 80,
              height: 80,
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [AppTheme.primaryColor.withOpacity(0.3), AppTheme.secondaryColor.withOpacity(0.3)],
                ),
                borderRadius: BorderRadius.circular(20),
              ),
              child: const Icon(Icons.chat_bubble_outline, color: AppTheme.primaryColor, size: 40),
            ),
            const SizedBox(height: 24),
            const Text(
              'Start a Conversation',
              style: TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
                color: Colors.white,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'Ask questions about your data using natural language',
              style: TextStyle(color: Colors.white.withOpacity(0.6)),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 32),
            
            // Quick Queries
            const Text(
              'Try these:',
              style: TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.w600,
                color: Colors.white70,
              ),
            ),
            const SizedBox(height: 16),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              alignment: WrapAlignment.center,
              children: controller.quickQueries.map((query) {
                return ActionChip(
                  label: Text(query),
                  labelStyle: const TextStyle(color: Colors.white, fontSize: 12),
                  backgroundColor: AppTheme.darkCard,
                  side: BorderSide(color: AppTheme.primaryColor.withOpacity(0.5)),
                  onPressed: () => controller.sendQuickQuery(query),
                );
              }).toList(),
            ),
          ],
        ),
      ),
    );
  }
  
  Widget _buildMessageItem(ChatMessage message) {
    if (message.isUser) {
      return _buildUserMessage(message);
    } else {
      return _buildAiMessage(message);
    }
  }
  
  Widget _buildUserMessage(ChatMessage message) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16, left: 40),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.end,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Flexible(
            child: Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [AppTheme.primaryColor, AppTheme.secondaryColor],
                ),
                borderRadius: const BorderRadius.only(
                  topLeft: Radius.circular(16),
                  topRight: Radius.circular(16),
                  bottomLeft: Radius.circular(16),
                  bottomRight: Radius.circular(4),
                ),
              ),
              child: Text(
                message.query,
                style: const TextStyle(color: Colors.white),
              ),
            ),
          ),
          const SizedBox(width: 8),
          CircleAvatar(
            radius: 16,
            backgroundColor: AppTheme.primaryColor,
            child: const Icon(Icons.person, color: Colors.white, size: 18),
          ),
        ],
      ),
    );
  }
  
  Widget _buildAiMessage(ChatMessage message) {
    // Calculate duration text if available
    String durationText = '';
    if (message.metadata != null && message.metadata!['duration_ms'] != null) {
      final ms = message.metadata!['duration_ms'];
      if (ms > 1000) {
        durationText = '${(ms / 1000).toStringAsFixed(2)}s';
      } else {
        durationText = '${ms.toInt()}ms';
      }
    }

    return Container(
      margin: const EdgeInsets.only(bottom: 24, right: 32),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Professional Avatar
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [AppTheme.secondaryColor, AppTheme.primaryColor],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              shape: BoxShape.circle,
              boxShadow: [
                BoxShadow(
                  color: AppTheme.primaryColor.withOpacity(0.3),
                  blurRadius: 8,
                  offset: const Offset(0, 4),
                ),
              ],
            ),
            child: const Icon(Icons.auto_awesome, color: Colors.white, size: 20),
          ),
          const SizedBox(width: 12),
          
          Flexible(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Main Content Card
                Container(
                  padding: const EdgeInsets.all(20),
                  decoration: BoxDecoration(
                    color: message.hasError ? AppTheme.errorColor.withOpacity(0.1) : AppTheme.darkCard,
                    borderRadius: const BorderRadius.only(
                      topLeft: Radius.circular(4),
                      topRight: Radius.circular(20),
                      bottomLeft: Radius.circular(20),
                      bottomRight: Radius.circular(20),
                    ),
                    border: Border.all(
                      color: message.hasError 
                          ? AppTheme.errorColor.withOpacity(0.3) 
                          : Colors.white.withOpacity(0.05),
                    ),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withOpacity(0.2),
                        blurRadius: 10,
                        offset: const Offset(0, 4),
                      ),
                    ],
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Header: Agents Used
                      if (message.agentsUsed.isNotEmpty)
                        Padding(
                          padding: const EdgeInsets.only(bottom: 16),
                          child: Wrap(
                            spacing: 8,
                            children: message.agentsUsed.map((agent) {
                              return Container(
                                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                                decoration: BoxDecoration(
                                  color: AppTheme.primaryColor.withOpacity(0.1),
                                  borderRadius: BorderRadius.circular(20),
                                  border: Border.all(color: AppTheme.primaryColor.withOpacity(0.3)),
                                ),
                                child: Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    Icon(Icons.token, size: 12, color: AppTheme.accentColor),
                                    const SizedBox(width: 4),
                                    Text(
                                      agent.toUpperCase(),
                                      style: const TextStyle(
                                        fontSize: 10,
                                        color: AppTheme.accentColor,
                                        fontWeight: FontWeight.w600,
                                        letterSpacing: 0.5,
                                      ),
                                    ),
                                  ],
                                ),
                              );
                            }).toList(),
                          ),
                        ),
                      
                      // Answer Content
                      MarkdownBody(
                        data: message.answer,
                        selectable: true,
                        styleSheet: MarkdownStyleSheet(
                          p: const TextStyle(color: Colors.white, height: 1.5, fontSize: 15),
                          h1: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 24),
                          h2: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 20),
                          h3: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 18),
                          strong: const TextStyle(color: AppTheme.accentColor, fontWeight: FontWeight.w600),
                          em: const TextStyle(color: Colors.white70, fontStyle: FontStyle.italic),
                          listBullet: const TextStyle(color: AppTheme.secondaryColor),
                          blockquote: TextStyle(color: Colors.white70, fontStyle: FontStyle.italic),
                          blockquoteDecoration: BoxDecoration(
                            border: Border(left: BorderSide(color: AppTheme.secondaryColor, width: 4)),
                            color: Colors.white.withOpacity(0.05),
                            borderRadius: BorderRadius.circular(4),
                          ),
                          code: TextStyle(
                            backgroundColor: Colors.black.withOpacity(0.3),
                            color: AppTheme.accentColor,
                            fontFamily: 'monospace',
                            fontSize: 13,
                          ),
                          codeblockDecoration: BoxDecoration(
                            color: Colors.black.withOpacity(0.3),
                            borderRadius: BorderRadius.circular(8),
                            border: Border.all(color: Colors.white.withOpacity(0.1)),
                          ),
                        ),
                      ),
                      
                      // Chart
                      if (message.chartData != null)
                        _buildChart(message.chartData!),
                      
                      // Insights and Data Preview removed as per requirement

                      // Thinking Trace
                      Obx(() {
                        if (controller.showThinkingTrace.value && message.thinkingTrace != null) {
                          return _buildThinkingTrace(message.thinkingTrace!);
                        }
                        return const SizedBox.shrink();
                      }),
                      
                      // Blocked Agents Warning
                      if (message.agentsBlocked.isNotEmpty)
                        Padding(
                          padding: const EdgeInsets.only(top: 12),
                          child: Container(
                            padding: const EdgeInsets.all(12),
                            decoration: BoxDecoration(
                              color: AppTheme.warningColor.withOpacity(0.1),
                              borderRadius: BorderRadius.circular(8),
                              border: Border.all(color: AppTheme.warningColor.withOpacity(0.3)),
                            ),
                            child: Row(
                              children: [
                                const Icon(Icons.warning_amber, color: AppTheme.warningColor, size: 18),
                                const SizedBox(width: 8),
                                Expanded(
                                  child: Text(
                                    'Access denied: ${message.agentsBlocked.join(", ")}',
                                    style: const TextStyle(color: AppTheme.warningColor, fontSize: 12),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                    ],
                  ),
                ),
                
                // Footer: Actions & Metadata
                Padding(
                  padding: const EdgeInsets.only(top: 8, left: 4),
                  child: Row(
                    children: [
                      // Duration
                      if (durationText.isNotEmpty)
                        Container(
                          margin: const EdgeInsets.only(right: 16),
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                          decoration: BoxDecoration(
                            color: Colors.white.withOpacity(0.05),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Row(
                            children: [
                              const Icon(Icons.timer_outlined, size: 12, color: Colors.white54),
                              const SizedBox(width: 4),
                              Text(
                                durationText,
                                style: const TextStyle(color: Colors.white54, fontSize: 11),
                              ),
                            ],
                          ),
                        ),
                        
                      // Copy Query
                      _buildActionIcon(
                        Icons.copy_all, 
                        'Copy Q&A', 
                        () {
                          Clipboard.setData(ClipboardData(text: 'Q: ${message.query}\n\nA: ${message.answer}'));
                          Get.snackbar('Copied', 'Conversation copied to clipboard', 
                            snackPosition: SnackPosition.BOTTOM, 
                            duration: const Duration(seconds: 1),
                            backgroundColor: AppTheme.primaryColor,
                            colorText: Colors.white,
                            margin: const EdgeInsets.all(16),
                            borderRadius: 12,
                          );
                        }
                      ),
                      
                      const SizedBox(width: 8),
                      
                      // Copy Answer Only
                      _buildActionIcon(
                        Icons.content_copy, 
                        'Copy Answer', 
                        () {
                          Clipboard.setData(ClipboardData(text: message.answer));
                          Get.snackbar('Copied', 'Answer copied to clipboard',
                            snackPosition: SnackPosition.BOTTOM,
                            duration: const Duration(seconds: 1),
                            backgroundColor: AppTheme.darkCard,
                            colorText: Colors.white,
                            margin: const EdgeInsets.all(16),
                            borderRadius: 12,
                          );
                        }
                      ),
                      
                      const SizedBox(width: 8),
                      
                      // Feedback Buttons
                      if (message.messageId != null) ...[
                         Container(width: 1, height: 16, color: Colors.white.withOpacity(0.1)),
                         const SizedBox(width: 8),
                         _buildActionIcon(
                          Icons.thumb_up_outlined,
                          'Helpful',
                          () => controller.submitFeedback(message.messageId!, true),
                        ),
                        _buildActionIcon(
                          Icons.thumb_down_outlined,
                          'Not Helpful',
                          () => controller.submitFeedback(message.messageId!, false),
                        ),
                      ],
                    ],
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildActionIcon(IconData icon, String tooltip, VoidCallback onTap) {
    return Tooltip(
      message: tooltip,
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(20),
          child: Padding(
            padding: const EdgeInsets.all(6),
            child: Icon(icon, size: 16, color: Colors.white38),
          ),
        ),
      ),
    );
  }
  
  Widget _buildChart(Map<String, dynamic> chartData) {
    final type = chartData['type'] as String? ?? 'bar';
    final labels = List<String>.from(chartData['labels'] ?? []);
    final datasets = chartData['datasets'] as List?;
    
    if (labels.isEmpty || datasets == null || datasets.isEmpty) {
      return const SizedBox.shrink();
    }
    
    final values = List<double>.from(
      (datasets[0]['data'] as List).map((e) => (e as num).toDouble())
    );
    
    return Container(
      margin: const EdgeInsets.only(top: 12),
      height: 250,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.darkSurface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.white.withOpacity(0.1)),
      ),
      child: type == 'pie'
          ? _buildPieChart(labels, values)
          : _buildBarChartWidget(labels, values),
    );
  }
  
  Widget _buildPieChart(List<String> labels, List<double> values) {
    final colors = [
      AppTheme.primaryColor,
      AppTheme.secondaryColor,
      AppTheme.accentColor,
      AppTheme.warningColor,
      const Color(0xFFEC4899),
      const Color(0xFF3B82F6),
    ];
    
    return PieChart(
      PieChartData(
        sectionsSpace: 2,
        centerSpaceRadius: 50,
        sections: List.generate(values.length.clamp(0, 6), (index) {
          final total = values.reduce((a, b) => a + b);
          final percentage = (values[index] / total * 100).toStringAsFixed(1);
          
          return PieChartSectionData(
            value: values[index],
            title: '$percentage%',
            titleStyle: const TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.bold),
            color: colors[index % colors.length],
            radius: 60,
          );
        }),
      ),
    );
  }
  
  Widget _buildBarChartWidget(List<String> labels, List<double> values) {
    return BarChart(
      BarChartData(
        barTouchData: BarTouchData(enabled: true),
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
                    labels[index].length > 6 ? '${labels[index].substring(0, 6)}...' : labels[index],
                    style: TextStyle(color: Colors.white.withOpacity(0.6), fontSize: 9),
                  ),
                );
              },
            ),
          ),
          leftTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
          topTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
          rightTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
        ),
        borderData: FlBorderData(show: false),
        gridData: FlGridData(show: false),
        barGroups: List.generate(values.length.clamp(0, 10), (index) {
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
                borderRadius: const BorderRadius.vertical(top: Radius.circular(4)),
                width: 16,
              ),
            ],
          );
        }),
      ),
    );
  }
  
  Widget _buildInsights(List<Map<String, dynamic>> insights) {
    return Container(
      margin: const EdgeInsets.only(top: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Key Insights',
            style: TextStyle(
              color: Colors.white.withOpacity(0.7),
              fontSize: 12,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: insights.take(3).map((insight) {
              return Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                decoration: BoxDecoration(
                  color: AppTheme.primaryColor.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: AppTheme.primaryColor.withOpacity(0.3)),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      insight['title'] ?? '',
                      style: const TextStyle(
                        color: AppTheme.primaryColor,
                        fontSize: 11,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    Text(
                      insight['value'] ?? '',
                      style: const TextStyle(color: Colors.white, fontSize: 13),
                    ),
                  ],
                ),
              );
            }).toList(),
          ),
        ],
      ),
    );
  }
  
  Widget _buildDataPreview(List<Map<String, dynamic>> data) {
    if (data.isEmpty) return const SizedBox.shrink();
    
    return Container(
      margin: const EdgeInsets.only(top: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'Data (${data.length} rows)',
                style: TextStyle(
                  color: Colors.white.withOpacity(0.7),
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                ),
              ),
              TextButton.icon(
                onPressed: () {
                  // TODO: Show full data dialog
                },
                icon: const Icon(Icons.fullscreen, size: 16),
                label: const Text('Expand', style: TextStyle(fontSize: 12)),
              ),
            ],
          ),
          Container(
            decoration: BoxDecoration(
              color: AppTheme.darkSurface,
              borderRadius: BorderRadius.circular(8),
            ),
            clipBehavior: Clip.antiAlias,
            child: SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: DataTable(
                headingRowColor: MaterialStateProperty.all(Colors.white.withOpacity(0.05)),
                columns: data.first.keys.take(5).map((key) {
                  return DataColumn(
                    label: Text(
                      key.toString(),
                      style: const TextStyle(color: Colors.white70, fontWeight: FontWeight.w600),
                    ),
                  );
                }).toList(),
                rows: data.take(5).map((row) {
                  return DataRow(
                    cells: row.keys.take(5).map((key) {
                      return DataCell(
                        Text(
                          row[key]?.toString() ?? '-',
                          style: const TextStyle(color: Colors.white),
                        ),
                      );
                    }).toList(),
                  );
                }).toList(),
              ),
            ),
          ),
        ],
      ),
    );
  }
  
  Widget _buildThinkingTrace(Map<String, dynamic> trace) {
    return Container(
      margin: const EdgeInsets.only(top: 12),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.black.withOpacity(0.3),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.white.withOpacity(0.1)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.psychology, color: Colors.white.withOpacity(0.5), size: 16),
              const SizedBox(width: 8),
              Text(
                'Thinking Trace',
                style: TextStyle(
                  color: Colors.white.withOpacity(0.5),
                  fontSize: 11,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            'Query: ${trace['query'] ?? ''}',
            style: TextStyle(color: Colors.white.withOpacity(0.6), fontSize: 11),
          ),
          Text(
            'Type: ${trace['query_type'] ?? ''}',
            style: TextStyle(color: Colors.white.withOpacity(0.6), fontSize: 11),
          ),
          Text(
            'Tool: ${trace['tool'] ?? ''}',
            style: TextStyle(color: Colors.white.withOpacity(0.6), fontSize: 11),
          ),
          Text(
            'Domains: ${(trace['allowed_domains'] as List?)?.join(", ") ?? ''}',
            style: TextStyle(color: Colors.white.withOpacity(0.6), fontSize: 11),
          ),
        ],
      ),
    );
  }
  
  Widget _buildInputArea() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.darkSurface,
        border: Border(
          top: BorderSide(color: Colors.white.withOpacity(0.1)),
        ),
      ),
      child: SafeArea(
        child: Row(
          children: [
            Expanded(
              child: TextField(
                controller: controller.queryController,
                style: const TextStyle(color: Colors.white),
                maxLines: null,
                decoration: InputDecoration(
                  hintText: 'Ask anything about your data...',
                  hintStyle: TextStyle(color: Colors.white.withOpacity(0.4)),
                  filled: true,
                  fillColor: AppTheme.darkCard,
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(24),
                    borderSide: BorderSide.none,
                  ),
                  contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
                ),
                onSubmitted: (_) => controller.sendQuery(),
              ),
            ),
            const SizedBox(width: 12),
            Obx(() => Container(
              decoration: BoxDecoration(
                gradient: controller.isProcessing.value
                    ? null
                    : LinearGradient(colors: [AppTheme.primaryColor, AppTheme.secondaryColor]),
                color: controller.isProcessing.value ? Colors.grey : null,
                shape: BoxShape.circle,
              ),
              child: IconButton(
                onPressed: controller.isProcessing.value ? null : controller.sendQuery,
                icon: controller.isProcessing.value
                    ? const SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                      )
                    : const Icon(Icons.send, color: Colors.white),
              ),
            )),
          ],
        ),
      ),
    );
  }
  
  Widget _buildMemoryTab() {
    return Obx(() {
      if (controller.isLoadingMemory.value) {
        return const Center(
          child: CircularProgressIndicator(color: AppTheme.primaryColor),
        );
      }
      
      if (controller.conversationHistory.isEmpty) {
        return _buildEmptyMemory();
      }
      
      return RefreshIndicator(
        onRefresh: controller.refresh,
        child: ListView.builder(
          padding: const EdgeInsets.all(16),
          itemCount: controller.conversationHistory.length,
          itemBuilder: (context, index) {
            final conv = controller.conversationHistory[index];
            return _buildConversationCard(conv);
          },
        ),
      );
    });
  }
  
  Widget _buildEmptyMemory() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.history, size: 60, color: Colors.white.withOpacity(0.3)),
          const SizedBox(height: 16),
          const Text(
            'No Conversation History',
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.w600,
              color: Colors.white,
            ),
          ),
          Text(
            'Your conversations will appear here',
            style: TextStyle(color: Colors.white.withOpacity(0.5)),
          ),
        ],
      ),
    );
  }
  
  Widget _buildConversationCard(Map<String, dynamic> conv) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      child: Material(
        color: AppTheme.darkCard,
        borderRadius: BorderRadius.circular(12),
        child: InkWell(
          onTap: () {
            final sessionId = conv['session_id'] ?? conv['conversation_id'];
            if (sessionId != null) {
              controller.loadSessionMessages(sessionId);
              controller.tabController.animateTo(0); // Switch to chat tab
            }
          },
          borderRadius: BorderRadius.circular(12),
          child: Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: Colors.white.withOpacity(0.1)),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Query
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Icon(Icons.person, color: AppTheme.primaryColor, size: 18),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        conv['query'] ?? conv['title'] ?? '',
                        style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w500),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                
                // Response
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Icon(Icons.smart_toy, color: AppTheme.secondaryColor, size: 18),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        (conv['response'] ?? '').toString().length > 200
                            ? '${(conv['response'] ?? '').toString().substring(0, 200)}...'
                            : conv['response'] ?? '',
                        style: TextStyle(color: Colors.white.withOpacity(0.7)),
                      ),
                    ),
                  ],
                ),
                
                // Metadata
                const SizedBox(height: 12),
                Row(
                  children: [
                    Icon(Icons.access_time, color: Colors.white.withOpacity(0.4), size: 14),
                    const SizedBox(width: 4),
                    Text(
                      conv['timestamp'] ?? conv['first_message'] ?? '',
                      style: TextStyle(color: Colors.white.withOpacity(0.4), fontSize: 12),
                    ),
                    const Spacer(),
                    if ((conv['agents_used'] as List?)?.isNotEmpty ?? false)
                      ...((conv['agents_used'] as List).map((agent) {
                        return Container(
                          margin: const EdgeInsets.only(left: 4),
                          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                          decoration: BoxDecoration(
                            color: AppTheme.primaryColor.withOpacity(0.2),
                            borderRadius: BorderRadius.circular(4),
                          ),
                          child: Text(
                            agent.toString().toUpperCase(),
                            style: const TextStyle(
                              color: AppTheme.primaryColor,
                              fontSize: 10,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        );
                      })),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
