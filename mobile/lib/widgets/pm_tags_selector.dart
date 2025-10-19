import 'package:flutter/material.dart';
import 'package:mobile/common/models.dart';

class PredictedMeTagsSelectorWidget extends StatefulWidget {
  final Set<String> _tagNames;
  final Iterable<String> Function(String) _tagsProvider;
  final Function(Set<String>) _onChanged;

  PredictedMeTagsSelectorWidget(
    Iterable<String> initialTagNames,
    Iterable<String> Function(String) tagsProvider,
    Function(Set<String>) onChanged,
  ) : this._tagNames = Set.from(initialTagNames),
      this._tagsProvider = tagsProvider,
      this._onChanged = onChanged;

  @override
  State<StatefulWidget> createState() => PredictedMeTagsSelectorState();
}

class PredictedMeTagsSelectorState extends State<PredictedMeTagsSelectorWidget>
    with TickerProviderStateMixin {
  @override
  Widget build(BuildContext context) {
    throw UnimplementedError();
  }
}
