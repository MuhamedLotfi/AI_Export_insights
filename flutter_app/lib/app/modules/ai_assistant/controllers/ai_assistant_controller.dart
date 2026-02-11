import 'package:flutter/material.dart';
import 'dart:async';
import 'package:get/get.dart';
import '../../../../config/api_config.dart';
import '../../../data/services/api_service.dart';
import '../../../data/services/log_service.dart';
import '../../../models/chat_message.dart';
import '../../../models/domain_agent.dart';
import '../../../services/auth_service.dart';


class AiAssistantController extends GetxController with GetSingleTickerProviderStateMixin {
  final ApiService _apiService = Get.find<ApiService>();
  final AuthService _authService = Get.find<AuthService>();
  final LogService _logger = LogService.instance;
  
  late TabController tabController;
  
  final TextEditingController queryController = TextEditingController();
  final ScrollController chatScrollController = ScrollController();
  
  // Tab index
  final RxInt currentTabIndex = 0.obs;
  
  // Chat state
  final RxList<ChatMessage> messages = <ChatMessage>[].obs;
  final RxBool isProcessing = false.obs;
  final RxDouble processingDuration = 0.0.obs;
  Timer? _processingTimer;
  final RxBool showThinkingTrace = true.obs;
  
  // Session management
  final RxString currentSessionId = ''.obs;
  final RxList<Map<String, dynamic>> sessionHistory = <Map<String, dynamic>>[].obs;
  final RxBool isLoadingHistory = false.obs;
  final RxBool hasMoreHistory = true.obs;
  final RxInt historyOffset = 0.obs;
  static const int historyLimit = 10;
  
  // Agent state
  final RxList<String> assignedAgents = <String>[].obs;
  final RxList<DomainAgent> allAgents = <DomainAgent>[].obs;
  final Rx<Map<String, dynamic>?> lastThinkingTrace = Rx<Map<String, dynamic>?>(null);
  
  // Memory state (legacy - for backward compatibility)
  final RxList<Map<String, dynamic>> conversationHistory = <Map<String, dynamic>>[].obs;
  final RxBool isLoadingMemory = false.obs;
  
  @override
  void onInit() {
    super.onInit();
    tabController = TabController(length: 2, vsync: this);
    tabController.addListener(() {
      currentTabIndex.value = tabController.index;
    });
    
    _loadAgentState();
    _loadSessionHistory();
  }
  
  @override
  void onClose() {
    tabController.dispose();
    queryController.dispose();
    chatScrollController.dispose();
    chatScrollController.dispose();
    _stopTimer();
    super.onClose();
  }

  void _startTimer() {
    processingDuration.value = 0.0;
    _processingTimer?.cancel();
    _processingTimer = Timer.periodic(const Duration(milliseconds: 100), (timer) {
      processingDuration.value += 0.1;
    });
  }

  void _stopTimer() {
    _processingTimer?.cancel();
    _processingTimer = null;
  }
  
  Future<void> _loadAgentState() async {
    try {
      final response = await _apiService.get(ApiConfig.agentState);
      
      if (response.statusCode == 200) {
        final data = response.data;
        assignedAgents.value = List<String>.from(data['assigned_agents'] ?? []);
        
        allAgents.value = (data['all_agents'] as List?)
            ?.map((json) => DomainAgent.fromJson(json))
            .toList() ?? [];
        
        _logger.info('Agent state loaded: ${assignedAgents.length} agents', source: 'AI');
      }
    } catch (e) {
      _logger.error('Failed to load agent state: $e', source: 'AI');
    }
  }
  
  // ===== SESSION HISTORY MANAGEMENT =====
  
