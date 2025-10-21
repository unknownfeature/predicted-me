import 'package:flutter/cupertino.dart';

abstract class PredictedMeBaseState<T extends StatefulWidget> extends State<T> {
  void redraw({VoidCallback? cb}) {
    setState(cb ?? () {});
  }
}
