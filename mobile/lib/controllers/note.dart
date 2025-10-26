import '../common/constants.dart';
import '../common/models.dart';
import '../services/note.dart';
import 'base_controller.dart';
class NoteController implements Controller<Note> {
  final NoteService _service = NoteService();

  @override
  Future<List<Note>> list(SearchCriteria criteria, [int page = 0, int limit = defaultPageSize]) {
    final queryParams = buildQueryParams(criteria, page, limit);
    return _service.list(queryParams);
  }

  @override
  Future<Note> get(int id) {
    return _service.get(id);
  }

  @override
  Future delete(int id) {
    throw UnimplementedError('NoteService does not support delete()');
  }

  @override
  Future<Note> save(Note item) async {
    if (item.id == null) {
      // Create new
      final result = await _service.create(
        text: item.text,
        imageKey: item.imageKey,
        audioKey: item.audioKey,
      );
      return item.copy(id: result[kId]);
    } else {
      // Update existing
      throw UnimplementedError('NoteService does not support update()');
    }
  }
}