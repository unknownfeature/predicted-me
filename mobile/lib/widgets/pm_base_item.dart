import 'package:flutter/material.dart';
import 'package:pm/common/models.dart';

typedef EditWidgetSupplier =
    Widget Function({
      Function(bool, BuildContext) onDoneEditing,
      Identifiable item,
    });

typedef TileWidgetSupplier =
    Widget Function({
      Function(BuildContext) onDelete,
      Function(Identifiable) onTap,
      Identifiable item,
    });
