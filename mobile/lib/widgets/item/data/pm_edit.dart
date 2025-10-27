import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:intl/intl.dart';
import 'package:pm/common/constants.dart';
import 'package:pm/common/models.dart';
import 'package:pm/controllers/base_controller.dart';
import 'package:pm/widgets/base_state.dart';
import 'package:pm/widgets/config/constants.dart';
import 'package:pm/widgets/config/theme.dart';
import 'package:pm/widgets/pm_autocomplete.dart';
import 'package:pm/widgets/pm_messages.dart';
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

class _PredictedMeEditDataPointState
    extends PredictedMeBaseState<PredictedMeEditDataPoint> {
  final _formKey = GlobalKey<FormState>();

  late DataPoint _dataPoint;

  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _dataPoint = widget.item;
  }

  @override
  void dispose() {
    super.dispose();
  }

  void _load(bool load) {
    setState(() => _isLoading = load);
  }

  void _handleError(BuildContext context, Object e) {
    showSnackBar(context, e.toString());
    _load(false);
  }

  Future<void> _onSave(BuildContext context) async {
    if (!_formKey.currentState!.validate()) {
      return;
    }
    _formKey.currentState!.save();

    _load(true);

    try {
      final savedMetric = await widget.metricController.save(_dataPoint.metric);

      if (_dataPoint.metric.schedule != null) {
        await widget.scheduleController.save(_dataPoint.metric.schedule!);
      } else if (widget.item.metric.schedule != null &&
          widget.item.metric.schedule!.id != null) {
        await widget.scheduleController.delete(
          widget.item.metric.schedule!.id!,
        );
      }

      final dataToSave = _dataPoint.copy(
        metric: savedMetric,
      ); // todo I think it's impossible to do now, need to add

      await widget.dataController.save(dataToSave);

      widget.onDoneEditing(true, context);
    } catch (e) {
      _handleError(context, e);
    }
  }

  Future<void> _onDelete(BuildContext context) async {
    final bool didConfirm = await showDeleteConfirmationDialog(context);
    if (didConfirm && _dataPoint.id != null) {
      setState(() => _isLoading = true);
      try {
        await widget.dataController.delete(_dataPoint.id!);
        widget.onDoneEditing(true, context);
      } catch (e) {
        _handleError(context, e);
      }
    }
  }

  void _updateMetricAndUnitsIfNull(MetricDetails metric) {
    setState(
      () => _dataPoint = _dataPoint.copy(
        metric: metric,
        units: _dataPoint.units ?? metric.defaultUnits,
      ),
    );
  }

  void _updateScheduleOrSetToNull(DataSchedule? schedule) {
    setState(
      () => _dataPoint = _dataPoint.copy(
        metric: _dataPoint.metric.copy(schedule: schedule),
      ),
    );
  }

  Future<Iterable<MetricDetails>> _metricSuggestions(
    String query,
    int limit,
  ) async {
    final criteria = SearchCriteria(text: query);
    return await widget.metricController.list(criteria, 0, limit);
  }

  Future<void> _onNewMetric(String name, BuildContext context) async {
    try {
      final newMetric = await widget.metricController.save(
        MetricDetails(
          name: name,
          tagged: false,
          tags: [],
          defaultUnits: _dataPoint.units,
        ),
      );
      _updateMetricAndUnitsIfNull(newMetric);
    } catch (e) {
      showSnackBar(context, e.toString());
    }
  }

  //  change this todo
  Widget _buildTimeSelector(BuildContext context) {
    final localTime = DateTime.fromMillisecondsSinceEpoch(
      _dataPoint.time * msInSec,
      isUtc: true,
    ).toLocal();

    final formattedTime = DateFormat(dateFormat).format(localTime);

    return ListTile(
      title: Text(formattedTime),
      trailing: const Icon(Icons.edit_outlined, color: greyPrimary),
      onTap: () async {
        final newDate = await showDatePicker(
          context: context,
          initialDate: localTime,
          firstDate: DateTime(2000),
          lastDate: DateTime.now().add(const Duration(days: 1)),
        );
        if (newDate == null) return;

        final newTime = await showTimePicker(
          context: context,
          initialTime: TimeOfDay.fromDateTime(localTime),
        );
        if (newTime == null) return;

        final newLocalTime = DateTime(
          newDate.year,
          newDate.month,
          newDate.day,
          newTime.hour,
          newTime.minute,
        );

        setState(() {
          _dataPoint = _dataPoint.copy(
            time: newLocalTime.toUtc().millisecondsSinceEpoch ~/ msInSec,
          );
        });
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    String? units = _dataPoint.units ?? _dataPoint.metric.defaultUnits;
    return Form(
      key: _formKey,
      child: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(paddingSmall),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Wrap(
                  children: [
                    IconButton(
                      icon: const Icon(Icons.close),
                      onPressed: () => widget.onDoneEditing(false, context),
                    ),

                    IconButton(
                      icon: const Icon(Icons.check, color: greyPrimary),
                      onPressed: () => _onSave(context),
                    ),
                  ],
                ),

                IconButton(
                  icon: const Icon(Icons.delete_outline, color: darkRaspberry),
                  onPressed: () => _onDelete(context),
                ),
              ],
            ),
          ),

          _isLoading
              ? const Expanded(
                  child: Center(child: CircularProgressIndicator()),
                )
              : Expanded(
                  child: SingleChildScrollView(
                    padding: const EdgeInsets.all(paddingLarge),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        PredictedMeAutocomplete(
                          initialValue: _dataPoint.metric.name,
                          suggestionsSupplier: _metricSuggestions,
                          onSelected: _updateMetricAndUnitsIfNull,
                          onNew: (name) => _onNewMetric(name, context),
                          multiValued: false,
                          maxLength:
                              500, // todo set normal limits for these fields
                        ),
                        const SizedBox(height: sizedBoxExtraLarge),

                        TextFormField(
                          initialValue: _dataPoint.value.toString(),
                          decoration: const InputDecoration(
                            hintText: 'the value',
                          ),
                          keyboardType: const TextInputType.numberWithOptions(
                            decimal: true,
                          ),
                          inputFormatters: [
                            FilteringTextInputFormatter.allow(
                              RegExp(r'^\d+\.?\d*'),
                            ),
                          ],
                          validator: (val) => (val == null || val.isEmpty)
                              ? "Value is required"
                              : null,
                          onSaved: (val) => _dataPoint = _dataPoint.copy(
                            value: double.parse(val!),
                          ),
                        ),
                        const SizedBox(height: sizedBoxExtraLarge),
                        // todo add set as default checkbox
                        TextFormField(
                          initialValue: units,
                          decoration: const InputDecoration(
                            hintText: 'e.g., lbs, kg, mg',
                          ),
                          onSaved: (val) => _dataPoint = _dataPoint.copy(
                            units: val,
                            metric: _dataPoint.metric.copy(
                              defaultUnits:
                                  _dataPoint.metric.defaultUnits ?? val,
                            ),
                          ),
                        ),
                        const SizedBox(height: sizedBoxMedium),
                        SwitchListTile(
                          title: const Text("use these as default"),
                          value:
                              (units) == _dataPoint.metric.defaultUnits &&
                              (units) != null,
                          onChanged: (bool newValue) =>
                              _updateMetricAndUnitsIfNull(
                                _dataPoint.metric.copy(
                                  defaultUnits: _dataPoint.units,
                                ),
                              ),
                          dense: true,
                          contentPadding: EdgeInsets.zero,
                          activeThumbColor: greyPrimary,
                        ),

                        const SizedBox(height: sizedBoxExtraLarge),

                        _buildTimeSelector(context),

                        const SizedBox(height: sizedBoxExtraLarge),

                        PredictedMeTagsSelector(
                          initialTagNames: _dataPoint.metric.tags.toSet(),
                          tagsSupplier: (pieceOfName, limit) =>
                              widget.tagController.list(
                                SearchCriteria(text: pieceOfName),
                                0,
                                limit,
                              ),
                          onChanged: (tags) => _updateMetricAndUnitsIfNull(
                            _dataPoint.metric.copy(tags: tags.toList()),
                          ),
                          onNew: (newTag) async {
                            // todo maybe not needed as it'll crete a non existing tag
                            await widget.tagController.save(Tag(name: newTag));
                          },
                        ),
                        const SizedBox(height: sizedBoxExtraLarge),

                        PredictedMeSchedule<DataSchedule>(
                          initialSchedule:
                              _dataPoint.metric.schedule ??
                              DataSchedule.dailyMetric(
                                targetValue: _dataPoint.value,
                              ),
                          onChanged: _updateScheduleOrSetToNull,
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
