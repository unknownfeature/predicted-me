import 'package:flutter/material.dart';
import 'package:intl/intl.dart'; // Add 'intl' package
import 'package:expandable/expandable.dart'; // Add 'expandable' package
import 'package:pm/common/models.dart';
import 'package:pm/controllers/base_controller.dart';
import 'package:pm/widgets/base_state.dart';
import 'package:pm/widgets/config/constants.dart';
import 'package:pm/widgets/config/theme.dart';

import '../common/constants.dart';

class SaveScheduleNotification extends Notification {}

class PredictedMeSchedule<T extends BaseSchedule> extends StatefulWidget {
  final T? initialSchedule;
  final Function onDisable;
  final Function(String, String, String, int) onChanged;

  const PredictedMeSchedule({
    Key? key,
    required this.onDisable,
    required this.onChanged,

    this.initialSchedule,
  }) : super(key: key);

  @override
  State<StatefulWidget> createState() => PredictedMeScheduleState<T>();
}

class PredictedMeScheduleState<T extends BaseSchedule>
    extends PredictedMeBaseState<PredictedMeSchedule<T>> {
  final _formKey = GlobalKey<FormState>();

  late TimeOfDay _selectedTime;
  late List<bool> _selectedWeekDays;
  late int _nextRun;
  late T? _schedule;

  late ExpandableController _expandableController;

  @override
  void initState() {
    super.initState();

    _schedule = widget.initialSchedule;

    _selectedWeekDays = _cronToDaysOfWeek(_schedule);
    _selectedTime = _cronToTimeOfDay(_schedule);
    _nextRun = _calculateNextRun(_selectedWeekDays, _selectedTime);

    _expandableController = ExpandableController(
      initialExpanded: _schedule != null,
    );
  }

  // todo review AI
  int _calculateNextRun(List<bool> selectedDays, TimeOfDay selectedTime) {
    final DateTime now = DateTime.now();

    DateTime targetTimeToday = DateTime(
      now.year,
      now.month,
      now.day,
      selectedTime.hour,
      selectedTime.minute,
    );

    int todayIndex = now.weekday - 1; // 0=Mon, 6=Sun
    if (selectedDays[todayIndex] && targetTimeToday.isAfter(now)) {
      return targetTimeToday.toUtc().millisecondsSinceEpoch ~/ msInSec;
    }

    for (int daysToAdd = 1; daysToAdd <= 7; daysToAdd++) {
      final DateTime nextDay = now.add(Duration(days: daysToAdd));
      final int nextDayIndex = nextDay.weekday - 1; // 0=Mon, 6=Sun

      if (selectedDays[nextDayIndex]) {
        final DateTime nextRunTime = DateTime(
          nextDay.year,
          nextDay.month,
          nextDay.day,
          selectedTime.hour,
          selectedTime.minute,
        );
        return nextRunTime.toUtc().millisecondsSinceEpoch ~/ msInSec;
      }
    }

    // FIX: If no days are selected, return 0
    return 0;
  }

  TimeOfDay _cronToTimeOfDay(T? schedule) {
    if (schedule == null) {
      return const TimeOfDay(hour: 9, minute: 0); // Default
    }

    int hour = int.parse(schedule.hour);
    int minute = int.parse(schedule.minute);

    DateTime utcNow = DateTime.now().toUtc();
    DateTime utcAdjusted = DateTime.utc(
      utcNow.year,
      utcNow.month,
      utcNow.day,
      hour,
      minute,
    );
    DateTime local = utcAdjusted.toLocal();

    return TimeOfDay(hour: local.hour, minute: local.minute);
  }

  TimeOfDay _timeOfDayToUtcTime(TimeOfDay local) {
    DateTime localNow = DateTime.now();
    DateTime localAdjusted = DateTime(
      localNow.year,
      localNow.month,
      localNow.day,
      local.hour,
      local.minute,
    );
    DateTime inUtc = localAdjusted.toUtc();
    return TimeOfDay(hour: inUtc.hour, minute: inUtc.minute);
  }

  List<bool> _cronToDaysOfWeek(T? schedule) {
    if (schedule == null || schedule.dayOfWeek == '*') {
      return List.filled(7, true);
    }

    Set<int> days = schedule.dayOfWeek.split(',').map(int.parse).toSet();
    return List.generate(7, (index) => days.contains(index + 1));
  }

  String _daysOfWeekToCron(List<bool> daysOfWeek) {
    Iterable<int> thoseThatTrue = daysOfWeek
        .asMap()
        .entries
        .where((item) => item.value)
        .map((item) => item.key + 1); // 1-7
    if (thoseThatTrue.length == 7) {
      return '*';
    }
    return thoseThatTrue.isEmpty ? '*' : thoseThatTrue.join(',');
  }

  void _onToggleHeader() {
    if (_schedule == null) {
      redraw(
        cb: () {
          _schedule = widget.initialSchedule;
          _selectedWeekDays = _cronToDaysOfWeek(_schedule);
          _selectedTime = _cronToTimeOfDay(_schedule);
          _nextRun = _calculateNextRun(_selectedWeekDays, _selectedTime);
        },
      );
    } else {
      widget.onDisable();
      redraw(cb: () => _schedule = null);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final bool isEnabled = _schedule != null;

    return Form(
      key: _formKey,
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(paddingMedium),
        child: ExpandablePanel(
          controller: _expandableController,
          theme: const ExpandableThemeData(
            headerAlignment: ExpandablePanelHeaderAlignment.center,
            hasIcon: false,
            tapHeaderToExpand: false,
            tapBodyToCollapse: false,
            useInkWell: false,
          ),

          header: InkWell(
            onTap: _onToggleHeader,
            child: Padding(
              padding: const EdgeInsets.symmetric(vertical: paddingSmall),
              child: Row(
                children: [
                  Icon(
                    Icons.repeat_outlined,
                    color: isEnabled ? greyPrimary : greyShadow,
                  ),
                  const SizedBox(width: paddingSmall),
                  Text(
                    "Repeat on:",
                    style: theme.textTheme.titleMedium?.copyWith(
                      color: isEnabled ? greyPrimary : greyShadow,
                    ),
                  ),
                ],
              ),
            ),
          ),

          collapsed: const SizedBox.shrink(),

          expanded: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: paddingSmall),
              _buildDaySelector(),

              const SizedBox(height: sizedBoxExtraLarge),

              Text("At:", style: theme.textTheme.titleSmall),
              _buildTimeSelector(),

              if (isEnabled && _schedule!.nextRun > 0)
                const SizedBox(height: sizedBoxExtraLarge),

              if (isEnabled && _schedule!.nextRun > 0) _buildNextRun(),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildDaySelector() {
    final days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    return Center(
      child: Wrap(
        spacing: spacingSmall,
        alignment: WrapAlignment.center,
        children: days.asMap().entries.map((entry) {
          final int index = entry.key;
          final String day = entry.value;
          return Column(
            children: [
              Text(
                day,
                style: TextStyle(
                  color: _selectedWeekDays[index] ? greyPrimary : greyShadow,
                ),
              ),
              Checkbox(
                value: _selectedWeekDays[index],
                onChanged: (bool? value) {
                  redraw(
                    cb: () {
                      _selectedWeekDays[index] = value!;
                      _nextRun = _calculateNextRun(
                        _selectedWeekDays,
                        _selectedTime,
                      );
                    },
                  );
                  _notifyChanged();
                },
              ),
            ],
          );
        }).toList(),
      ),
    );
  }

  Widget _buildTimeSelector() {
    return ListTile(
      title: Text("At: ${_selectedTime.format(context)}"),
      trailing: const Icon(Icons.edit_outlined, color: greyPrimary),
      onTap: () async {
        final newTime = await showTimePicker(
          context: context,
          initialTime: _selectedTime,
        );
        if (newTime != null) {
          redraw(
            cb: () {
              _selectedTime = newTime;
              _nextRun = _calculateNextRun(_selectedWeekDays, _selectedTime);
            },
          );
          _notifyChanged();
        }
      },
    );
  }

  void _notifyChanged() {
    TimeOfDay selectedUtc = _timeOfDayToUtcTime(_selectedTime);
    widget.onChanged(
      _daysOfWeekToCron(_selectedWeekDays),
      selectedUtc.hour.toString(),
      selectedUtc.minute.toString(),
      _nextRun,
    );
  }

  Widget _buildNextRun() {
    final nextRunTime = DateTime.fromMillisecondsSinceEpoch(
      _nextRun * 1000,
      isUtc: true,
    ).toLocal();
    final formattedTime = DateFormat(
      'MMM d, yyyy – hh:mm a',
    ).format(nextRunTime);

    return ListTile(
      leading: const Icon(Icons.update, color: greyShadow),
      title: const Text("Next run"),
      subtitle: Text(formattedTime),
    );
  }
}