  Future<void> _loadSessionHistory({bool loadMore = false}) async {
    if (loadMore && !hasMoreHistory.value) return;
    if (loadMore && isLoadingHistory.value) return;
    
    isLoadingHistory.value = true;
    
    try {
      if (!loadMore) {
        historyOffset.value = 0;
        hasMoreHistory.value = true;
      }
      
      _logger.info('Loading session history (offset: ${historyOffset.value})', source: 'AI');
      
      final response = await _apiService.get(
        '${ApiConfig.conversations}/sessions',
        queryParameters: {
          'limit': historyLimit.toString(),
          'offset': historyOffset.value.toString(),
        },
      );
      
      if (response.statusCode == 200) {
        final data = response.data;
        final sessions = (data['sessions'] as List?) ?? [];
        
        final validSessions = sessions.where((s) {
          if (s == null) return false;
          final sessionMap = s is Map<String, dynamic> ? s : null;
          return sessionMap != null && sessionMap.containsKey('session_id');
        }).map((s) {
          final map = Map<String, dynamic>.from(s);
          if (map['session_id'] != null) {
            map['session_id'] = map['session_id'].toString();
          }
          return map;
        }).toList();
        
        if (validSessions.length < historyLimit) {
          hasMoreHistory.value = false;
        }
        
        if (loadMore) {
          sessionHistory.addAll(validSessions);
          historyOffset.value += validSessions.length;
        } else {
          sessionHistory.value = validSessions;
          historyOffset.value = validSessions.length;
        }
        
        _logger.info('Loaded ${validSessions.length} sessions. Total: ${sessionHistory.length}', source: 'AI');
        
        // Also update legacy conversationHistory for Memory tab
        conversationHistory.value = sessionHistory;
      }
    } catch (e) {
      _logger.error('Failed to load session history: $e', source: 'AI');
    } finally {
      isLoadingHistory.value = false;
      isLoadingMemory.value = false;
    }
  }
  
  Future<void> loadSessionMessages(String? sessionId) async {
    if (sessionId == null || sessionId.isEmpty) return;
    
    currentSessionId.value = sessionId;
    isProcessing.value = true;
    
    try {
      _logger.info('Loading session messages for: $sessionId', source: 'AI');
      
      final response = await _apiService.get(
        '${ApiConfig.conversations}/sessions/$sessionId/messages',
      );
      
      if (response.statusCode == 200) {
        final data = response.data;
        final messageList = (data['messages'] as List?) ?? [];
        
        messages.value = messageList.where((m) {
          if (m == null) return false;
          final msgMap = m is Map<String, dynamic> ? m : null;
          return msgMap != null && msgMap.containsKey('query');
        }).map((m) => ChatMessage.fromJson(m)).toList();
        
        _logger.info('Loaded ${messages.length} messages for session $sessionId', source: 'AI');
      } else {
        Get.snackbar('Error', 'Failed to load session messages');
      }
    } catch (e) {
      _logger.error('Failed to load session messages: $e', source: 'AI');
      Get.snackbar('Error', 'Could not load chat session');
    } finally {
      isProcessing.value = false;
      _scrollToBottom();
    }
  }
  
  Future<void> startNewChat() async {
    _logger.info('Starting new chat session', source: 'AI');
    
    // Generate new session ID
    final newSessionId = 'session_${DateTime.now().millisecondsSinceEpoch}';
    currentSessionId.value = newSessionId;
    
    // Add to session history immediately
    final newSession = {
      'session_id': newSessionId,
      'title': 'New Chat',
      'message_count': 0,
      'first_message': DateTime.now().toIso8601String(),
    };
    sessionHistory.insert(0, newSession);
    
    // Clear current messages
    messages.clear();
    lastThinkingTrace.value = null;
    
    _logger.info('New session created: $newSessionId', source: 'AI');
  }
  
  Future<void> deleteSession(String? sessionId) async {
    if (sessionId == null || sessionId.isEmpty) return;
    
    try {
      _logger.info('Deleting session: $sessionId', source: 'AI');
      
      // Optimistic update - remove from local list
      sessionHistory.removeWhere((s) => s['session_id'] == sessionId);
      conversationHistory.removeWhere((s) => s['session_id'] == sessionId);
      
      // If deleted current session, start new one
      if (currentSessionId.value == sessionId) {
        await startNewChat();
      }
      
      // Try to delete from backend (if endpoint exists)
      try {
        await _apiService.delete('${ApiConfig.conversations}/sessions/$sessionId');
      } catch (_) {
        // Endpoint might not exist - that's ok
      }
      
    } catch (e) {
      _logger.error('Failed to delete session: $e', source: 'AI');
    }
  }
  
  // ===== LEGACY CONVERSATION HISTORY =====
  
  Future<void> _loadConversationHistory() async {
    isLoadingMemory.value = true;
    
    try {
      final response = await _apiService.get(ApiConfig.conversations);
      
      if (response.statusCode == 200) {
        conversationHistory.value = List<Map<String, dynamic>>.from(response.data);
        _logger.info('Loaded ${conversationHistory.length} conversations', source: 'AI');
      }
    } catch (e) {
      _logger.error('Failed to load conversation history: $e', source: 'AI');
    } finally {
      isLoadingMemory.value = false;
    }
  }
  
