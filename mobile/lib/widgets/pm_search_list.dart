import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:infinite_scroll_pagination/infinite_scroll_pagination.dart';
import 'package:pm/widgets/base_state.dart';

import '../common/models.dart';

class RefreshNeededNotification extends Notification {}

class PredictedMeSearchList<T extends Identifiable> extends StatefulWidget {
  final Widget Function(BuildContext, T, int) itemBuilder;
  final Future<List<T>> Function(int) itemsProvider;
  final Function(ScrollDirection) onScroll;
  final int initialPage;

  const PredictedMeSearchList({
    super.key,
    required this.itemBuilder,
    required this.itemsProvider,
    required this.onScroll,
    this.initialPage = 0,
  });

  @override
  State<StatefulWidget> createState() => PredictedMeSearchListState();
}

class PredictedMeSearchListState<T extends Identifiable>
    extends PredictedMeBaseState<PredictedMeSearchList<T>> {
  late ScrollController _scrollController;
  late PagingController<int, T> _pagingController;
  late int _initialPage;

  @override
  void initState() {
    _pagingController = PagingController(
      getNextPageKey: _getNextKey,
      fetchPage: _fetchNextPage,
    );
    _scrollController = ScrollController();
    _initialPage = widget.initialPage;
    _scrollController.addListener(_onScroll);
    super.initState();
  }

  @override
  void dispose() {
    _scrollController.removeListener(_onScroll);
    _scrollController.dispose();
    _pagingController.dispose();
    super.dispose();
  }

  Future<List<T>> _fetchNextPage(int key) async {
    return await widget.itemsProvider(key);
  }

  int _getNextKey(PagingState<int, T> _pagingState) =>
      (_pagingState.keys?.last ?? _initialPage) + 1; // todo do I have to add it

  void _onScroll() {
    widget.onScroll(_scrollController.position.userScrollDirection);
  }

  bool _refresh(RefreshNeededNotification _) {
    _pagingController.refresh();
    return true;
  }

  @override
  Widget build(BuildContext context) {
    return NotificationListener<RefreshNeededNotification>(
      onNotification: _refresh,
      child: PagingListener(
        controller: _pagingController,
        builder: (context, state, fetchNextPage) => PagedListView<int, T>(
          state: state,
          scrollController: _scrollController,
          fetchNextPage: fetchNextPage,
          builderDelegate: PagedChildBuilderDelegate(
            itemBuilder: (context, item, index) {
              return widget.itemBuilder(context, item, index);
            },
          ),
        ),
      ),
    );
  }
}
