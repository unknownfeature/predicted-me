import 'package:pm/common/models.dart';
import 'package:pm/controllers/base_controller.dart';

import '../../common/constants.dart';

class MockMetricScheduleController implements Controller<DataSchedule> {
  final int metricId;
  MockMetricScheduleController(this.metricId);

  static DataSchedule? mockSchedule;

  @override
  Future<DataSchedule> save(DataSchedule item) async {
    print('MOCK: Saving DataSchedule');
    final newItem = DataSchedule.fromJson(item.toJson()..[kId] = 1);
    mockSchedule = newItem;
    return newItem;
  }

  @override
  Future delete(int id) async {
    print('MOCK: Deleting DataSchedule $id');
    mockSchedule = null;
  }

  @override
  Future<DataSchedule> get(int id) { throw UnimplementedError(); }
  @override
  Future<List<DataSchedule>> list(SearchCriteria criteria, [int page = 0, int limit = defaultPageSize]) { throw UnimplementedError(); }
}

