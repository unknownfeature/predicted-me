import '../../common/constants.dart';
import '../../common/models.dart';

enum DateRange { d1, w1, m1, m3, m6, y1 }

extension DateRangePresetExtension on DateRange {

  (int?, int?) get toUtcTimestamps {
    final now = DateTime.now().toUtc();
    final endTime = DateTime.utc(now.year, now.month, now.day, 23, 59, 59);
    DateTime? startTime;
    switch (this) {
      case DateRange.d1:
        startTime = now.subtract(const Duration(days: 1));
        break;
      case DateRange.w1:
        startTime = now.subtract(const Duration(days: 7));
        break;
      case DateRange.m1:
        startTime = now.subtract(const Duration(days: 30));
        break;
      case DateRange.m3:
        startTime = now.subtract(const Duration(days: 90));
        break;
      case DateRange.m6:
        startTime = now.subtract(const Duration(days: 182));
        break;
      case DateRange.y1:
        startTime = now.subtract(const Duration(days: 365));
        break;
    }
    return (
    startTime.millisecondsSinceEpoch ~/ msInSec,
    endTime.millisecondsSinceEpoch ~/ msInSec,
    );
  }
}

class SearchCriteria {
  String? text;
  DateRange dateRange;
  Set<String> tags;

  SearchCriteria({this.text, required this.dateRange, required this.tags})
}

abstract class Controller<T extends Identifiable> {
  Future<List<T>> list(SearchCriteria criteria, int page);

  Future<T> get(int id);

  Future delete(int id);

  Future<T> save(T);
}