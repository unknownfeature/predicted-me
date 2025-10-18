import '../common/constants.dart';
import '../common/models.dart';
import 'api_client.dart';

const String _path = '/metric/schedule';

class MetricScheduleService {
  final ApiClient _apiClient = ApiClient();

  Future<Map<String, dynamic>> create(
    int metricId,
    double value,
    {String? units,
    String? minute,
    String? hour,
    String? dayOfMonth,
    String? month,
    String? dayOfWeek,
    int? periodSeconds,
  }) async {
    return await _apiClient.post(
      '/metric/$metricId/schedule',
      body: {
        kTargetValue: value,
        if (units != null) kUnits: units,
        if (minute != null) kMinute: minute,
        if (hour != null) kHour: hour,
        if (dayOfMonth != null) kDayOfMonth: dayOfMonth,
        if (month != null) kMonth: month,
        if (dayOfWeek != null) kDayOfWeek: dayOfWeek,
        if (periodSeconds != null) kPeriodSeconds: periodSeconds,
      },
    );
  }

  Future<void> update(
    int id, {
    double? value,
    String? units,
    String? minute,
    String? hour,
    String? dayOfMonth,
    String? month,
    String? dayOfWeek,
    int? periodSeconds,
  }) async {
    final body = {
      kTargetValue: value,
      if (units != null) kUnits: units,
      if (minute != null) kMinute: minute,
      if (hour != null) kHour: hour,
      if (dayOfMonth != null) kDayOfMonth: dayOfMonth,
      if (month != null) kMonth: month,
      if (dayOfWeek != null) kDayOfWeek: dayOfWeek,
      if (periodSeconds != null) kPeriodSeconds: periodSeconds,
    };
    await _apiClient.patch('$_path/$id', body: body);
  }

  Future<void> delete(int id) async {
    await _apiClient.delete('$_path/$id');
  }
}
