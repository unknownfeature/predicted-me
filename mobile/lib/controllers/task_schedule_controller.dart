import 'package:pm/common/models.dart';
import 'package:pm/controllers/base_controller.dart';
import 'package:pm/services/task_schedule.dart';
import 'package:pm/common/constants.dart';


class TaskScheduleController implements Controller<OccurrenceSchedule> {
  final TaskScheduleService _service = TaskScheduleService();
  final int taskId;

  TaskScheduleController(this.taskId);

  @override
  Future<OccurrenceSchedule> save(OccurrenceSchedule item) async {
    if (item.id == 0) {
      final result = await _service.create(
        taskId,
        item.priority,
        minute: item.minute,
        hour: item.hour,
        dayOfMonth: item.dayOfMonth,
        month: item.month,
        dayOfWeek: item.dayOfWeek,
        periodSeconds: item.periodSeconds,
      );
      return OccurrenceSchedule.fromJson(item.toJson()..[kId] = result[kId]);
    } else {
      await _service.update(
        id: item.id,
        priority: item.priority,
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
  Future<OccurrenceSchedule> get(int id) {
    throw UnimplementedError("Schedule is fetched with its parent (Metric/Task)");
  }

  @override
  Future<List<OccurrenceSchedule>> list(SearchCriteria criteria, int page) {
    throw UnimplementedError("Schedule is fetched with its parent (Metric/Task)");
  }
}
