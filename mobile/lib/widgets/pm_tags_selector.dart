import 'package:flutter/material.dart';
import 'package:pm/widgets/config/theme.dart';
import 'package:pm/widgets/pm_autocomplete.dart';
import 'base_state.dart';
import 'config/dimensions.dart';

class PredictedMeTagsSelector extends StatefulWidget {
  final Set<String> initialTagNames;
  final Future<Iterable<String>> Function(String) tagsProvider;
  final Function(Set<String>) onChanged;
  final Future Function(String)? onNew;
  final int limit;
  final bool required;

  const PredictedMeTagsSelector({
    Key? key,
    this.initialTagNames = const {},
    required this.tagsProvider,
    required this.onChanged,
    this.onNew,
    this.limit = 10,
    this.required = false,
  }) : super(key: key);

  @override
  State<StatefulWidget> createState() => PredictedMeTagsSelectorState();
}

class PredictedMeTagsSelectorState
    extends PredictedMeBaseState<PredictedMeTagsSelector> {
  late Set<String> _tags;

  final FocusNode _focusNode = FocusNode();

  @override
  void initState() {
    super.initState();
    _tags = Set.from(widget.initialTagNames);
    _focusNode.addListener(redraw);
  }

  @override
  void dispose() {
    _focusNode.removeListener(redraw);
    _focusNode.dispose();
    super.dispose();
  }

  @override
  void didUpdateWidget(covariant PredictedMeTagsSelector oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.initialTagNames != widget.initialTagNames) {
      setState(() {
        _tags = Set.from(widget.initialTagNames);
      });
    }
  }

  void _removeTag(FormFieldState<Set<String>> state, String tagName) {
    redraw(cb: () => _tags.remove(tagName));
    widget.onChanged(_tags);
    state.didChange(_tags);
  }

  Future<void> _addTag(
    FormFieldState<Set<String>> state,
    String tagName,
    bool newTag,
  ) async {
    if (_tags.length < widget.limit) {
      if (_tags.any((tag) => tag.toLowerCase() == tagName.toLowerCase())) {
        return;
      }
      if (newTag) {
        await widget.onNew!(tagName);
      }
      _focusNode.requestFocus();
      redraw(cb: () => _tags.add(tagName));
      widget.onChanged(_tags);
      state.didChange(_tags);
    }
  }

  Widget _buildTagChip(FormFieldState<Set<String>> state, String tagName) {
    return Chip(
      label: Text(tagName, style: lightOnDarkTextStyle),
      side: BorderSide.none,
      backgroundColor: greyPrimary,
      deleteIcon: Icon(Icons.close_outlined, color: background),
      onDeleted: () => _removeTag(state, tagName),
      visualDensity: VisualDensity.compact,
      padding: EdgeInsets.zero,
    );
  }

  @override
  Widget build(BuildContext context) {
    return FormField<Set<String>>(
      initialValue: _tags,

      validator: (Set<String>? value) {
        if (widget.required && value == null || value!.isEmpty) {
          return 'at least one tag is required';
        }
        return null;
      },
      builder: (FormFieldState<Set<String>> state) {
        return Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              padding: const EdgeInsets.symmetric(
                horizontal: Dimensions.paddingSmall,
              ),
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(
                  Dimensions.borderRadiusMedium,
                ),
              ),
              child: GestureDetector(
                onTap: _focusNode.requestFocus,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    PredictedMeAutocomplete(
                      key: widget.key,
                      focusNode: _focusNode,
                      suggestionsProvider: widget.tagsProvider,
                      excludedProvider: () => Set.of(_tags),
                      onSelected: (s) => _addTag(state, s, false),
                      onNew: (s) => _addTag(state, s, true),
                      hintText: 'type to add tags',
                    ),
                    Wrap(
                      spacing: Dimensions.spacingSmall,
                      runSpacing: Dimensions.spacingNone,
                      children: List.of(
                        _tags.map((tagName) => _buildTagChip(state, tagName)),
                      ),
                    ),

                  ],
                ),
              ),
            ),
          ],
        );
      },
    );
  }
}
