import '../../common/constants.dart';
import '../../common/models.dart';
import '../base_controller.dart';

class MockMetricController implements Controller<MetricDetails> {
  static List<MetricDetails> mockMetrics = [
    MetricDetails.fromJson({'id': 1, 'name': 'Mock Metric', 'tagged': false, 'tags': [], 'schedule': {}})
  ];

  @override
  Future<List<MetricDetails>> list(SearchCriteria criteria, [int page = 0, int limit = defaultPageSize]) {
    print('MOCK: Listing Metrics (page $page)');
    return Future.value(mockMetrics);
  }

  @override
  Future<MetricDetails> get(int id) { throw UnimplementedError(); }

  @override
  Future delete(int id) {
    print('MOCK: Deleting Metric $id');
    mockMetrics.removeWhere((m) => m.id == id);
    return Future.value();
  }

  @override
  Future<MetricDetails> save(MetricDetails item) {
    print('MOCK: Saving Metric ${item.id}');
    mockMetrics.removeWhere((m) => m.id == item.id);
    mockMetrics.add(item);
    return Future.value(item);
  }
}