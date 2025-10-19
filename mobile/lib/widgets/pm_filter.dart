import 'package:flutter/material.dart';

class FiltrationCriteria {
  int? _id;
  int? _noteId;
  int _startTime;
  int _endTime;
  List<String> _tags;
  int _offset;
  int _limit;

  FiltrationCriteria({
    int? id,
    int? noteId,
    required int startTime,
    required int endTime,
    List<String>? tags,
    int offset = 0,
    int limit = 10,
  }) : _id = id,
       _noteId = noteId,
       _startTime = startTime,
       _endTime = endTime,
       _tags = tags ?? [],
       _offset = offset,
       _limit = limit;

  int? get id => _id;

  int? get noteId => _noteId;

  int get startTime => _startTime;

  int get endTime => _endTime;

  List<String> get tags => List.unmodifiable(_tags);

  int get offset => _offset;

  int get limit => _limit;

  set _setOffset(int value) => _offset = value;

  set _setId(int value) => _id = value;

  set _setNoteId(int value) => _noteId = value;

  set _setStartTime(int value) => _startTime = value;

  set _setEndTime(int value) => _endTime = value;

  set _addTag(String tag) => _tags.add(tag);

  set _removeTag(String tag) => _tags.remove(tag);

  void updateTimeRange(int newStart, int newEnd) {
    _setStartTime = newStart;
    _setEndTime = newEnd;
  }
}

class PredictedMeFilterWidget extends StatefulWidget {
  FiltrationCriteria _criteria;
  Function(FiltrationCriteria) _onCriteriaChanged;

  PredictedMeFilterWidget(this._criteria, this._onCriteriaChanged);

  @override
  State<StatefulWidget> createState() =>
      PredictedMeFilterWidgetState();
}

class PredictedMeFilterWidgetState extends State<PredictedMeFilterWidget>
    with TickerProviderStateMixin {


  PredictedMeFilterWidgetState();

  @override
  Widget build(BuildContext context) {
    throw UnimplementedError();
  }
}
