import 'package:pm/services/tag.dart';

import '../common/constants.dart';
import '../common/models.dart';
import 'base_controller.dart';

class TagController implements Controller<Tag> {
  final TagService _service = TagService();

  @override
  Future<List<Tag>> list(SearchCriteria criteria, [int page = 0, int limit = defaultPageSize]) {
    final queryParams = buildQueryParams(criteria, page, limit);
    return _service.list(queryParams: queryParams);
  }

  @override
  Future<Tag> get(int id) {
    throw UnimplementedError('TagService does not support get(id)');
  }

  @override
  Future delete(int id) {
    throw UnimplementedError('TagService does not support delete()');
  }

  @override
  Future<Tag> save(Tag item) async {
    if (item.id == null) {
      // Create new
      final result = await _service.create(
        item.name,
      );
      return Tag(id: result[kId], name: item.name);
    } else {
      throw UnimplementedError('TagService does not support update()');
    }
  }
}