import 'package:flutter/material.dart';
import 'package:pm/widgets/base_state.dart';
import 'package:pm/widgets/config/constants.dart';

import 'config/theme.dart';

class PredictedMeAppBar extends StatefulWidget {
  final void Function(String) onTextChanged;
  final String? initialText;
  final Function() onLeadingTap;
  final List<Widget>? actions;

  PredictedMeAppBar({
    Key? key,
    required this.onTextChanged,
    required this.onLeadingTap,
    this.actions,
    this.initialText,
  }) : super(key: key);

  @override
  State<StatefulWidget> createState() => PredictedMeAppBarState();
}

class PredictedMeAppBarState extends PredictedMeBaseState<PredictedMeAppBar>
    with TickerProviderStateMixin{
  late final TextEditingController _textController;
  late final FocusNode _focusNode;
  late final AnimationController _animationController;

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      vsync: this,
      duration: animationDuration,
    );
    _focusNode = FocusNode();
    _textController = TextEditingController(text: widget.initialText ?? empty);
    _textController.addListener(_onTextChanged);
    _focusNode.addListener(_onFocusChanged);
  }

  @override
  void dispose() {
    _textController.removeListener(_onTextChanged);
    _focusNode.removeListener(_onFocusChanged);
    _textController.dispose();
    _focusNode.dispose();
    _animationController.dispose();
    super.dispose();
  }

  void _onFocusChanged() {
    if (_focusNode.hasFocus) {
      _animationController.reverse();
    } else {
      _animationController.forward();
    }
    redraw();
  }

  void _onTextChanged() {
    redraw(cb: () => widget.onTextChanged(_textController.text.trim()));
  }

  Widget? _buildSuffixIcon() {
    if (_textController.text.trim().isEmpty) {
      return null;
    }
    return IconButton(
      icon: const Icon(Icons.close_outlined, color: greyPrimary),
      iconSize: iconSizeMedium,
      padding: EdgeInsets.zero,
      onPressed: () {
        _textController.clear();
        _onTextChanged();
      },
    );
  }

  Widget _buildSearchBarRow() {
    return TextField(
      focusNode: _focusNode,
      controller: _textController,
      decoration: InputDecoration(
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(
            borderRadiusExtraLarge,
          ),
          borderSide: BorderSide.none,
        ),
        isDense: true,
        hintText: _focusNode.hasFocus ? empty : 'find something ...',
        counterText: empty,
        hintStyle: TextStyle(fontSize: fontSizeMedium),
        suffixIcon: _buildSuffixIcon(),
        suffixIconConstraints: BoxConstraints(
          maxHeight: fontSizeMedium,
        ),
      ),
    );
  }


  @override
  Widget build(BuildContext context) {
    return SliverSafeArea(
      sliver: SliverPadding(
        padding: EdgeInsets.only(
          left: paddingMedium,
          right: paddingMedium,
        ),
        sliver: SliverAppBar(
          backgroundColor: background,
          shadowColor: pinkShadow,
          shape: const RoundedRectangleBorder(
            borderRadius: BorderRadius.all(
              Radius.circular(borderRadiusExtraLarge),
            ),
          ),
          floating: true,
          elevation: elevationMedium,
          forceElevated: true,
          title: _buildSearchBarRow(),
          actions: widget.actions,
          leading: IconButton(
            icon: AnimatedIcon(
              icon: AnimatedIcons.search_ellipsis,
              progress: _animationController,
            ),
            onPressed: widget.onLeadingTap,
          ),
        ),
      ),
    );
  }


}
