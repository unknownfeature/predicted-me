import '../../common/constants.dart';
import '../../common/models.dart';
import '../base_controller.dart';

class MockTaskController implements Controller<Task> {
  static List<Task> mockTasks = [
    Task.fromJson({'id': 1, 'summary': 'Mock Task 1', 'description': 'Desc 1', 'tags': ['mock']})
  ];

  @override
  Future<List<Task>> list(SearchCriteria criteria, [int page = 0, int limit = defaultPageSize]) {
    print('MOCK: Listing Tasks (page $page)');
    return Future.value(mockTasks);
  }

  @override
  Future<Task> get(int id) {
    print('MOCK: Getting Task $id');
    return Future.value(mockTasks.first);
  }

  @override
  Future delete(int id) {
    print('MOCK: Deleting Task $id');
    mockTasks.removeWhere((t) => t.id == id);
    return Future.value();
  }

  @override
  Future<Task> save(Task item) {
    print('MOCK: Saving Task ${item.id}');
    mockTasks.removeWhere((t) => t.id == item.id);
    mockTasks.add(item);
    return Future.value(item);
  }
}