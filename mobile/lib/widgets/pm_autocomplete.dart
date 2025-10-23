import 'package:flutter/material.dart';
import 'package:pm/widgets/config/theme.dart';
import 'base_state.dart';
import 'config/constants.dart';

class PredictedMeAutocomplete extends StatefulWidget {
  final Future<Iterable<String>> Function(String) suggestionsProvider;
  final Iterable<String> Function()? excludedProvider;
  final Function(String)? onNew;
  final Function(String) onSelected;
  final Function(String)? onChanged;
  final FocusNode focusNode;
  final bool multiValued;
  final String hintText;
  final bool showCounter;
  final int maxLength;
  final OptionsViewOpenDirection optionsViewOpenDirection;

  const PredictedMeAutocomplete({
    super.key,
    required this.focusNode,
    required this.suggestionsProvider,
    required this.onSelected,
    this.onChanged,
    this.onNew,
    this.excludedProvider,
    this.hintText = 'start typing ..',
    this.multiValued = true,
    this.maxLength = 100,
    this.showCounter = false,
    this.optionsViewOpenDirection = OptionsViewOpenDirection.down,
  });

  @override
  State<StatefulWidget> createState() => PredictedMeAutocompleteState();
}

class PredictedMeAutocompleteState
    extends PredictedMeBaseState<PredictedMeAutocomplete>
    with TickerProviderStateMixin {
  final TextEditingController _textController = TextEditingController();
  late final AnimationController _animationController;
  late final Animation<double> _animation;

  bool _showAddIcon() {
    return _textController.text.length >= 3 &&
        widget.onNew != null &&
        widget.focusNode.hasFocus;
  }

  @override
  void initState() {
    super.initState();
    widget.focusNode.addListener(redraw);
    _textController.addListener(redraw);
    _animationController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: animationDuration),
    );
    _animation = CurvedAnimation(
      parent: _animationController,
      curve: Curves.easeInOut,
    );
  }

  @override
  void dispose() {
    widget.focusNode.removeListener(redraw);
    _textController.dispose();
    _animationController.dispose();
    super.dispose();
  }

  Future<void> _onSelected(String item, FormFieldState<String> state) async {
    await widget.onSelected(item);
    if (widget.multiValued) {
      _textController.clear();
    }
    state.didChange(_textController.text);
    redraw();
  }

  void _onAdded(FormFieldState<String> state) {
    if (widget.onNew != null) {
      widget.onNew!(_textController.text.trim());
    }
    if (widget.multiValued) {
      _textController.clear();
    }
    state.didChange(_textController.text);
    redraw();
  }

  IconButton? _buildSuffixIcon(FormFieldState<String> state) {
    if (!_showAddIcon()) {
      return null;
    }
    return IconButton(
      icon: const Icon(Icons.check, color: greyPrimary),
      iconSize: Dimensions.iconSizeMedium,
      padding: EdgeInsets.zero,
      onPressed: () => _onAdded(state),
    );
  }

  @override
  Widget build(BuildContext context) {
    return FormField<String>(
      initialValue: _textController.text,
      validator: (String? value) {
        if (value != null && value.trim().isNotEmpty) {
          return 'You have an unadded value. Tap the add icon or clear the text.';
        }
        return null;
      },
      builder: (FormFieldState<String> state) {
        if (widget.focusNode.hasFocus) {
          _animationController.forward();
        } else {
          _animationController.reverse();
        }
        return RawAutocomplete<String>(
          optionsViewOpenDirection: widget.optionsViewOpenDirection,
          textEditingController: _textController,
          focusNode: widget.focusNode,

          // This runs your async 'suggestionsProvider'
          optionsBuilder: (TextEditingValue textEditingValue) async {
            final String text = textEditingValue.text.trim();
            if (text.isEmpty) {
              return const Iterable<String>.empty();
            }
            final results = await widget.suggestionsProvider(text);
            if (widget.excludedProvider != null) {
              return Set.of(
                results,
              ).difference(Set.of(widget.excludedProvider!()));
            }
            return results;
          },

          onSelected: (String selection) {
            _onSelected(selection, state);
          },

          fieldViewBuilder:
              (
                BuildContext context,
                TextEditingController fieldTextEditingController,
                FocusNode fieldFocusNode,
                VoidCallback onFieldSubmitted,
              ) {
                return TextField(
                  maxLength: widget.maxLength,
                  controller: _textController,
                  focusNode: widget.focusNode,
                  onChanged: (text) {
                    state.didChange(text);
                    if (widget.onChanged != null) {
                      widget.onChanged!(text);
                    }
                  },
                  decoration: InputDecoration(
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(
                        Dimensions.borderRadiusExtraLarge,
                      ),
                      borderSide: BorderSide.none,
                    ),
                    isDense: true,
                    hintText: widget.hintText,
                    counterText: widget.showCounter ? null : empty,
                    hintStyle: TextStyle(fontSize: Dimensions.fontSizeSmall),
                    filled: widget.focusNode.hasFocus,
                    fillColor: widget.focusNode.hasFocus
                        ? greyBackground_50
                        : Colors.transparent,
                    suffixIcon: _buildSuffixIcon(state),
                    suffixIconConstraints: BoxConstraints(
                      maxHeight: Dimensions.fontSizeMedium,
                    ),
                  ),
                );
              },

          // This builds your floating suggestion list
          optionsViewBuilder:
              (
                BuildContext context,
                AutocompleteOnSelected<String> onSelected,
                Iterable<String> options,
              ) {
                return FadeTransition(
                  opacity: _animation,
                  child: Align(
                    alignment: Alignment.topCenter,
                    child: SizedBox(
                      width: fullWidth(context),
                      child: Material(
                        elevation: Dimensions.elevationMedium,
                        child: Container(
                          constraints: BoxConstraints(
                            maxHeight: quoterHeight(context),
                          ),
                          width: fullWidth(context), // Takes full width
                          child: ListView.builder(
                            shrinkWrap: true,
                            padding: EdgeInsets.zero,
                            itemCount: options.length,
                            itemBuilder: (context, index) {
                              final suggestion = options.elementAt(index);
                              return ListTile(
                                title: Text(
                                  textAlign: TextAlign.center,
                                  suggestion,
                                  style: darkOnLightTextStyle,
                                ),
                                tileColor: index % 2 == 0
                                    ? pinkBackgroundDark_25
                                    : pinkBackgroundDark_50,
                                dense: true,
                                onTap: () {
                                  onSelected(suggestion);
                                },
                              );
                            },
                          ),
                        ),
                      ),
                    ),
                  ),
                );
              },
        );
      },
    );
  }
}
