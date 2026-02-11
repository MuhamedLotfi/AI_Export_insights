import 'package:flutter/material.dart';

class DomainAgent {
  final String code;
  final String name;
  final String description;
  final String icon;
  final List<String> capabilities;
  
  DomainAgent({
    required this.code,
    required this.name,
    required this.description,
    required this.icon,
    this.capabilities = const [],
  });
  
  factory DomainAgent.fromJson(Map<String, dynamic> json) {
    return DomainAgent(
      code: json['code'] ?? '',
      name: json['name'] ?? '',
      description: json['description'] ?? '',
      icon: json['icon'] ?? 'smart_toy',
      capabilities: List<String>.from(json['capabilities'] ?? []),
    );
  }
  
  Map<String, dynamic> toJson() {
    return {
      'code': code,
      'name': name,
      'description': description,
      'icon': icon,
      'capabilities': capabilities,
    };
  }
  
  IconData getIcon() {
    switch (icon) {
      case 'trending_up':
        return Icons.trending_up;
      case 'inventory_2':
        return Icons.inventory_2;
      case 'shopping_cart':
        return Icons.shopping_cart;
      case 'account_balance':
        return Icons.account_balance;
      default:
        return Icons.smart_toy;
    }
  }
  
  Color getColor() {
    switch (code) {
      case 'sales':
        return const Color(0xFF10B981); // Green
      case 'inventory':
        return const Color(0xFFF59E0B); // Amber
      case 'purchasing':
        return const Color(0xFF3B82F6); // Blue
      case 'accounting':
        return const Color(0xFF8B5CF6); // Purple
      default:
        return const Color(0xFF6366F1); // Indigo
    }
  }
}

class UserDomainAgents {
  final int userId;
  final String username;
  final List<String> assignedAgents;
  
  UserDomainAgents({
    required this.userId,
    required this.username,
    required this.assignedAgents,
  });
  
  factory UserDomainAgents.fromJson(Map<String, dynamic> json) {
    return UserDomainAgents(
      userId: json['user_id'] ?? 0,
      username: json['username'] ?? '',
      assignedAgents: List<String>.from(json['assigned_agents'] ?? []),
    );
  }
}

class AgentAccessValidation {
  final List<String> allowedAgents;
  final List<String> blockedAgents;
  final bool hasAccess;
  final bool partialAccess;
  
  AgentAccessValidation({
    required this.allowedAgents,
    required this.blockedAgents,
    required this.hasAccess,
    required this.partialAccess,
  });
  
  factory AgentAccessValidation.fromJson(Map<String, dynamic> json) {
    return AgentAccessValidation(
      allowedAgents: List<String>.from(json['allowed_agents'] ?? []),
      blockedAgents: List<String>.from(json['blocked_agents'] ?? []),
      hasAccess: json['has_access'] ?? false,
      partialAccess: json['partial_access'] ?? false,
    );
  }
}
