import '../common/models.dart';
import '../common/constants.dart';

class SearchCriteria {
  String? text;
  int? tsUtcStart;
  int? tsUtcEnd;
  Set<String>? tags;

  SearchCriteria({this.text, this.tsUtcStart, this.tsUtcEnd, this.tags});
}

abstract class Controller<T extends Identifiable> {
  Future<List<T>> list(SearchCriteria criteria, [int page = 0, int limit = 10]);

  Future<T> get(int id);

  Future delete(int id);

  Future<T> save(T item);
}

const String _kParamsDelim = '|';

/// Converts SearchCriteria and page into a Map for the API client.
Map<String, String> buildQueryParams(SearchCriteria criteria, [int page = 0, int limit = defaultPageSize]) {
  final params = <String, String>{};

  // Pagination
  params[pOffset] = (page * limit).toString();
  params[pLimit] = limit.toString();

  // Time
  if (criteria.tsUtcStart != null){
    params[pStart] = criteria.tsUtcStart.toString();
  }
  if (criteria.tsUtcEnd != null){
    params[pEnd] = criteria.tsUtcEnd.toString();
  }


  // Filters
  if (criteria.text != null && criteria.text!.isNotEmpty) {
    params[kText] = criteria.text!;
  }
  if (criteria.tags != null && criteria.tags!.isNotEmpty) {
    params[kTags] = criteria.tags!.join(_kParamsDelim);
  }

  return params;
}