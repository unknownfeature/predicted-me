import '../common/constants.dart';
import '../common/models.dart';
import 'api_client.dart';

const String _path = '/note';

class NoteService {
  final ApiClient _apiClient = ApiClient();

  Future<Note> get(int id) async {
    final response = await _apiClient.get('$_path/$id');
    return Note.fromJson(response.first);
  }

  Future<List<Note>> list(Map<String, String> queryParams) async {
    final response = await _apiClient.get(_path, queryParams: queryParams);
    return (response as List).map((data) => Note.fromJson(data)).toList();
  }

  Future<Map<String, dynamic>> create({
    String? text,
    String? imageKey,
    String? audioKey,
  }) async {
    final body = {
      if (text != null) kText: text,
      if (imageKey != null) kImageKey: imageKey,
      if (audioKey != null) kAudioKey: audioKey,
    };
    return await _apiClient.post(_path, body: body);
  }
}
