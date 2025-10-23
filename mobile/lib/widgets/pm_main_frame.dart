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

final GlobalKey<ScaffoldState> _scaffoldKey = GlobalKey<ScaffoldState>();

enum Mode { note, data, graph, link, task }

class FilterCriteria{
  String? text;
  DateRange dateRange;
  Set<String> tags;
}
class ModeConfig<T> {
  final Widget Function(BuildContext, T, int) listItemWidgetBuilder;
  final Widget Function(BuildContext, T, int) detailsWidgetBuilder;
  Future<List<T>> Function(FilterCriteria, int) itemsProvider
  final Icon navIcon;
}

void showSnackBar(String message) {
  ScaffoldMessenger.of(
    _scaffoldKey.currentContext!,
  ).showSnackBar(SnackBar(content: Text(message)));
}

class PredictedMeMainFrame<T> extends StatefulWidget {
  final ModeConfig<Note> noteConfig;
  final ModeConfig<DataPoint> dataConfig;
  final ModeConfig<Link> linkConfig;
  final ModeConfig<Task> taskConfig;
  final Mode initialMode;
  final FilterCriteria initialCriteria;

  const PredictedMeMainFrame({super.key});

  @override
  State<StatefulWidget> createState() => PredictedMeMainFrameState();
}

class PredictedMeMainFrameState<T>
    extends PredictedMeBaseState<PredictedMeMainFrame<T>>
    with TickerProviderStateMixin {
  late PanelController _panelController;
  bool _listView = true;
  int _page = 0;
  late Mode _currentMode;
  late _criteria = widget.initialCriteria;

  @override
  void initState() {
    _panelController = PanelController();
    _currentMode = widget.initialMode;
    super.initState();
  }

  ModeConfig<dynamic> _findModeConfig(){
    if (_currentMode == Mode.note){
      return widget.noteConfig;
    }

  }

  Future<List<dynamic>> Function(int) _buildItemsProvider(
      ModeConfig<dynamic> config) {
    return (page) {
      redraw(cb: () => _page = page);
      return config.itemsProvider(_criteria, page);
    };
  }
  PredictedMeSearchGrid _buildSearchGrid(ModeConfig<dynamic> config){
    return  PredictedMeSearchGrid(itemBuilder: config.listItemWidgetBuilder, itemsProvider: _buildItemsProvider(config),);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      key: _scaffoldKey,
      body: Stack(
        children: [
          CustomScrollView(
            slivers: [
              PredictedMeAppBar(onTextChanged: _onSearchTextChanged),
              PredictedMeSearchGrid(),
            ],
          ),
          SlidingUpPanel(
            controller: _panelController,
            maxHeight: fullHeight(context),
            minHeight: 0,
            defaultPanelState: _listView ? PanelState.CLOSED : PanelState.OPEN,
            onPanelClosed: () => redraw(cb: () => _listView = true),
            panel: Center(
              child: _listView ? SizedBox.shrink() : _getEditingForm(),
            ),
          ),
        ],
      ),
      bottomNavigationBar: PredictedNavBar(
        navs: navItems,
        currentIndex: _currentIndex,
      ),
    );
  }
}
