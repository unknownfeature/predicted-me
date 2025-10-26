import 'dart:math'; // For Random
import 'package:pm/common/models.dart';
import 'package:pm/controllers/base_controller.dart';

import '../../common/constants.dart';

// ... (other mock controllers)

class MockDataController implements Controller<DataPoint> {
  static final MetricDetails _mockMetric = MetricDetails(
    id: 1,
    name: 'Mock Metric',
    tagged: false,
    tags: [],
  );

  static List<DataPoint> mockDataPoints = [
    DataPoint(
      id: 1,
      noteId: 1,
      value: 100.0,
      units: 'kg',
      time: 12345,
      metric: _mockMetric,
    )
  ];

  @override
  Future<List<DataPoint>> list(SearchCriteria criteria, [int page = 0, int limit = defaultPageSize]) {
    print('MOCK: Listing DataPoints (page $page)');
    return Future.value(mockDataPoints);
  }

  @override
  Future<DataPoint> get(int id) {
    print('MOCK: Getting DataPoint $id');
    return Future.value(mockDataPoints.firstWhere((d) => d.id == id));
  }

  @override
  Future delete(int id) {
    print('MOCK: Deleting DataPoint $id');
    mockDataPoints.removeWhere((d) => d.id == id);
    return Future.value();
  }

  @override
  Future<DataPoint> save(DataPoint item) {
    if (item.id == null) {
      print('MOCK: Creating DataPoint');
      final newItem = item.copy(id: Random().nextInt(1000) + 10);
      mockDataPoints.add(newItem);
      return Future.value(newItem);
    } else {
      print('MOCK: Saving DataPoint ${item.id}');
      mockDataPoints.removeWhere((d) => d.id == item.id);
      mockDataPoints.add(item);
      return Future.value(item);
    }
  }
}