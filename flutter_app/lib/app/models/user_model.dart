class User {
  final int id;
  final String username;
  final String email;
  final String role;
  final List<String> domainAgents;
  
  User({
    required this.id,
    required this.username,
    required this.email,
    required this.role,
    this.domainAgents = const [],
  });
  
  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'] ?? 0,
      username: json['username'] ?? '',
      email: json['email'] ?? '',
      role: json['role'] ?? 'user',
      domainAgents: List<String>.from(json['domain_agents'] ?? []),
    );
  }
  
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'username': username,
      'email': email,
      'role': role,
      'domain_agents': domainAgents,
    };
  }
  
  bool get isAdmin => role == 'admin';
  bool get isManager => role == 'manager' || isAdmin;
}
