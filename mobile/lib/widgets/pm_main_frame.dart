import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:infinite_scroll_pagination/infinite_scroll_pagination.dart';
import 'package:pm/common/models.dart';
import 'package:pm/widgets/base_state.dart';
import 'package:pm/widgets/config/constants.dart';
import 'package:pm/widgets/pm_app_bar.dart';
import 'package:pm/widgets/item/pm_base_item.dart';
import 'package:pm/widgets/pm_filter.dart';
import 'package:pm/widgets/pm_nav_bar.dart';
import 'package:pm/widgets/pm_search_list.dart';
import 'package:sliding_up_panel/sliding_up_panel.dart';
import 'package:pm/widgets/config/theme.dart';

import '../controllers/base_controller.dart';

final GlobalKey<ScaffoldState> _scaffoldKey = GlobalKey<ScaffoldState>();

enum Mode { note, data, link, task, graph }

class Config<T extends Identifiable> {
  final EditWidgetSupplier editSupplier;
  final TileWidgetSupplier tileSupplier;
  final FloatingWidgetSupplier floatingActionSupplier;

  final Future<List<T>> Function(SearchCriteria criteria, int page) itemsSupplier;

  final IconData navIcon;
  final bool latestItemAtTheBottomOfTheList;

  Config({
    required this.editSupplier,
    required this.tileSupplier,
    required this.itemsSupplier,
    required this.floatingActionSupplier,
    required this.navIcon,
    required this.latestItemAtTheBottomOfTheList
  });
}

void showSnackBar(String message) {
  ScaffoldMessenger.of(
    _scaffoldKey.currentContext!,
  ).showSnackBar(SnackBar(content: Text(message)));
}

class PredictedMeMainFrame extends StatefulWidget {
  final Map<Mode, Config> configs;
  final Mode initialMode;
  final SearchCriteria initialCriteria;
  final Future<Iterable<Tag>> Function(String, int) tagsSupplier;

  const PredictedMeMainFrame({
    super.key,
    required this.configs,
    required this.initialMode,
    required this.initialCriteria,
    required this.tagsSupplier,
  });

  @override
  State<StatefulWidget> createState() => PredictedMeMainFrameState();
}

