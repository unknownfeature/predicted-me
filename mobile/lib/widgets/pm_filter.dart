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

class PredictedMeFilter extends StatefulWidget implements PreferredSizeWidget {
  final Function(String?, DateRange, Set<String>?) onCriteriaChanged;
  final Future<Iterable<String>> Function(String) tagsSuggestionsProvider;
  final DateRange initialDateTime;
  final Set<String> initialTags;
  final String? initialText;

  PredictedMeFilter({
    Key? key,
    required this.onCriteriaChanged,
    required this.tagsSuggestionsProvider,
    this.initialDateTime = DateRange.d1,
    this.initialTags = const {},
    this.initialText,
  }) : super(key: key);

  @override
  State<StatefulWidget> createState() => PredictedMeFilterState();

  @override
  Size get preferredSize =>
      const Size.fromHeight(250.0); // Set this to your max expected height
}

class PredictedMeFilterState extends PredictedMeBaseState<PredictedMeFilter> {
  late final TextEditingController _textController;
  late DateRange _currentDateRange;
  late Set<String> _currentTags;
  bool _expanded = false;

  // --- Define the heights for the animation ---
  // This is the height of just the search bar + padding
  final double _collapsedHeight = kToolbarHeight + Dimensions.paddingMedium;
  // This is an estimate of the full height. You can adjust this.
  final double _expandedHeight = 250.0;

  @override
  void initState() {
    super.initState();
    _textController = TextEditingController(text: widget.initialText ?? empty);
    _currentDateRange = widget.initialDateTime;
    _currentTags = widget.initialTags;
    _textController.addListener(_onTextChanged);
  }

  @override
  void dispose() {
    _textController.removeListener(_onTextChanged);
    _textController.dispose();
    super.dispose();
  }

  void _onToggleExpand() {
    setState(() {
      _expanded = !_expanded;
    });
  }

  void _onDateToggled(DateRange range) {
    setState(() {
      _currentDateRange = range;
    });
    widget.onCriteriaChanged(
        _textController.text.trim(), _currentDateRange, _currentTags);
  }

  void _onTextChanged() {
    redraw();
    widget.onCriteriaChanged(
        _textController.text.trim(), _currentDateRange, _currentTags);
  }

  void _onTagsChanged(Set<String> newTags) {
    setState(() {
      _currentTags = newTags;
    });
    widget.onCriteriaChanged(
        _textController.text.trim(), _currentDateRange, _currentTags);
  }

  Widget? _buildSuffixIcon() {
    if (_textController.text.trim().isEmpty) {
      return null;
    }
    return IconButton(
      icon: const Icon(Icons.close_outlined, color: greyPrimary),
      iconSize: Dimensions.iconSizeMedium,
      padding: EdgeInsets.zero,
      onPressed: () {
        _textController.clear();
        _onTextChanged();
      },
    );
  }

  Widget _buildDateToggle(DateRange range) {
    final bool isActive = _currentDateRange == range;
    final Color color = isActive ? greyPrimary : greyShadow;
    final size = Dimensions.iconSizeMedium * 1.2;

    return Material(
      color: Colors.transparent,
      child: InkResponse(
        onTap: () => _onDateToggled(range),
        splashColor: pinkPrimary_50,
        radius: size * 0.8,
        customBorder: CircleBorder(),
        child: Padding(
          padding: const EdgeInsets.all(Dimensions.paddingSmall),
          child: Text(
            range.toDisplayString,
            style: TextStyle(
              color: color,
              fontWeight: isActive ? FontWeight.bold : FontWeight.normal,
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildDateToggles() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
      children:
      DateRange.values.map((range) => _buildDateToggle(range)).toList(),
    );
  }

  Widget _buildSearchBarRow() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Expanded(
          child: TextField(
            controller: _textController,
            decoration: InputDecoration(
              prefixIcon: Icon(Icons.search),
              border: OutlineInputBorder(
                borderRadius:
                BorderRadius.circular(Dimensions.borderRadiusExtraLarge),
                borderSide: BorderSide.none,
              ),
              isDense: true,
              hintText: 'search for ...',
              counterText: empty,
              hintStyle: TextStyle(fontSize: Dimensions.fontSizeSmall),
              filled: true,
              fillColor: greyBackground_50,
              suffixIcon: _buildSuffixIcon(),
              suffixIconConstraints: BoxConstraints(
                maxHeight: Dimensions.fontSizeMedium,
              ),
            ),
          ),
        ),
        IconButton(
          icon: Icon(
            _expanded
                ? Icons.filter_list_off_outlined
                : Icons.filter_list_outlined,
            color: greyPrimary,
          ),
          iconSize: Dimensions.iconSizeMedium,
          padding: EdgeInsets.zero,
          onPressed: _onToggleExpand,
        ),
      ],
    );
  }

  Widget _buildExpandedContent() {
    // This Column contains the filters
    return Column(
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
    );
  }

  @override
  Widget build(BuildContext context) {

    return AnimatedContainer(
      duration: const Duration(milliseconds: 300),
      curve: Curves.easeInOut,
      height: _expanded ? _expandedHeight : _collapsedHeight,
      color: background,
      child: SafeArea(
        bottom: false, // AppBar only needs top safe area
        child: Padding(
          padding: const EdgeInsets.all(Dimensions.paddingMedium),

          child: SingleChildScrollView(
            physics: const NeverScrollableScrollPhysics(),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                _buildSearchBarRow(),

                AnimatedOpacity(
                  duration: const Duration(milliseconds: animationDuration),
                  opacity: _expanded ? 1.0 : 0.0,
                  child: _expanded ? _buildExpandedContent() : null,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}