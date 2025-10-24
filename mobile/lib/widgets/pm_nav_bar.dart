import 'dart:ui';

import 'package:flutter/material.dart';
import 'package:pm/widgets/config/constants.dart';
import 'package:pm/widgets/config/theme.dart';
import 'base_state.dart';

class Nav {
  final IconData icon;
  final VoidCallback onTap;

  Nav(this.icon, this.onTap);
}

class PredictedNavBar extends StatefulWidget {
  final List<Nav> navs;
  final int currentIndex;

  const PredictedNavBar({
    super.key,
    required this.navs,
    required this.currentIndex,
  });

  @override
  State<StatefulWidget> createState() => PredictedNavBarState();
}

class PredictedNavBarState extends PredictedMeBaseState<PredictedNavBar> {
  Widget _buildNavItem(Nav nav, bool active) {
    final Color color = active ? background : pinkBackgroundDark;

    double size = iconSizeLarge;
    return Expanded(
      child: Material(
        color: Colors.transparent,
        child: InkResponse(
          onTap: nav.onTap,
          splashColor: pinkPrimary_50,
          radius: size * 0.8,
          child: Padding(
            padding: const EdgeInsets.symmetric(
              vertical: paddingSmall,
            ),
            child: Icon(
              nav.icon,
              shadows: active ? [
                Shadow(color: pinkBackgroundDark,
                    blurRadius: size * .1)
              ] : null,
              color: color,
              size: size,
            ),
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return ClipRect(
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: sigmaX, sigmaY: sigmaY),
        child: Container(
          color: pinkPrimary_75,
          padding: EdgeInsets.only(top: paddingSmall),
          child: SafeArea(
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: widget.navs.asMap().entries.map((entry) {
                final int index = entry.key;
                final Nav nav = entry.value;
                return _buildNavItem(nav, index == widget.currentIndex);
              }).toList(),
            ),
          ),
        ),
      ),
    );
  }
}
