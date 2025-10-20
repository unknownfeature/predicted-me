import 'package:flutter/material.dart';

class PredictedMeTagsSelectorWidget extends StatefulWidget {
  final Set<String> initialTagNames;
  final Iterable<String> Function(String) tagsProvider;
  final Function(Set<String>) onChanged;
  final Function(String)? onNew;
  final int limit;


  final Color? chipBorderColor;
  final Color? chipBackgroundColor;
  final Color? chipCloseIconColor;
  final Color? chipAddIconColor;
  final Color? textAreaBackgroundColor;
  final Color? textAreaBorderColor;


  const PredictedMeTagsSelectorWidget({
    Key? key,
    this.initialTagNames = const {},
    required this.tagsProvider,
    required this.onChanged,
    this.onNew,
    this.limit = 10,
    this.chipBorderColor,
    this.chipBackgroundColor,
    this.chipCloseIconColor,
    this.chipAddIconColor,
    this.textAreaBackgroundColor,
    this.textAreaBorderColor,
  }) : super(key: key);

  @override
  State<StatefulWidget> createState() => PredictedMeTagsSelectorState();
}

class PredictedMeTagsSelectorState extends State<PredictedMeTagsSelectorWidget> {
  late Set<String> _tags;

  final TextEditingController _textController = TextEditingController();
  final FocusNode _focusNode = FocusNode();
  Set<String> _suggestions = {};
  bool _showAddIcon = false;

  @override
  void initState() {
    super.initState();
    _tags = Set.from(widget.initialTagNames);
    _textController.addListener(_onTextChanged);
    _focusNode.addListener(_onFocusChange);
  }

  @override
  void dispose() {
    _textController.removeListener(_onTextChanged);
    _focusNode.removeListener(_onFocusChange);
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

  void _onFocusChange() {
    if (!_focusNode.hasFocus) {
      setState(() {
        _suggestions = {};
      });
    } else {
      _onTextChanged();
    }
  }

  void _onTextChanged() {
    final text = _textController.text.trim();
    if (text.isEmpty) {
      setState(() {
        _suggestions = {};
        _showAddIcon = false;
      });
      return;
    }

    if (_focusNode.hasFocus) {
      final results = widget.tagsProvider(text).toList();
      setState(() {
        _suggestions = Set.from(results);
        _showAddIcon = text.length >= 3;
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
        _showAddIcon = false;
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

    final tagExists = _tags.any((tag) => tag.toLowerCase() == newTag.toLowerCase());

    if (tagExists) {
      setState(() {
        _textController.clear();
        _suggestions = {};
        _showAddIcon = false;
      });
      _focusNode.requestFocus();
      return;
    }

    setState(() {
      _tags.add(newTag);
      _textController.clear();
      _suggestions = {};
      _showAddIcon = false;
    });

    widget.onChanged(_tags);
    widget.onNew?.call(newTag);
    state.didChange(_tags);
    _focusNode.requestFocus();
  }

  Widget _buildTagChip(String tagName, Function(String) onDeleted) {
    return Chip(
      label: Text(tagName),
      backgroundColor: widget.chipBackgroundColor,
      deleteIconColor: widget.chipCloseIconColor,
      side: widget.chipBorderColor == null
          ? null
          : BorderSide(color: widget.chipBorderColor!),
      onDeleted: () => onDeleted(tagName),
      visualDensity: VisualDensity.compact,
      padding: EdgeInsets.zero,
    );
  }

  Widget _buildInputTextField(Function() onAdd) {
    return SizedBox(
      width: 150, // todo media query
      child: TextField(
        controller: _textController,
        focusNode: _focusNode,
        decoration: InputDecoration(
          isDense: true,
          hintText: 'tag name ..', // todo do I need this?
          border: InputBorder.none,
          suffixIcon: _showAddIcon
              ? IconButton(
                  icon: const Icon(Icons.add_circle),
                  iconSize: 20, // todo media query
                  padding: EdgeInsets.zero,
                  color: widget.chipAddIconColor,
                  onPressed: onAdd,
                )
              : null,
          suffixIconConstraints: BoxConstraints(maxHeight: 20), // todo media query
        ),
      ),
    );
  }

  Widget _buildSuggestionsList(Function(String) onTagSelected) {
    List<String> suggestions = List.from(_suggestions);

    // Only show suggestions if the text field is focused
    if (suggestions.isEmpty || !_focusNode.hasFocus) {
      return SizedBox.shrink();
    }

    return Container(
      constraints: BoxConstraints(maxHeight: 150), // todo media query
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border.all(color: Colors.grey.shade300),
        borderRadius: BorderRadius.circular(4), // todo media query
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
    return FormField<Set<String>>(
      initialValue: _tags,
      onSaved: (newValue) {
        widget.onChanged(newValue ?? {});
      },
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
              padding: const EdgeInsets.symmetric(horizontal: 8),
              decoration: BoxDecoration(
                color: widget.textAreaBackgroundColor,
                border: Border.all(
                    color: state.hasError
                        ? Theme.of(context).colorScheme.error
                        : widget.textAreaBorderColor ?? Colors.grey.shade400),
                borderRadius: BorderRadius.circular(8),
              ),
              child: GestureDetector(
                onTap: () {
                  if (_tags.length < widget.limit) {
                    _focusNode.requestFocus();
                  }
                },
                child: Wrap(
                  spacing: 6.0,  // todo media query
                  runSpacing: 0.0,  // todo media query
                  children: [
                    ..._tags.map((tagName) =>
                        _buildTagChip(tagName, (tag) => _removeTag(state, tag))),
                    if (_tags.length < widget.limit)
                      _buildInputTextField(() => _addNewTagFromTextField(state)),
                  ],
                ),
              ),
            ),
            if (state.hasError)
              Padding(
                padding: const EdgeInsets.only(left: 12.0, top: 4.0), // todo media query
                child: Text(
                  state.errorText!,
                  style: TextStyle(
                    color: Theme.of(context).colorScheme.error,
                    fontSize: 12,
                  ),
                ),
              ),
            SizedBox(height: 4),
            _buildSuggestionsList((tag) => _addTag(state, tag)),
          ],
        );
      },
    );
  }
}