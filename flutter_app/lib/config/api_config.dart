/// API Configuration
class ApiConfig {
  // Base URL - Change this for different environments
  static const String baseUrl = 'http://127.0.0.1:8000';
  
  // API Endpoints
  static const String login = '/auth/login';
  static const String register = '/auth/register';
  static const String me = '/auth/me';
  static const String users = '/auth/users';
  static String resetUserPassword(int id) => '/auth/users/$id/reset-password';
  
  static const String chat = '/ai/chat';
  static const String conversations = '/ai/conversations';
  static const String agentState = '/ai/state';
  static const String clearMemory = '/ai/memory';
  static const String schema = '/ai/schema';
  static const String feedback = '/ai/feedback';
  
  static const String dashboard = '/dashboard';
  static const String kpis = '/dashboard/kpis';
  static const String charts = '/dashboard/charts';
  
  static const String settings = '/settings';
  static const String aiConfig = '/settings/ai-config';
  static const String theme = '/settings/theme';
  
  static const String agents = '/ai/agents';
  static const String myAgents = '/ai/agents/my';
  static const String assignAgent = '/ai/agents/assign';
  static const String revokeAgent = '/ai/agents/revoke';
  
  // Timeout settings
  static const Duration connectTimeout = Duration(seconds: 30);
  static const Duration receiveTimeout = Duration(seconds: 60);
  
  // Headers
  static Map<String, String> get defaultHeaders => {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  };
}
