import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:pm/common/constants.dart';
import 'package:pm/common/models.dart';
import 'package:pm/controllers/base_controller.dart';
import 'package:pm/controllers/metric_schedule.dart';
import 'package:pm/widgets/base_state.dart';
import 'package:pm/widgets/config/constants.dart';
import 'package:pm/widgets/config/theme.dart';
import 'package:pm/widgets/pm_messages.dart';
import 'package:pm/widgets/pm_autocomplete.dart';
import 'package:pm/widgets/pm_schedule.dart';
import 'package:pm/widgets/pm_tags_selector.dart';

// todo continue review/fix AI
class PredictedMeEditDataPoint extends StatefulWidget {
  final Function(bool, BuildContext) onDoneEditing;
  final DataPoint item;
  final Controller<DataPoint> dataController;
  final Controller<MetricDetails> metricController;
  final Controller<Tag> tagController;
  final Controller<DataSchedule> scheduleController;

  const PredictedMeEditDataPoint({
    Key? key,
    required this.onDoneEditing,
    required this.item,
    required this.dataController,
    required this.metricController,
    required this.tagController,
    required this.scheduleController,
  }) : super(key: key);

  @override
  State<StatefulWidget> createState() => _PredictedMeEditDataPointState();
}

class _PredictedMeEditDataPointState extends PredictedMeBaseState<PredictedMeEditDataPoint> {
  final _formKey = GlobalKey<FormState>();

  late DataPoint _dataPoint;
  late MetricDetails _metricDetails;
  late DataSchedule? _schedule;


