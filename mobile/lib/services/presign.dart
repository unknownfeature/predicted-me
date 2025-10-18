import '../common/constants.dart';
import '../common/models.dart';
import 'api_client.dart';

class PresignService {
  final ApiClient _apiClient = ApiClient();

  Future<PresignedUrlResponse> get(String? extension, String? key) async {

    const Map<String, String> queryParams = {};

    if (extension != null){
      queryParams[pExtension] = extension;
      queryParams[pMethod] = vPut;
    } else if (key != null){
      queryParams[pKey] = key;
      queryParams[pMethod] = vGet;
    }else{
      throw Exception('key or extension should be provided');
    }

    final response = await _apiClient.get('/presign', queryParams: queryParams);
    return PresignedUrlResponse.fromJson(response);
  }
}