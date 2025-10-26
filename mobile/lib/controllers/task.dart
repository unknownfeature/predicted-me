import 'package:pm/common/constants.dart';

import '../common/models.dart';
import '../services/task.dart';
import 'base_controller.dart';
class TaskController implements Controller<Task> {
  final TaskService _service = TaskService();

  @override
  Future<List<Task>> list(SearchCriteria criteria, [int page = 0, int limit = defaultPageSize]) {
    final queryParams = buildQueryParams(criteria, page, limit);
    return _service.list(queryParams: queryParams);
  }

  @override
  Future<Task> get(int id) {
    return _service.get(id);
  }

  @override
  Future delete(int id) {
    return _service.delete(id);
  }

  @override
  Future<Task> save(Task item) async {
    if (item.id == null) {
      // Create new
      final result = await _service.create(
        item.summary,
        item.description,
        item.tags,
      );
      return item.copy(id: result[kId]);
    } else {
      // Update existing
      await _service.update(
        item.id!,
        summary: item.summary,
        description: item.description,
        tags: item.tags,
      );
      return item;
    }
  }
}