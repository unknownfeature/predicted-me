import '../../common/constants.dart';
import '../../common/models.dart';
import '../base_controller.dart';

class MockNoteController implements Controller<Note> {
  static List<Note> mockNotes = [
    Note.fromJson({
      'id': 1, 'text': 'This is a mock note', 'time': 12345,
      'imageDescribed': false, 'audioTranscribed': false,
    })
  ];

  @override
  Future<List<Note>> list(SearchCriteria criteria, [int page = 0, int limit = defaultPageSize]) {
    print('MOCK: Listing Notes (page $page)');
    return Future.value(mockNotes);
  }

  @override
  Future<Note> get(int id) {
    print('MOCK: Getting Note $id');
    return Future.value(mockNotes.first);
  }

  // New create method
  Future<Map<String, dynamic>> create({
    String? text,
    String? imageKey,
    String? audioKey,
  }) {
    print('MOCK: Creating new note');
    final newNote = Note.fromJson({
      'id': 99, 'text': text, 'time': 12345,
      'imageKey': imageKey, 'audioKey': audioKey,
      'imageDescribed': false, 'audioTranscribed': false,
    });
    mockNotes.add(newNote);
    return Future.value({'id': 99, 'status': 'success'});
  }

  @override
  Future delete(int id) { throw UnimplementedError(); }
  @override
  Future<Note> save(Note item) { throw UnimplementedError(); }
}