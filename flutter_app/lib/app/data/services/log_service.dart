import 'package:flutter/foundation.dart';
import 'package:get/get.dart';

enum LogLevel { debug, info, warning, error }

class LogService extends GetxService {
  static LogService get instance => Get.find<LogService>();
  
  final RxList<LogEntry> logs = <LogEntry>[].obs;
  final int maxLogs = 1000;
  
  void log(String message, {LogLevel level = LogLevel.info, String? source}) {
    final entry = LogEntry(
      message: message,
      level: level,
      source: source,
      timestamp: DateTime.now(),
    );
    
    logs.add(entry);
    
    // Limit logs
    if (logs.length > maxLogs) {
      logs.removeAt(0);
    }
    
    // Print to console in debug mode
    if (kDebugMode) {
      final prefix = source != null ? '[$source]' : '';
      print('${level.name.toUpperCase()} $prefix $message');
    }
  }
  
  void debug(String message, {String? source}) {
    log(message, level: LogLevel.debug, source: source);
  }
  
  void info(String message, {String? source}) {
    log(message, level: LogLevel.info, source: source);
  }
  
  void warning(String message, {String? source}) {
    log(message, level: LogLevel.warning, source: source);
  }
  
  void error(String message, {String? source}) {
    log(message, level: LogLevel.error, source: source);
  }
  
  List<LogEntry> getLogsByLevel(LogLevel level) {
    return logs.where((log) => log.level == level).toList();
  }
  
  void clear() {
    logs.clear();
  }
}

class LogEntry {
  final String message;
  final LogLevel level;
  final String? source;
  final DateTime timestamp;
  
  LogEntry({
    required this.message,
    required this.level,
    this.source,
    required this.timestamp,
  });
}
