import 'package:flutter/material.dart';
import 'base_state.dart';
import 'config/dimensions.dart';

class PredictedMeTagsSelectorWidget extends StatefulWidget {
  final Set<String> initialTagNames;
  final Iterable<String> Function(String) tagsProvider;
  final Function(Set<String>) onChanged;
  final Function(String)? onNew;
  final int limit;

  const PredictedMeTagsSelectorWidget({
    Key? key,
    this.initialTagNames = const {},
    required this.tagsProvider,
    required this.onChanged,
    this.onNew,
    this.limit = 10,
  }) : super(key: key);

  @override
  State<StatefulWidget> createState() => PredictedMeTagsSelectorState();
}

class PredictedMeTagsSelectorState
    extends PredictedMeBaseState<PredictedMeTagsSelectorWidget> {
  late Set<String> _tags;

  final TextEditingController _textController = TextEditingController();
  final FocusNode _focusNode = FocusNode();

  bool _showAddIcon() {
    return _textController.text.length >= 3 && widget.onNew != null;
  }

  bool _showEdit() {
    return _focusNode.hasFocus && _textController.text.isNotEmpty;
  }
  @override
  void initState() {
    super.initState();
    _tags = Set.from(widget.initialTagNames);
    _textController.addListener(_onTextChanged);
    _focusNode.addListener(redraw);
  }

  @override
  void dispose() {
    _textController.removeListener(_onTextChanged);
    _focusNode.removeListener(redraw);
    _textController.dispose();
    _focusNode.dispose();
    super.dispose();
  }

  @override
  void didUpdateWidget(covariant PredictedMeTagsSelectorWidget oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.initialTagNames != widget.initialTagNames) {
      setState(() {
        _tags = Set.from(widget.initialTagNames);
      });
    }
  }


  void _onTextChanged() {
    final text = _textController.text.trim();
    if (text.isEmpty) {
      redraw();
      return;
    }

    if (_focusNode.hasFocus) {
      final results = widget.tagsProvider(text).toList();
      setState(() {
        _suggestions = Set.from(results);
      });
    }
  }

  void _removeTag(FormFieldState<Set<String>> state, String tagName) {
    setState(() {
      _tags.remove(tagName);
    });
    widget.onChanged(_tags);
    state.didChange(_tags);
  }

  void _addTag(FormFieldState<Set<String>> state, String tagName) {
    if (_tags.length < widget.limit) {
      setState(() {
        _tags.add(tagName);
        _textController.clear();
        _suggestions = {};
      });
      widget.onChanged(_tags);
      state.didChange(_tags);
      _focusNode.requestFocus();
    }
  }

  void _addNewTagFromTextField(FormFieldState<Set<String>> state) {
    final newTag = _textController.text.trim();
    if (newTag.isEmpty || _tags.length >= widget.limit) {
      return;
    }

    final tagExists = _tags.any(
      (tag) => tag.toLowerCase() == newTag.toLowerCase(),
    );

    if (tagExists) {
      setState(() {
        _textController.clear();
        _suggestions = {};
      });
      _focusNode.requestFocus();
      return;
    }

    setState(() {
      _tags.add(newTag);
      _textController.clear();
      _suggestions = {};
    });

    widget.onChanged(_tags);
    widget.onNew?.call(newTag);
    state.didChange(_tags);
    _focusNode.requestFocus();
  }

  Widget _buildTagChip(String tagName, Function(String) onDeleted) {
    return Chip(
      label: Text(tagName),
      deleteIcon: Icon(Icons.cancel_outlined),
      onDeleted: () => onDeleted(tagName),
      visualDensity: VisualDensity.compact,
      padding: EdgeInsets.zero,
    );
  }

  Widget _buildInputTextField(Function() onAdd) {
    final theme = Theme.of(context);

    return SizedBox(
      width: fullWidth(context),
      child: TextField(
        controller: _textController,
        focusNode: _focusNode,
        decoration: InputDecoration(
          isDense: true,
          hintText: 'tag name ..',
          // fillColor: theme.colorScheme.surface,
          // filled: true,
          border: InputBorder.none,
          suffixIcon: _showAddIcon()
              ? IconButton(
                  icon: const Icon(Icons.check),
                  iconSize: Dimensions.iconSizeMedium,
                  padding: EdgeInsets.zero,
                  // color: theme.colorScheme.primary,
                  onPressed: onAdd,
                )
              : null,
          suffixIconConstraints: BoxConstraints(
            maxHeight: Dimensions.iconSizeMedium,
          ),
        ),
      ),
    );
  }

  Widget _buildSuggestionsList(Function(String) onTagSelected) {
    final theme = Theme.of(context);
    List<String> suggestions = List.from(_suggestions.difference(_tags));

    if (suggestions.isEmpty || !_focusNode.hasFocus) {
      return SizedBox.shrink();
    }

    return Container(
      constraints: BoxConstraints(maxHeight: Dimensions.suggestionsMaxHeight),
      decoration: BoxDecoration(
        // color: Theme.of(context).colorScheme.surface,
        // border: Border.all( color: theme.colorScheme.outline),
        borderRadius: BorderRadius.circular(Dimensions.borderRadiusSmall),
      ),
      child: ListView.builder(
        itemCount: suggestions.length,
        itemBuilder: (context, index) {
          final suggestion = suggestions[index];
          return ListTile(
            title: Text(suggestion),
            dense: true,
            onTap: () => onTagSelected(suggestion),
          );
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return FormField<Set<String>>(
      initialValue: _tags,

      validator: (Set<String>? value) {
        if (_textController.text.trim().isNotEmpty) {
          return 'You have an unadded tag. Tap the add icon or clear the text.';
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
                // color: theme.colorScheme.onPrimary,
                // border: Border.all(
                //     color: state.hasError
                //         ? theme.colorScheme.error
                //         : theme.colorScheme.surface),
                borderRadius: BorderRadius.circular(
                  Dimensions.borderRadiusMedium,
                ),
              ),
              child: GestureDetector(
                onTap: () {
                  if (_tags.length < widget.limit) {
                    _focusNode.requestFocus();
                  }
                },
                child: Wrap(
                  spacing: Dimensions.spacingSmall,
                  runSpacing: Dimensions.spacingNone,
                  children: [
                    ..._tags.map(
                      (tagName) => _buildTagChip(
                        tagName,
                        (tag) => _removeTag(state, tag),
                      ),
                    ),
                    if (_showEdit())
                      _buildInputTextField(
                        () => _addNewTagFromTextField(state),
                      ),
                  ],
                ),
              ),
            ),
            if (state.hasError)
              Padding(
                padding: const EdgeInsets.only(
                  left: Dimensions.paddingMedium,
                  top: Dimensions.paddingExtraSmall,
                ),
                child: Text(
                  state.errorText!,
                  style: TextStyle(
                    // color: theme.colorScheme.error,
                    fontSize: Dimensions.fontSizeSmall,
                  ),
                ),
              ),
            SizedBox(height: Dimensions.paddingExtraSmall),
            _buildSuggestionsList((tag) => _addTag(state, tag)),
          ],
        );
      },
    );
  }
}