class PredictedMeMainFrameState
    extends PredictedMeBaseState<PredictedMeMainFrame> {
  late PanelController _itemDetailsPanelController;

  bool _listView = true;
  bool _showNavs = true;
  int _page = 0;
  late Mode _mode;
  late SearchCriteria _criteria;
  late Identifiable? _item;

  @override
  void initState() {
    _itemDetailsPanelController = PanelController();
    _mode = widget.initialMode;
    _criteria = widget.initialCriteria;
    super.initState();
  }

  @override
  void dispose() {
    super.dispose();
  }

  Future<List<Identifiable>> Function(int) _buildItemsSupplier(
    Config<Identifiable> config,
  ) {
    return (page) {
      _page = page; // no redraw
      return config.itemsSupplier(_criteria, page);
    };
  }

  void _onScroll(ScrollDirection scrollDirection) {
    redraw(cb: () => _showNavs = scrollDirection == ScrollDirection.reverse);
  }

  void _notifyListRefreshNeeded(BuildContext context) {
    RefreshNeededNotification().dispatch(context);
  }

  void _startEdit(Identifiable item) {
    redraw(
      cb: () {
        _item = item;
        _listView = false;
      },
    );

    _itemDetailsPanelController.show();
  }

  void _finishEdit() {
    redraw(
      cb: () {
        _listView = true;
      },
    );
    _itemDetailsPanelController.hide();
  }

  void Function(String) _getOnTextChanged(BuildContext context) {
    return (text) {
      _criteria = SearchCriteria(
        tsUtcStart: _criteria.tsUtcStart,
        tsUtcEnd: _criteria.tsUtcEnd,
        tags: _criteria.tags,
        text: text,
      );
      _notifyListRefreshNeeded(context);
    };
  }

  void Function(int, int, Set<String>) _getOnFilterCriteriaChanged(
    BuildContext context,
  ) {
    return (start, end , tags) {
      _criteria = SearchCriteria(
        tsUtcStart: start,
        tsUtcEnd: end,
        tags: tags,
        text: _criteria.text,
      );
      _notifyListRefreshNeeded(context);
    };
  }

  Widget Function(BuildContext, Identifiable) _getTileWidgetBuilder(
    Config config,
  ) {
    return (context, item) => config.tileSupplier(
      item: item,
      onDelete: _notifyListRefreshNeeded,
      onTap: _startEdit,
    );
  }

  PredictedMeSearchList _buildSearchList(Config<Identifiable> config) {
    return PredictedMeSearchList(
      tile: _getTileWidgetBuilder(config),
      supplier: _buildItemsSupplier(config),
      onScroll: _onScroll,
      initialPage: _page,
      reverse: config.latestItemAtTheBottomOfTheList,
    );
  }

  void _onDoneEditingItem(bool didEdit, BuildContext context) {
    if (didEdit) {
      _notifyListRefreshNeeded(context);
    }
    _finishEdit();
  }

  Center _buildEditWidget(Config<Identifiable> config) {
    return Center(
      child: _listView
          ? SizedBox.shrink()
          : config.editSupplier(
              item: _item!,
              onDoneEditing: _onDoneEditingItem,
            ),
    );
  }

  List<Nav> _toNavs() {
    return widget.configs.entries
        .map((e) => Nav(e.value.navIcon, _onNav(e.key)))
        .toList();
  }

  void Function() _onNav(Mode mode) {
    return () => redraw(
      cb: () {
        _mode = mode;
        _showNavs = false;
      },
    );
  }

  void _maybeOpenDrawer() {
    if (_scaffoldKey.currentState != null) {
      _scaffoldKey.currentState!.openDrawer();
    }
  }

  void _maybeCloseDrawer() {
    if (_scaffoldKey.currentState != null) {
      _scaffoldKey.currentState!.closeDrawer();
    }
  }

  Widget _showFilterAction(BuildContext context) {
    return IconButton(
      onPressed: () => _showFilter(context),
      icon: Icon(Icons.filter_list_outlined, size: iconSizeMedium),
    );
  }

  void _showFilter(BuildContext context) {
    showDialog(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: Align(
            alignment: Alignment.topRight,
            child: IconButton(
              onPressed: Navigator.of(context).pop,
              icon: Icon(Icons.close_outlined, size: iconSizeMedium),
            ),
          ),
          content: SizedBox(
            height: quoterHeight(context),
            width: double.maxFinite,

            child: SingleChildScrollView(
              child: PredictedMeFilter(
                onCriteriaChanged: _getOnFilterCriteriaChanged(context),
                tagsSuggestionsSupplier: widget.tagsSupplier,
              ),
            ),
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    Config<Identifiable> config = widget.configs[_mode]!;
    return Scaffold(
      key: _scaffoldKey,
      body: Stack(
        children: [
          CustomScrollView(
            slivers: [
              PredictedMeAppBar(
                onTextChanged: _getOnTextChanged(context),
                initialText: _criteria.text,
                onLeadingTap: _maybeOpenDrawer,
                actions: [_showFilterAction(context)],
              ),
              _buildSearchList(config),
            ],
          ),

          SlidingUpPanel(
            controller: _itemDetailsPanelController,
            maxHeight: fullHeight(context),
            minHeight: 0,
            defaultPanelState: PanelState.CLOSED,
            panel: _buildEditWidget(config),
          ),
        ],
      ),
      drawer: Drawer(
        child: Center(
          child: IconButton(
            onPressed: _maybeCloseDrawer,
            icon: Icon(Icons.close_outlined, size: iconSizeLarge),
          ),
        ),
      ),
      floatingActionButton: config.floatingActionSupplier(onSubmit: () => _notifyListRefreshNeeded(context)),
      bottomNavigationBar: AnimatedContainer(
        duration: animationDuration,
        height: _showNavs ? iconSizeLarge * 3 : 0.0, // todo calc this better
        child: PredictedNavBar(navs: _toNavs(), currentIndex: _mode.index),
      ),
    );
  }
}
