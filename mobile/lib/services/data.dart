import '../common/constants.dart';
import '../common/models.dart';
import 'api_client.dart';

const String _path = '/data';

class DataService {
  final ApiClient _apiClient = ApiClient();

  Future<Map<String, dynamic>> create(
    int metricId,
    double value,
    String? units,
    {int? time}
  ) async {
    return await _apiClient.post(
      '/metric/$metricId/data',
      body: {kValue: value, kUnits: units, if (time!= null) kTime: time},
    );
  }

  Future<List<DataPoint>> list({Map<String, String>? queryParams}) async {
    final response = await _apiClient.get(_path, queryParams: queryParams);
    return response.map((data) => DataPoint.fromJson(data)).toList();
  }

  Future<DataPoint> get(int id) async {
    final response = await _apiClient.get('$_path/$id');
    return DataPoint.fromJson(response.first);
  }

  Future<void> update(int id, {double? value, String? units, int? time}) async {
    final body = {
      if (value != null) kValue: value,
      if (units != null) kUnits: units,
      if (time != null) kTime: time,
    };
    await _apiClient.patch('$_path/$id', body: body);
  }


  Future<void> delete(int id) async {
    await _apiClient.delete('$_path/$id');
  }
}
