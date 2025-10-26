import '../common/constants.dart';
import '../common/models.dart';
import '../services/metric.dart';
import 'base_controller.dart';

class MetricController implements Controller<MetricDetails> {
  final MetricService _service = MetricService();

  @override
  Future<List<MetricDetails>> list(SearchCriteria criteria, [int page = 0, int limit = defaultPageSize]) {
    final queryParams = buildQueryParams(criteria, page, limit);
    return _service.list(queryParams: queryParams);
  }

  @override
  Future<MetricDetails> get(int id) {
    throw UnimplementedError('MetricDetailsService does not support get(id)');
  }

  @override
  Future delete(int id) {
    return _service.delete(id);
  }

  @override
  Future<MetricDetails> save(MetricDetails item) async {
    if (item.id == null) {
      // Create new
      final result = await _service.create(
        item.name,
        item.tags,
      );
      return item.copy(id: result[kId]);
    } else {
      // Update existing
      await _service.update(
        item.id!,
        name: item.name,
        tags: item.tags,
      );
      return item;
    }
  }
}