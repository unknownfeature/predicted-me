import 'package:flutter/material.dart';
import 'package:pm/widgets/config/constants.dart';
import 'package:pm/widgets/config/theme.dart'; // Import your theme colors
import 'base_state.dart';

class Nav {
  final String text;
  final IconData icon; // Use IconData for better flexibility
  final VoidCallback onTap;

  Nav(this.text, this.icon, this.onTap);
}

class PredictedNavBar extends StatefulWidget {
  final List<Nav> navs;
  final int currentIndex; // The parent must tell the nav which index is active

  const PredictedNavBar({
    super.key,
    required this.navs,
    required this.currentIndex,
  });

  @override
  State<StatefulWidget> createState() => PredictedNavBarState();
}

class PredictedNavBarState extends PredictedMeBaseState<PredictedNavBar> {
  Widget _buildNavItem(Nav nav, bool isActive) {
    final Color color = isActive ? background : greyBackgroundDark;

    return Expanded(
      child: Material(
        color: Colors.transparent,

        child: InkWell(
          onTap: nav.onTap,
          splashColor: pinkPrimary_75,
          child: Padding(
            padding: const EdgeInsets.symmetric(
              vertical: Dimensions.paddingSmall,
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(nav.icon, color: color),
                const SizedBox(height: Dimensions.sizedBoxExtraSmall),
                Text(
                  nav.text,
                  style: TextStyle(
                    color: color,
                    fontWeight: isActive ? FontWeight.bold : FontWeight.normal,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      color: pinkPrimary,
      padding: EdgeInsets.only(top: Dimensions.paddingSmall),
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
    );
  }
}
