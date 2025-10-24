import 'package:pm/common/models.dart';
import 'package:pm/controllers/base_controller.dart';
import 'package:pm/services/metric_schedule.dart';
import 'package:pm/common/constants.dart';

class MetricScheduleController implements Controller<DataSchedule> {
  final MetricScheduleService _service = MetricScheduleService();
  final int metricId;

  MetricScheduleController(this.metricId);

  @override
  Future<DataSchedule> save(DataSchedule item) async {
    if (item.id == 0) {
      // New schedule, call create
      final result = await _service.create(
        metricId,
        item.targetValue,
        units: item.units,
        minute: item.minute,
        hour: item.hour,
        dayOfMonth: item.dayOfMonth,
        month: item.month,
        dayOfWeek: item.dayOfWeek,
        periodSeconds: item.periodSeconds,
      );
      // We must return a full object, so we create one
      return DataSchedule.fromJson(item.toJson()..[kId] = result[kId]);
    } else {
      // Existing schedule, call update
      await _service.update(
        item.id,
        value: item.targetValue,
        units: item.units,
        minute: item.minute,
        hour: item.hour,
        dayOfMonth: item.dayOfMonth,
        month: item.month,
        dayOfWeek: item.dayOfWeek,
        periodSeconds: item.periodSeconds,
      );
      return item;
    }
  }

  @override
  Future delete(int id) async {
    return await _service.delete(id);
  }

  @override
  Future<DataSchedule> get(int id) {
    throw UnimplementedError("Schedule is fetched with its parent (Metric/Task)");
  }

  @override
  Future<List<DataSchedule>> list(SearchCriteria criteria, int page) {
    throw UnimplementedError("Schedule is fetched with its parent (Metric/Task)");
  }
}
