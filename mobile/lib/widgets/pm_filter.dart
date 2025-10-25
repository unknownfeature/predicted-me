import 'package:flutter/material.dart';
import 'package:pm/widgets/base_state.dart';
import 'package:pm/widgets/config/constants.dart';
import 'package:pm/widgets/pm_tags_selector.dart';

import '../common/constants.dart';
import 'config/theme.dart';

DateTime getUtcDateTimeEndForToday() {
  final now = DateTime.now().toUtc();
  return DateTime.utc(now.year, now.month, now.day, 23, 59, 59);
}

DateTimeRange<DateTime> toUtcDateTimeRange(int tsUtcStart, int tsUtcEnd) {
  final rangeInUtc = DateTimeRange(
    start: toUtcDateTime(tsUtcStart),
    end: DateTime.fromMillisecondsSinceEpoch(tsUtcEnd * msInSec, isUtc: true),
  );
  return rangeInUtc;
}

DateTimeRange<DateTime> toLocalDateTimeRange(int tsUtcStart, int tsUtcEnd) {
  final rangeInUtc = DateTimeRange(
    start: toUtcDateTime(tsUtcStart).toLocal(),
    end: toUtcDateTime(tsUtcEnd * msInSec).toLocal(),
  );
  return rangeInUtc;
}

DateTime toUtcDateTime(int tsUtcStart) {
  return DateTime.fromMillisecondsSinceEpoch(tsUtcStart * msInSec, isUtc: true);
}

final startYear = DateTime(2000);
final endYear = DateTime(2030);

Duration day = const Duration(days: 1);
Duration week = const Duration(days: 7);
Duration month = const Duration(days: 31);
Duration threeMonths = const Duration(days: 92);
Duration sixMonths = const Duration(days: 183);
Duration year = const Duration(days: 366);

enum DateRange { d1, w1, m1, m3, m6, y1 }

extension DateRangeExtension on DateRange {
  Duration get duration {
    switch (this) {
      case DateRange.d1:
        return day;
      case DateRange.w1:
        return week;
      case DateRange.m1:
        return month;
      case DateRange.m3:
        return threeMonths;
      case DateRange.m6:
        return sixMonths;
      case DateRange.y1:
        return year;
    }
  }

  (int, int) get toUtcTimestamps {
    DateTime now = getUtcDateTimeEndForToday();
    return (
      now.millisecondsSinceEpoch ~/ msInSec,
      now.subtract(this.duration).millisecondsSinceEpoch ~/ msInSec,
    );
  }

  String get toDisplayString {
    return switch (this) {
      DateRange.d1 => '1D',
      DateRange.w1 => '1W',
      DateRange.m1 => '1M',
      DateRange.m3 => '3M',
      DateRange.m6 => '6M',
      DateRange.y1 => '1Y',
    };
  }

  static DateRange? fromRange(int tsUtcStart, int tsUtcEnd) {
    DateTimeRange<DateTime> rangeInUtc = toUtcDateTimeRange(tsUtcStart, tsUtcEnd);
    final end = rangeInUtc.end;

    if (end.millisecondsSinceEpoch ~/ msInSec != getUtcDateTimeEndForToday()) {
      return null;
    }
    var difference = end.difference(rangeInUtc.start);

    if (difference.compareTo(year) == 0) {
      return DateRange.y1;
    }

    if (difference.compareTo(sixMonths) == 0) {
      return DateRange.m6;
    }

    if (difference.compareTo(threeMonths) == 0) {
      return DateRange.m3;
    }

    if (difference.compareTo(month) == 0) {
      return DateRange.m1;
    }

    if (difference.compareTo(week) == 0) {
      return DateRange.w1;
    }
    if (difference.compareTo(day) == 0) {
      return DateRange.d1;
    }

    return null;
  }
}

class PredictedMeFilter extends StatefulWidget {
  final Function(int, int, Set<String>) onCriteriaChanged;
  final Future<Iterable<String>> Function(String) tagsSuggestionsSupplier;
  final int? initialTsUtcStart;
  final int? initialTsUtcEnd;
  final Set<String> initialTags;

