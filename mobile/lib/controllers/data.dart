import '../common/constants.dart';
import '../common/models.dart';
import '../services/data.dart';
import 'base_controller.dart';

class DataController implements Controller<DataPoint> {
  final DataService _service = DataService();

  @override
  Future<List<DataPoint>> list(SearchCriteria criteria, [int page = 0, int limit = defaultPageSize]) {
    final queryParams = buildQueryParams(criteria, page, limit);
    return _service.list(queryParams: queryParams);
  }

  @override
  Future<DataPoint> get(int id) {
    return _service.get(id);
  }

  @override
  Future delete(int id) {
    return _service.delete(id);
  }

  @override
  Future<DataPoint> save(DataPoint item) async {
    if (item.id == null) {
      // Create new
      if (item.metric.id == null) {
        throw Exception("Cannot create a DataPoint without a Metric ID.");
      }
      final result = await _service.create(
        item.metric.id!,
        item.value,
        item.units,
        time: item.time,
      );
      return item.copy(id: result[kId]);
    } else {
      // Update existing
      await _service.update(
        item.id!,
        value: item.value,
        units: item.units,
        time: item.time,
      );
      return item;
    }
  }
}