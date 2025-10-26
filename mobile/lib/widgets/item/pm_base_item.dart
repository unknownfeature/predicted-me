import 'package:flutter/material.dart';
import 'package:pm/common/models.dart';

typedef EditWidgetSupplier =
    Widget Function({
      required Function(bool, BuildContext) onDoneEditing,
      required Identifiable item,
    });

typedef TileWidgetSupplier =
    Widget Function({
      required Function(BuildContext) onDelete,
      required Function(Identifiable) onTap,
      required Identifiable item,
    });

typedef FloatingWidgetSupplier =
    Widget Function({required Function() onSubmit});