  // ===== CHAT FUNCTIONALITY =====
  
  Future<void> sendQuery() async {
    final query = queryController.text.trim();
    if (query.isEmpty) return;
    
    // Add user message
    messages.add(ChatMessage.userMessage(query));
    queryController.clear();
    
    // Scroll to bottom
    _scrollToBottom();
    
    
    isProcessing.value = true;
    _startTimer();
    
    try {
      final response = await _apiService.post(
        ApiConfig.chat,
        data: {
          'query': query,
          'conversation_id': currentSessionId.value.isNotEmpty 
              ? currentSessionId.value 
              : null,
        },
      );
      
      if (response.statusCode == 200) {
        final chatResponse = ChatMessage.fromApiResponse(response.data, query);
        messages.add(chatResponse);
        
        // Update session ID if returned from backend
        final returnedSessionId = response.data['metadata']?['conversation_id'];
        if (returnedSessionId != null && returnedSessionId.toString().isNotEmpty) {
          currentSessionId.value = returnedSessionId.toString();
        }
        
        // Store thinking trace
        if (chatResponse.thinkingTrace != null) {
          lastThinkingTrace.value = chatResponse.thinkingTrace;
        }
        
        // Refresh history to show the new conversation
        _loadSessionHistory();
        
        _logger.info('Query processed: $query', source: 'AI');
      } else {
        _addErrorMessage('Failed to process query. Please try again.');
      }
    } catch (e) {
      _logger.error('Query failed: $e', source: 'AI');
      _addErrorMessage('An error occurred. Please check your connection.');
    } finally {
      isProcessing.value = false;
      _stopTimer();
      _scrollToBottom();
    }
  }
  
  void _addErrorMessage(String error) {
    messages.add(ChatMessage(
      query: '',
      answer: error,
      isUser: false,
      timestamp: DateTime.now(),
      hasError: true,
    ));
  }
  
  void _scrollToBottom() {
    Future.delayed(const Duration(milliseconds: 100), () {
      if (chatScrollController.hasClients) {
        chatScrollController.animateTo(
          chatScrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }
  
  Future<void> clearMemory() async {
    try {
      await _apiService.delete(ApiConfig.clearMemory);
      messages.clear();
      conversationHistory.clear();
      sessionHistory.clear();
      lastThinkingTrace.value = null;
      currentSessionId.value = '';
      
      Get.snackbar(
        'Memory Cleared',
        'All conversation history has been cleared.',
        backgroundColor: Colors.green,
        colorText: Colors.white,
        snackPosition: SnackPosition.TOP,
      );
      
      _logger.info('Memory cleared', source: 'AI');
    } catch (e) {
      _logger.error('Failed to clear memory: $e', source: 'AI');
    }
  }
  
  void toggleThinkingTrace() {
    showThinkingTrace.toggle();
  }
  
  // Quick query suggestions
  List<String> get quickQueries => [
    'Show me top 10 sales',
    'What is current inventory status?',
    'Compare sales by category',
    'Show revenue trends',
  ];
  
  void sendQuickQuery(String query) {
    queryController.text = query;
    sendQuery();
  }
  
  // Check agent access
  bool hasAgentAccess(String agentCode) {
    return assignedAgents.contains(agentCode);
  }
  
  // Refresh data
  Future<void> refresh() async {
    await _loadAgentState();
    await _loadSessionHistory();
  }
  
  Future<void> submitFeedback(String messageId, bool isPositive) async {
    try {
      final rating = isPositive ? 'positive' : 'negative';
      
      // Optimistic UI update could happen here if we tracked feedback state in message list
      // For now we just send the request
      
      await _apiService.post(
        ApiConfig.feedback,
        data: {
          'message_id': messageId,
          'rating': rating,
        },
      );
      
      Get.snackbar(
        'Thank You',
        'Your feedback helps us improve.',
        snackPosition: SnackPosition.BOTTOM,
        backgroundColor: Colors.green,
        colorText: Colors.white,
        duration: const Duration(seconds: 2),
        margin: const EdgeInsets.all(16),
        borderRadius: 12,
      );
      
    } catch (e) {
      _logger.error('Failed to submit feedback: $e', source: 'AI');
    }
  }

  // Load more history (for pagination)
  Future<void> loadMoreHistory() async {
    await _loadSessionHistory(loadMore: true);
  }
}
