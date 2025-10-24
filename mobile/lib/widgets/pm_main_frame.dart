import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:infinite_scroll_pagination/infinite_scroll_pagination.dart';
import 'package:pm/common/models.dart';
import 'package:pm/widgets/base_state.dart';
import 'package:pm/widgets/config/constants.dart';
import 'package:pm/widgets/pm_app_bar.dart';
import 'package:pm/widgets/pm_filter.dart';
import 'package:pm/widgets/pm_nav_bar.dart';
import 'package:pm/widgets/pm_search_list.dart';
import 'package:sliding_up_panel/sliding_up_panel.dart';
import 'package:pm/widgets/config/theme.dart';

import 'controllers/base_controller.dart';

final GlobalKey<ScaffoldState> _scaffoldKey = GlobalKey<ScaffoldState>();

enum Mode { note, data, link, task, graph }


class Config<T extends Identifiable> {
  final Widget Function(BuildContext, T, int) listItemWidgetBuilder;
  final Widget Function(BuildContext, T, int) detailsWidgetBuilder;
  Controller controller;

  final IconData navIcon;
}


void showSnackBar(String message) {
  ScaffoldMessenger.of(
    _scaffoldKey.currentContext!,
  ).showSnackBar(SnackBar(content: Text(message)));
}

class PredictedMeMainFrame extends StatefulWidget {
  final Map<Mode, Config> configs;
  final Mode initialMode;
  final FilterCriteria initialCriteria;

  const PredictedMeMainFrame({super.key});

  @override
  State<StatefulWidget> createState() => PredictedMeMainFrameState();
}

class PredictedMeMainFrameState
    extends PredictedMeBaseState<PredictedMeMainFrame>
    with TickerProviderStateMixin {
  late PanelController _panelController;
  late AnimationController _navBarController;
  bool _listView = true;
  bool _showNavs = true;
  int _page = 0;
  late Mode _mode;
  late SearchCriteria _criteria;

  @override
  void initState() {
    _panelController = PanelController();
    _navBarController = AnimationController(
        vsync: this, duration: Duration(milliseconds: animationDuration))
    _mode = widget.initialMode;
    _criteria = widget.initialCriteria;
    super.initState();
  }


  Future<List<Identifiable>> Function(int) _buildItemsProvider(
      Config<Identifiable> config) {
    return (page) {
      redraw(cb: () => _page = page);
      return config.controller.list(_criteria, page);
    };
  }

  void _onScroll(ScrollDirection scrollDirection) {
    redraw(cb: () => scrollDirection == ScrollDirection.reverse);
  }

  void _notifyListRefreshNeeded(BuildContext context) {
    RefreshNeededNotification().dispatch(context);
  }

  Future _delete(Controller controller, Identifiable item,
      BuildContext context) async {
    return await controller.delete(item.id)
        .then((_) => _notifyListRefreshNeeded(context));
  }

  Future _save(Controller controller, Identifiable item,
      BuildContext context) async {
    return await controller.save(item)
        .then((_) => _notifyListRefreshNeeded(context));
  }

  Function(DismissDirection) _getItemDeleteHandler(Controller controller,
      Identifiable item, BuildContext context) {
    return (DismissDirection) async => await _delete(controller, item, context);
  }

  Widget Function(BuildContext, Identifiable, int) _getItemBuilder(
      Config<Identifiable> config,) {
    return (BuildContext context, Identifiable item, int index) =>
        Dismissible(
          key: ValueKey(item.hashCode),
          direction: DismissDirection.horizontal,
          background: Container(
            color: darkRaspberry,
            alignment: Alignment.centerRight,
            padding: EdgeInsets.symmetric(horizontal: Dimensions.paddingLarge,
                vertical: Dimensions.paddingSmall),
            child: Icon(Icons.delete_outline, color: background,
              size: Dimensions.iconSizeLarge,),
          ),
          onDismissed: _getItemDeleteHandler(config.controller, item, context),
          child: config.listItemWidgetBuilder(context, item, index),
        );
  }

  void Function(String) _getOnTextChanged(BuildContext context) {
    return (text) {
      redraw(cb: () =>
      _criteria = SearchCriteria(
          dateRange: _criteria.dateRange, tags: _criteria.tags, text: text));
      _notifyListRefreshNeeded(context);
    }
  }

  PredictedMeSearchList _buildSearchGrid(Config<Identifiable> config) {
    return PredictedMeSearchList(
      itemBuilder: config.listItemWidgetBuilder,
      itemsProvider: _buildItemsProvider(config),
      onScroll: _onScroll,
      initialPage: _page,);
  }

  void Function() _onNav(Mode mode) {
    return () => redraw(cb: () => _mode = mode);
  }

  @override
  Widget build(BuildContext context) {
    if (_showNavs) {
      _navBarController.forward();
    } else {
      _navBarController.reverse();
    }
    return Scaffold(
        key: _scaffoldKey,
        body: Stack(
          children: [
            CustomScrollView(
              slivers: [
                PredictedMeAppBar(onTextChanged: _getOnTextChanged(context)),
                _buildSearchGrid(widget.configs[_mode]!),
              ],
            ),
            SlidingUpPanel(
              controller: _panelController,
              maxHeight: fullHeight(context),
              minHeight: 0,
              defaultPanelState: _listView ? PanelState.CLOSED : PanelState
                  .OPEN,
              onPanelClosed: () => redraw(cb: () => _listView = true),
              panel: Center(
                child: _listView ? SizedBox.shrink() : _getEditingForm(),
              ),
            ),
          ],
        ),
        bottomNavigationBar: AnimatedContainer(
          duration: Duration(milliseconds: animationDuration),
          height: _showNavs ? Dimensions.iconSizeLarge * 3 : 0.0,
          child: PredictedNavBar(
            navs: _toNavs(),
            currentIndex: _mode.index,
          ),

        ));
  }

  List<Nav> _toNavs() {
    return widget.configs.entries
        .map((e) => Nav(e.value.navIcon, _onNav(e.key))).toList();
  }
}
