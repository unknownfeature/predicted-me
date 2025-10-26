import '../../common/constants.dart';
import '../../common/models.dart';
import '../base_controller.dart';

class MockLinkController implements Controller<Link> {
  static List<Link> mockLinks = [
    Link.fromJson({
      'id': 1, 'url': 'https://mock.com', 'summary': 'Mock Link',
      'description': 'Desc 1', 'tagged': false, 'time': 12345, 'tags': []
    })
  ];

  @override
  Future<List<Link>> list(SearchCriteria criteria, [int page = 0, int limit = defaultPageSize]) {
    print('MOCK: Listing Links (page $page)');
    return Future.value(mockLinks);
  }

  @override
  Future<Link> get(int id) {
    print('MOCK: Getting Link $id');
    return Future.value(mockLinks.first);
  }

  @override
  Future delete(int id) {
    print('MOCK: Deleting Link $id');
    mockLinks.removeWhere((l) => l.id == id);
    return Future.value();
  }

  @override
  Future<Link> save(Link item) {
    print('MOCK: Saving Link ${item.id}');
    mockLinks.removeWhere((l) => l.id == item.id);
    mockLinks.add(item);
    return Future.value(item);
  }
}