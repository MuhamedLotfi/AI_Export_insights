import 'package:dio/dio.dart';
import 'package:get/get.dart' hide Response;
import '../../../config/api_config.dart';

import '../../services/auth_service.dart';

import 'log_service.dart';

class ApiService extends GetxService {
  late final Dio _dio;
  final LogService _logger = LogService.instance;
  
  Dio get dio => _dio;
  
  @override
  void onInit() {
    super.onInit();
    _initDio();
  }
  
  void _initDio() {
    _dio = Dio(BaseOptions(
      baseUrl: ApiConfig.baseUrl,
      connectTimeout: ApiConfig.connectTimeout,
      receiveTimeout: ApiConfig.receiveTimeout,
      headers: ApiConfig.defaultHeaders,
    ));
    
    // Add interceptors
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) {
        // Add auth token if available
        try {
          final authService = Get.find<AuthService>();
          final token = authService.token.value;
          if (token.isNotEmpty) {
            options.headers['Authorization'] = 'Bearer $token';
            _logger.info('Auth header set (token: ${token.length} chars)', source: 'API');
          } else {
            _logger.warning('No auth token available for request', source: 'API');
          }
        } catch (e) {
          // AuthService not ready yet
        }
        
        _logger.info('API Request: ${options.method} ${options.path}', source: 'API');
        handler.next(options);
      },
      onResponse: (response, handler) {
        _logger.info('API Response: ${response.statusCode}', source: 'API');
        handler.next(response);
      },
      onError: (error, handler) {
        _logger.error('API Error: ${error.message}', source: 'API');
        
        // Don't auto-logout from the interceptor during init
        // Let the caller (_loadCurrentUser) handle 401 errors properly
        handler.next(error);
      },
    ));
  }
  
  // GET request
  Future<Response<T>> get<T>(
    String path, {
    Map<String, dynamic>? queryParameters,
    Options? options,
  }) async {
    return await _dio.get<T>(
      path,
      queryParameters: queryParameters,
      options: options,
    );
  }
  
  // POST request
  Future<Response<T>> post<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
  }) async {
    return await _dio.post<T>(
      path,
      data: data,
      queryParameters: queryParameters,
      options: options,
    );
  }
  
  // PUT request
  Future<Response<T>> put<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
  }) async {
    return await _dio.put<T>(
      path,
      data: data,
      queryParameters: queryParameters,
      options: options,
    );
  }
  
  // DELETE request
  Future<Response<T>> delete<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
  }) async {
    return await _dio.delete<T>(
      path,
      data: data,
      queryParameters: queryParameters,
      options: options,
    );
  }
}
