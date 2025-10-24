import 'package:pm/common/models.dart';
import 'package:pm/controllers/base_controller.dart';

import '../../common/constants.dart';

class MockTaskScheduleController implements Controller<OccurrenceSchedule> {
  final int taskId;
  MockTaskScheduleController(this.taskId);

  static OccurrenceSchedule? mockSchedule;

  @override
  Future<OccurrenceSchedule> save(OccurrenceSchedule item) async {
    print('MOCK: Saving OccurrenceSchedule');
    final newItem = OccurrenceSchedule.fromJson(item.toJson()..[kId] = 1);
    mockSchedule = newItem;
    return newItem;
  }

  @override
  Future delete(int id) async {
    print('MOCK: Deleting OccurrenceSchedule $id');
    mockSchedule = null;
  }

  @override
  Future<OccurrenceSchedule> get(int id) { throw UnimplementedError(); }
  @override
  Future<List<OccurrenceSchedule>> list(SearchCriteria criteria, int page) { throw UnimplementedError(); }
}