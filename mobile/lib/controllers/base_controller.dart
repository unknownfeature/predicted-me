import '../common/constants.dart';
import '../common/models.dart';

class SearchCriteria {
  String? text;
  int tsUtcStart;
  int tsUtcEnd;
  Set<String>? tags;

  SearchCriteria({this.text, required this.tsUtcStart, required this.tsUtcEnd, this.tags});
}

abstract class Controller<T extends Identifiable> {
  Future<List<T>> list(SearchCriteria criteria, int page);

  Future<T> get(int id);

  Future delete(int id);

  Future<T> save(T item);
}