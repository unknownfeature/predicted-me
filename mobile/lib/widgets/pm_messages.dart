import 'package:flutter/material.dart';
import 'package:pm/widgets/config/theme.dart';

/// Shows a reusable confirmation dialog.
Future<bool> showDeleteConfirmationDialog(
  BuildContext context, [
  String title = 'Delete Item?',
  String message =
      'Are you sure you want to delete this item? This action cannot be undone.',
]) async {
  final bool? didConfirm = await showDialog(
    context: context,
    builder: (BuildContext context) {
      return AlertDialog(
        title: Text(title),
        content: Text(message),
        actions: <Widget>[
          TextButton(
            child: const Text('Cancel'),
            style: TextButton.styleFrom(
              backgroundColor: greyPrimary,
              foregroundColor: background,
            ),
            onPressed: () {
              Navigator.of(context).pop(false); // Return false
            },
          ),
          TextButton(
            child: const Text('Delete'),
            style: TextButton.styleFrom(
              backgroundColor: pinkPrimary,
              foregroundColor: background,
            ),
            onPressed: () {
              Navigator.of(context).pop(true); // Return true
            },
          ),
        ],
      );
    },
  );
  // Handle the case where the dialog is dismissed (null)
  return didConfirm ?? false;
}


void showSnackBar(BuildContext context, String message) {
  ScaffoldMessenger.of(
    context,
  ).showSnackBar(SnackBar(content: Text(message)));
}