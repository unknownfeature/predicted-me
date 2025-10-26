import '../common/constants.dart';
import '../common/models.dart';
import '../services/link.dart';
import 'base_controller.dart';

class LinkController implements Controller<Link> {
  final LinkService _service = LinkService();

  @override
  Future<List<Link>> list(SearchCriteria criteria, [int page = 0, int limit = defaultPageSize]) {
    final queryParams = buildQueryParams(criteria, page, limit);
    return _service.list(queryParams: queryParams);
  }

  @override
  Future<Link> get(int id) {
    return _service.get(id);
  }

  @override
  Future delete(int id) {
    return _service.delete(id);
  }

  @override
  Future<Link> save(Link item) async {
    if (item.id == null) {
      // Create new
      final result = await _service.create(
        item.summary,
        item.description ?? '',
        item.url,
        item.tags,
      );
      return item.copy(id: result[kId]);
    } else {
      // Update existing
      await _service.update(
        item.id!,
        summary: item.summary,
        description: item.description,
        url: item.url,
        tags: item.tags,
      );
      return item;
    }
  }
}