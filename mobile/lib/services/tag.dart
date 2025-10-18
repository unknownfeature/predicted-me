import '../common/constants.dart';
import '../common/models.dart';
import 'api_client.dart';

const String _path = '/tag';

class TagService {
  final ApiClient _apiClient = ApiClient();

  Future<Map<String, dynamic>> create(String name,) async {
    final body = {
      kName: name,
    };
    return await _apiClient.post(_path, body: body);
  }

  Future<List<MetricDetails>> list({Map<String, String>? queryParams}) async {
    final response = await _apiClient.get(_path, queryParams: queryParams);
    return response.map((metric) => MetricDetails.fromJson(metric)).toList();
  }

}