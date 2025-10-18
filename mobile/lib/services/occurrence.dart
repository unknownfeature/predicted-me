import '../common/constants.dart';
import '../common/models.dart';
import 'api_client.dart';

const String _path = '/occurrence';

class OccurrenceService {
  final ApiClient _apiClient = ApiClient();

  Future<Map<String, dynamic>> create(
    int taskId,
    int priority, {
    int? time,
    bool? completed,
  }) async {
    return await _apiClient.post(
      '/task/$taskId/occurrence',
      body: {
        kPriority: priority,
        if (time != null) kTime: time,
        if (completed != null) kCompleted: completed,
      },
    );
  }

  Future<List<Occurrence>> list({Map<String, String>? queryParams}) async {
    final response = await _apiClient.get(_path, queryParams: queryParams);
    return response
        .map((occurrence) => Occurrence.fromJson(occurrence))
        .toList();
  }

  Future<Occurrence> get(int id) async {
    final response = await _apiClient.get('$_path/$id');
    return Occurrence.fromJson(response.first);
  }

  Future<void> update(
    int id, {
    int? priority,
    int? time,
    bool? completed,
  }) async {
    final body = {
      if (priority != null) kPriority: priority,
      if (completed != null) kCompleted: completed,
      if (time != null) kTime: time,
    };
    await _apiClient.patch('$_path/$id', body: body);
  }

  Future<void> delete(int id) async {
    await _apiClient.delete('$_path/$id');
  }
}
