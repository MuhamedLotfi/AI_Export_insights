class ChatMessage {
  final String query;
  final String answer;
  final Map<String, dynamic>? thinkingTrace;
  final List<Map<String, dynamic>> data;
  final Map<String, dynamic>? chartData;
  final List<Map<String, dynamic>> insights;
  final List<Map<String, dynamic>> recommendations;
  final List<String> agentsUsed;
  final List<String> agentsBlocked;
  final bool isUser;
  final DateTime timestamp;
  final bool hasError;
  final Map<String, dynamic>? metadata;
  final String? messageId;
  final String? feedback; // 'positive' or 'negative'
  
  ChatMessage({
    required this.query,
    required this.answer,
    this.thinkingTrace,
    this.data = const [],
    this.chartData,
    this.insights = const [],
    this.recommendations = const [],
    this.agentsUsed = const [],
    this.agentsBlocked = const [],
    required this.isUser,
    required this.timestamp,
    this.hasError = false,
    this.metadata,
    this.messageId,
    this.feedback,
  });
  
  factory ChatMessage.fromApiResponse(Map<String, dynamic> json, String query) {
    return ChatMessage(
      query: query,
      answer: json['answer'] ?? '',
      thinkingTrace: json['thinking_trace'],
      data: List<Map<String, dynamic>>.from(json['data'] ?? []),
      chartData: json['chart_data'],
      insights: List<Map<String, dynamic>>.from(json['insights'] ?? []),
      recommendations: List<Map<String, dynamic>>.from(json['recommendations'] ?? []),
      agentsUsed: List<String>.from(json['agents_used'] ?? []),
      agentsBlocked: List<String>.from(json['agents_blocked'] ?? []),
      isUser: false,
      timestamp: DateTime.now(),
      hasError: json['error'] ?? false,
      metadata: json['metadata'],
      messageId: json['metadata']?['message_id'],
    );
  }
  
  factory ChatMessage.userMessage(String message) {
    return ChatMessage(
      query: message,
      answer: '',
      isUser: true,
      timestamp: DateTime.now(),
    );
  }
  
  factory ChatMessage.fromJson(Map<String, dynamic> json) {
    final role = json['role'] ?? 'assistant';
    final isUser = role == 'user';
    
    return ChatMessage(
      query: isUser ? (json['content'] ?? json['query'] ?? '') : (json['query'] ?? ''),
      answer: isUser ? '' : (json['content'] ?? json['response'] ?? json['answer'] ?? ''),
      thinkingTrace: json['thinking_trace'],
      data: List<Map<String, dynamic>>.from(json['data'] ?? []),
      chartData: json['chart_data'] ?? json['chart'],
      insights: List<Map<String, dynamic>>.from(json['insights'] ?? json['key_findings'] ?? []),
      recommendations: List<Map<String, dynamic>>.from(json['recommendations'] ?? []),
      agentsUsed: List<String>.from(json['agents_used'] ?? []),
      agentsBlocked: List<String>.from(json['agents_blocked'] ?? []),
      isUser: isUser,
      timestamp: json['timestamp'] != null 
          ? DateTime.tryParse(json['timestamp'].toString()) ?? DateTime.now()
          : DateTime.now(),
      hasError: json['error'] ?? json['has_error'] ?? false,
      metadata: json['metadata'],
      messageId: json['message_id'] ?? json['metadata']?['message_id'],
      feedback: json['feedback'],
    );
  }
}

class Conversation {
  final String? id;
  final String query;
  final String response;
  final String timestamp;
  final List<String> agentsUsed;
  
  Conversation({
    this.id,
    required this.query,
    required this.response,
    required this.timestamp,
    this.agentsUsed = const [],
  });
  
  factory Conversation.fromJson(Map<String, dynamic> json) {
    return Conversation(
      id: json['id']?.toString(),
      query: json['query'] ?? '',
      response: json['response'] ?? '',
      timestamp: json['timestamp'] ?? '',
      agentsUsed: List<String>.from(json['agents_used'] ?? []),
    );
  }
}
