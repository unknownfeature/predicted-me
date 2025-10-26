import 'package:flutter/material.dart';
import 'package:pm/common/constants.dart';
import 'package:pm/widgets/config/theme.dart';
import 'package:pm/widgets/pm_autocomplete.dart';
import '../common/models.dart';
import 'base_state.dart';
import 'config/constants.dart';

class PredictedMeTagsSelector extends StatefulWidget {
  final Set<String> initialTagNames;
  final Future<Iterable<Tag>> Function(String, int) tagsSupplier;
  final Function(Set<String>) onChanged;
  final Future Function(String)? onNew;
  final int maxTags;
  final int limit;
  final bool required;

  const PredictedMeTagsSelector({
    Key? key,
    this.initialTagNames = const {},
    required this.tagsSupplier,
    required this.onChanged,
    this.onNew,
    this.limit = defaultPageSize,
    this.maxTags = 3,
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
    if (_tags.length < widget.maxTags) {
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
      label: Text(tagName, style: lightWithGreyShadows),
      side: BorderSide.none,
      shape: RoundedRectangleBorder(borderRadius: BorderRadiusDirectional.circular(borderRadiusExtraLarge)),
      shadowColor: pinkShadow,
      backgroundColor: greyPrimary_75,
      deleteIcon: Icon(Icons.close_outlined, color: background, shadows: [greyPrimaryShadow],),
      onDeleted: () => _removeTag(state, tagName),
      padding: EdgeInsets.only(left: paddingExtraSmall),
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
                horizontal: paddingSmall,
              ),
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(
                  borderRadiusMedium,
                ),
              ),
              child: GestureDetector(
                onTap: _focusNode.requestFocus,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Wrap(
                      spacing: spacingSmall,
                      runSpacing: spacingNone,
                      children: List.of(
                        _tags.map((tagName) => _buildTagChip(state, tagName)),
                      ),
                    ),
                    SizedBox(height: sizedBoxExtraSmall,),
                    PredictedMeAutocomplete(
                      key: widget.key,
                      focusNode: _focusNode,
                      suggestionsSupplier: widget.tagsSupplier,
                      excludedSupplier: () => Set.of(_tags),
                      onSelected: (s) => _addTag(state, s.name, false),
                      onNew: (s) => _addTag(state, s, true),
                      hintText: 'type to add tags',
                      maxLength: tagFieldLength,
                      limit: widget.limit,
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
