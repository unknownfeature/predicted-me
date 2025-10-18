import '../common/constants.dart';
import '../common/models.dart';
import 'api_client.dart';

const String _path = '/task';

class TaskService {
  final ApiClient _apiClient = ApiClient();

  Future<Map<String, dynamic>> create(
    String summary,
    String description,
    List<String> tags,
  ) async {
    final body = {
      kDescription: description,
      kSummary: summary,
      kTags: tags,
    };
    return await _apiClient.post(_path, body: body);
  }

  Future<List<Task>> list({Map<String, String>? queryParams}) async {
    final response = await _apiClient.get(_path, queryParams: queryParams);
    return response.map((task) => Task.fromJson(task)).toList();
  }

  Future<Task> get(int id) async {
    final response = await _apiClient.get('$_path/$id');
    return Task.fromJson(response.first);
  }

  Future<void> update(
    int id, {
    String? description,
    String? summary,
    List<String>? tags,
  }) async {
    final body = {
      if (description != null) kDescription: description,
      if (summary != null) kSummary: summary,
      if (tags != null && !tags.isEmpty) kTags: tags
    };
    await _apiClient.patch('$_path/$id', body: body);
  }

  Future<void> delete(int id) async {
    await _apiClient.delete('$_path/$id');
  }
}
