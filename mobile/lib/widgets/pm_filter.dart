import 'package:flutter/material.dart';
import 'package:pm/widgets/base_state.dart';
import 'package:pm/widgets/config/constants.dart';
import 'package:pm/widgets/pm_tags_selector.dart';

import 'config/theme.dart';

enum DateRange { d1, w1, m1, m3, m6, y1 }

extension DateRangePresetExtension on DateRange {
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

class PredictedMeFilter extends StatefulWidget {
  final Function(DateRange, Set<String>) onCriteriaChanged;
  final Future<Iterable<String>> Function(String) tagsSuggestionsProvider;
  final DateRange initialDateTime;
  final Set<String> initialTags;

  PredictedMeFilter({
    Key? key,
    required this.onCriteriaChanged,
    required this.tagsSuggestionsProvider,
    this.initialDateTime = DateRange.d1,
    this.initialTags = const {},
  }) : super(key: key);

  @override
  State<StatefulWidget> createState() => PredictedMeFilterState();
}

class PredictedMeFilterState extends PredictedMeBaseState<PredictedMeFilter> {
  late DateRange _currentDateRange;
  late Set<String> _currentTags;

  @override
  void initState() {
    super.initState();
    _currentDateRange = widget.initialDateTime;
    _currentTags = widget.initialTags;
  }

  @override
  void dispose() {
    super.dispose();
  }

  void _onDateToggled(DateRange range) {
    redraw(cb: () => _currentDateRange = range);
    widget.onCriteriaChanged(_currentDateRange, _currentTags);
  }

  void _onTagsChanged(Set<String> newTags) {
    redraw(cb: () => _currentTags = newTags);
    widget.onCriteriaChanged(_currentDateRange, _currentTags);
  }

  Widget _buildDateToggle(DateRange range) {
    final bool active = _currentDateRange == range;
    return Material(
      color: Colors.transparent,
      child: InkResponse(
        onTap: () => _onDateToggled(range),
        splashColor: pinkPrimary_50,
        radius: Dimensions.iconSizeMedium * 1.2,
        customBorder: CircleBorder(),
        child: Padding(
          padding: const EdgeInsets.all(Dimensions.paddingSmall),
          child: Text(
            range.toDisplayString,
            style: TextStyle(
              color: active ? greyPrimary : greyShadow,
              fontWeight: active ? FontWeight.bold : FontWeight.normal,
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildDateToggles() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
      children: DateRange.values
          .map((range) => _buildDateToggle(range))
          .toList(),
    );
  }



  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Column(
        mainAxisSize: MainAxisSize.min, // Takes only the space it needs
        children: [
          const SizedBox(height: Dimensions.sizedBoxExtraLarge),
          _buildDateToggles(),
          const SizedBox(height: Dimensions.sizedBoxExtraLarge),
          PredictedMeTagsSelector(
            initialTagNames: _currentTags,
            tagsProvider: widget.tagsSuggestionsProvider,
            onChanged: _onTagsChanged,
          ),
        ],
      ),
    );
  }
}
