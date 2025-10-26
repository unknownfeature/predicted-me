import '../../common/constants.dart';
import '../../common/models.dart';
import '../base_controller.dart';


class MockTagController implements Controller<Tag> {
  static List<Tag> mockTags = [
    Tag(id: 1, name: 'Health'),
    Tag(id: 2, name: 'Fitness'),
    Tag(id: 3, name: 'Work'),
    Tag(id: 4, name: 'Personal'),
  ];

  @override
  Future<List<Tag>> list(SearchCriteria criteria, [int page = 0, int limit = defaultPageSize]) {
    print('MOCK: Listing Tags (page $page, criteria: ${criteria.text})');

    List<Tag> filteredTags = mockTags;

    if (criteria.text != null && criteria.text!.isNotEmpty) {
      filteredTags = mockTags
          .where((tag) =>
          tag.name.toLowerCase().contains(criteria.text!.toLowerCase()))
          .toList();
    }

    return Future.value(filteredTags);
  }

  @override
  Future<Tag> save(Tag item) async {
    print('MOCK: Saving Tag ${item.name}');
    if (item.id == null) {
      // Create new
      final newTag = Tag(id: mockTags.length + 1, name: item.name);
      mockTags.add(newTag);
      return Future.value(newTag);
    } else {
      throw UnimplementedError('TagService does not support update()');
    }
  }

  @override
  Future<Tag> get(int id) {
    throw UnimplementedError('TagService does not support get(id)');
  }

  @override
  Future delete(int id) {
    throw UnimplementedError('TagService does not support delete()');
  }
}