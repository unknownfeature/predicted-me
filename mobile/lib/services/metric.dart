import '../common/constants.dart';
import '../common/models.dart';
import 'api_client.dart';

const String _path = '/metric';

class MetricService {
  final ApiClient _apiClient = ApiClient();

  Future<Map<String, dynamic>> create(
    String name,

    List<String> tags,
  ) async {
    final body = {
      kName: name,

      kTags: tags,
    };
    return await _apiClient.post(_path, body: body);
  }

  Future<List<MetricDetails>> list({Map<String, String>? queryParams}) async {
    final response = await _apiClient.get(_path, queryParams: queryParams);
    return response.map((metric) => MetricDetails.fromJson(metric)).toList();
  }


  Future<void> update(
    int id, {
    String? name,
    List<String>? tags,
  }) async {
    final body = {
      if (name != null) kName: name,
      if (tags != null && !tags.isEmpty) kTags: tags
    };
    await _apiClient.patch('$_path/$id', body: body);
  }

  Future<void> delete(int id) async {
    await _apiClient.delete('$_path/$id');
  }
}