  PredictedMeFilter({
    Key? key,
    required this.onCriteriaChanged,
    required this.tagsSuggestionsSupplier,
    this.initialTsUtcStart,
    this.initialTsUtcEnd,
    this.initialTags = const {},
  }) : super(key: key);

  @override
  State<StatefulWidget> createState() => PredictedMeFilterState();
}

class PredictedMeFilterState extends PredictedMeBaseState<PredictedMeFilter> {
  late int _tsUtcStart;
  late int _tsUtcEnd;
  late Set<String> _currentTags;

  @override
  void initState() {
    super.initState();
    _tsUtcEnd =
        widget.initialTsUtcEnd ??
        getUtcDateTimeEndForToday().millisecondsSinceEpoch / ~msInSec as int;
    _tsUtcStart = widget.initialTsUtcStart ?? _tsUtcEnd - day.inSeconds;
    _currentTags = widget.initialTags;
  }

  @override
  void dispose() {
    super.dispose();
  }

  void _onDateToggled(DateRange range) {
    redraw(
      cb: () {
        final (start, end) = range.toUtcTimestamps;
        _tsUtcStart = start;
        _tsUtcEnd = end;
      },
    );
    widget.onCriteriaChanged(_tsUtcStart, _tsUtcEnd, _currentTags);
  }

  void _onCustomRange() async {
    DateTimeRange? range = await showDateRangePicker(
      context: context,
      firstDate: startYear,
      lastDate: endYear,
      initialDateRange: toLocalDateTimeRange(_tsUtcStart, _tsUtcEnd),
    );

    if (range == null) {
      return;
    }

    redraw(
      cb: () {
        _tsUtcStart =
            range.start.toUtc().millisecondsSinceEpoch / ~msInSec as int;
        _tsUtcEnd = range.end.toUtc().millisecondsSinceEpoch / ~msInSec as int;
      },
    );
    widget.onCriteriaChanged(_tsUtcStart, _tsUtcEnd, _currentTags);
  }

  void _onTagsChanged(Set<String> newTags) {
    redraw(cb: () => _currentTags = newTags);
    widget.onCriteriaChanged(_tsUtcStart, _tsUtcEnd, _currentTags);
  }

  Widget _buildDateToggleItem(Function() onTap, Widget child) {
    return Material(
      color: Colors.transparent,
      child: InkResponse(
        onTap: () => onTap,
        splashColor: pinkPrimary_50,
        radius: iconSizeMedium * 1.2,
        customBorder: CircleBorder(),
        child: Padding(
          padding: const EdgeInsets.all(paddingSmall),
          child: child,
        ),
      ),
    );
  }

  Widget _buildDateToggle(DateRange range, bool active) {
    return _buildDateToggleItem(
      () => _onDateToggled(range),
      Text(
        range.toDisplayString,
        style: TextStyle(
          color: active ? greyPrimary : greyShadow,
          fontWeight: active ? FontWeight.bold : FontWeight.normal,
        ),
      ),
    );
  }

  Widget _buildDateToggles() {
    DateRange? fromStartAndEnd = DateRangeExtension.fromRange(
      _tsUtcStart,
      _tsUtcEnd,
    );
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
      children:
          DateRange.values
              .map((range) => _buildDateToggle(range, range == fromStartAndEnd))
              .toList()
            ..add(
              _buildDateToggleItem(
                _onCustomRange,
                IconButton(
                  onPressed: () {},
                  icon: Icon(
                    Icons.calendar_today_outlined,
                    color: fromStartAndEnd == null ? greyPrimary : greyShadow,
                    size: iconSizeLarge,
                  ),
                ),
              ),
            ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min, // Takes only the space it needs
      children: [
        const SizedBox(height: sizedBoxExtraLarge),
        _buildDateToggles(),
        const SizedBox(height: sizedBoxExtraLarge),
        PredictedMeTagsSelector(
          initialTagNames: _currentTags,
          tagsSupplier: widget.tagsSuggestionsSupplier,
          onChanged: _onTagsChanged,
        ),
      ],
    );
  }
}