  final FocusNode _metricNameFocusNode = FocusNode();

  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    // Initialize the draft state from the widget.item
    _dataPoint = widget.item.copy();
    _metricDetails = widget.item.metric.copy();
    _schedule = widget.item.metric.schedule?.copy();

  }

  @override
  void dispose() {
    _metricNameFocusNode.dispose();
    super.dispose();
  }



  Future<void> _onSave() async {
    // 1. Validate the form
    if (!_formKey.currentState!.validate()) {
      return;
    }
    // 2. Save all FormField data into their variables
    _formKey.currentState!.save();

    setState(() { _isLoading = true; });

    try {
      final savedMetric = await widget.metricController.save(_metricDetails);

      if (_schedule != null) {
        await widget.scheduleController.save(_schedule!);
      } else if (widget.item.metric.schedule != null &&
          widget.item.metric.schedule!.id != null) {
        await widget.scheduleController.delete(_schedule!.id!);
      }

      final dataToSave = _dataPoint.copy(metric: savedMetric);
      await widget.dataController.save(dataToSave);

      // 6. Close the panel
      widget.onDoneEditing(true, context);

    } catch (e) {
      showSnackBar(e.toString());
      setState(() { _isLoading = false; });
    }
  }

  Future<void> _onDelete() async {
    final bool didConfirm = await showDeleteConfirmationDialog(context);
    if (didConfirm && _dataPoint.id != null) {
      setState(() { _isLoading = true; });
      try {
        await widget.dataController.delete(_dataPoint.id!);
        widget.onDoneEditing(true, context);
      } catch (e) {
        showSnackBar(e.toString());
        setState(() { _isLoading = false; });
      }
    }
  }

  // --- Autocomplete Callbacks ---

  Future<Iterable<MetricDetails>> _metricSuggestions(String query) async {
    final criteria = SearchCriteria(
      text: query,
      tsUtcStart: 0, // Not used for name search
      tsUtcEnd: 0, // Not used for name search
    );
    final metrics = await widget.metricController.list(criteria, 0);
    return await widget.metricController.list(criteria, 0);
  }

  Future<void> _onMetricSelected(String name) async {
    final metric = (await widget.metricController.list(
        SearchCriteria(text: name, tsUtcStart: 0, tsUtcEnd: 0), 0)
    ).firstWhere((m) => m.name == name);

    setState(() {
      _metricDetails = metric;
      _schedule = metric.schedule?.copy();
      // Update units if the new metric has a default
      if (metric.defaultUnits != null) {
        _dataPoint = _dataPoint.copy(units: metric.defaultUnits);
      }
    });
  }

  Future<void> _onNewMetric(String name, BuildContext context) async {
    try {
      final newMetric = await widget.metricController.save(
        MetricDetails(name: name, tagged: false, tags: []),
      );
      setState(() {
        _metricDetails = newMetric;
        _schedule = null;
      });
    } catch (e) {
      showSnackBar( context, e.toString());
    }
  }

  // --- Schedule Callbacks ---

  void _onScheduleDisable() {
    // Set the local schedule to null
    setState(() {
      _schedule = null;
    });
    // You can also call the controller here to delete the schedule
    // if widget.item.metric.schedule != null {
    //   widget.scheduleController.delete(widget.item.metric.schedule!.id);
    // }
  }

  void _onScheduleChanged(DataSchedule? newScheduleOrNull) {
    _schedule = newScheduleOrNull;
  }

  Widget _buildTimeSelector(BuildContext context) {
    // 1. Get the local time by converting the UTC timestamp from the state
    final localTime = DateTime.fromMillisecondsSinceEpoch(
      _dataPoint.time * 1000, // Convert seconds to milliseconds
      isUtc: true,
    ).toLocal();

    final formattedTime = DateFormat('MMM d, yyyy – hh:mm a').format(localTime);

    return ListTile(
      title: Text(formattedTime),
      trailing: const Icon(Icons.edit_outlined, color: greyPrimary),
      onTap: () async {
        // 3. Show the Date Picker first
        final newDate = await showDatePicker(
          context: context,
          initialDate: localTime,
          firstDate: DateTime(2000), // Allow picking dates from the past
          lastDate: DateTime.now().add(const Duration(days: 365)), // Allow 1 year in future
        );
        if (newDate == null) return; // User canceled

        // 4. If they picked a date, show the Time Picker
        final newTime = await showTimePicker(
          context: context,
          initialTime: TimeOfDay.fromDateTime(localTime),
        );
        if (newTime == null) return; // User canceled

        // 5. Combine the new date and time
        final newLocalTime = DateTime(
          newDate.year,
          newDate.month,
          newDate.day,
          newTime.hour,
          newTime.minute,
        );

        // 6. Update the state, converting the local time back to a UTC timestamp
        setState(() {
          _dataPoint = _dataPoint.copy(
            time: newLocalTime.toUtc().millisecondsSinceEpoch ~/ 1000,
          );
        });
      },
    );
  }
  @override
  Widget build(BuildContext context) {
    // DO NOT return a Scaffold.
    // Return the form content directly.
    return Form(
      key: _formKey,
      child: Column(
        children: [
          // --- 1. A Custom App Bar Row ---
          // This is not a real AppBar, just a Row that looks like one.
          Padding(
            padding: const EdgeInsets.all(paddingSmall),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                IconButton(
                  icon: const Icon(Icons.close),
                  onPressed: () => widget.onDoneEditing(false, context),
                ),
                const Text('Edit Data', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                Row(
                  children: [
                    IconButton(
                      icon: const Icon(Icons.delete_outline, color: error),
                      onPressed: _onDelete,
                    ),
                    IconButton(
                      icon: const Icon(Icons.check, color: greyPrimary),
                      onPressed: _onSave,
                    ),
                  ],
                ),
              ],
            ),
          ),

          // --- 2. The Form Content ---
          _isLoading
              ? const Expanded(child: Center(child: CircularProgressIndicator()))
              : Expanded( // Use Expanded to make the content scrollable
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(paddingLarge),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text("Metric Name", style: Theme.of(context).textTheme.titleSmall),
                  PredictedMeAutocomplete(
                    focusNode: _metricNameFocusNode,
                    initialValue: _metricDetails.name,
                    suggestionsSupplier: _metricSuggestions,
                    onSelected: _onMetricSelected,
                    onNew: _onNewMetric,
                    onChanged: (val) => _metricDetails = _metricDetails.copy(name: val),
                    multiValued: false,
                  ),
                  const SizedBox(height: sizedBoxExtraLarge),

                  // --- Data Value ---
                  Text("Value", style: Theme.of(context).textTheme.titleSmall),
                  TextFormField(
                    initialValue: _dataPoint.value.toString(),
                    decoration: const InputDecoration(hintText: 'Enter value'),
                    keyboardType: const TextInputType.numberWithOptions(decimal: true),
                    inputFormatters: [
                      FilteringTextInputFormatter.allow(RegExp(r'^\d+\.?\d*')),
                    ],
                    validator: (val) => (val == null || val.isEmpty) ? "Value is required" : null,
                    onSaved: (val) => _dataPoint = _dataPoint.copy(value: double.parse(val!)),
                  ),
                  const SizedBox(height: sizedBoxExtraLarge),

                  // --- Data Units ---
                  Text("Units", style: Theme.of(context).textTheme.titleSmall),
                  TextFormField(
                    initialValue: _dataPoint.units ?? _metricDetails.defaultUnits,
                    decoration: const InputDecoration(hintText: 'e.g., lbs, kg, mg'),
                    onSaved: (val) => _dataPoint = _dataPoint.copy(units: val),
                  ),
                  const SizedBox(height: sizedBoxExtraLarge),

                  Text("Time", style: Theme.of(context).textTheme.titleSmall),
                  _buildTimeSelector(context),
                  const SizedBox(height: sizedBoxExtraLarge),

                  PredictedMeTagsSelector(
                    initialTagNames: _metricDetails.tags.toSet(),
                    tagsSupplier: (pieceOfName, limit) => widget.tagController.list(SearchCriteria(text: pieceOfName), 0),
                    onChanged: (tags) => _metricDetails = _metricDetails.copy(tags: tags.toList()),
                    onNew: (newTag) async {
                      await widget.tagController.save(Tag(id: null, name: newTag));
                    },
                  ),
                  const SizedBox(height: sizedBoxExtraLarge),

                  PredictedMeSchedule<DataSchedule>(
                    initialSchedule: _schedule ?? DataSchedule.dailyMetric(targetValue: _dataPoint.value),
                    onChanged: _onScheduleChanged,

                  ),

                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}