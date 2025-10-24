import 'package:flutter/material.dart';
import 'package:pm/common/models.dart';
import 'package:pm/widgets/base_state.dart';

enum ScheduleFrequency { periodic, hourly, daily, weekly, monthly }

class PredictedMeSchedule extends StatefulWidget {
  final BaseSchedule? initialSchedule;
  final Function(Map<String, dynamic> scheduleData) onSave;
  final VoidCallback onDelete;
  final Widget Function(BuildContext context) specificFieldsBuilder;

  const PredictedMeSchedule({
    Key? key,
    this.initialSchedule,
    required this.onSave,
    required this.onDelete,
    required this.specificFieldsBuilder,
  }) : super(key: key);

  @override
  State<StatefulWidget> createState() => PredictedMeScheduleState();
}

class PredictedMeScheduleState
    extends PredictedMeBaseState<PredictedMeSchedule> {
  final _formKey = GlobalKey<FormState>();
  ScheduleFrequency _frequency = ScheduleFrequency.daily;
  TimeOfDay _selectedTime = TimeOfDay.now();
  List<bool> _selectedWeekDays = List.filled(7, false); // Mon-Sun
  int _selectedMonthDay = 1;
  int _periodInSeconds = 3600; // Default to 1 hour

  @override
  void initState() {
    super.initState();
    _populateStateFromSchedule(widget.initialSchedule);
  }

  // This function reads the initial schedule and sets up the form's state
  void _populateStateFromSchedule(BaseSchedule? schedule) {
    if (schedule == null) return;

    if (schedule.periodSeconds != null) {
      _frequency = ScheduleFrequency.periodic;
      _periodInSeconds = schedule.periodSeconds!;
    } else if (schedule.minute != '*' &&
        schedule.hour != '*' &&
        schedule.dayOfWeek != '*' &&
        schedule.dayOfMonth != '*' &&
        schedule.month != '*') {
      // This is a complex custom cron, not supported by our UI
      _frequency = ScheduleFrequency.daily;
    } else if (schedule.dayOfWeek != '*') {
      _frequency = ScheduleFrequency.weekly;
      _selectedWeekDays = List.generate(7, (i) => schedule.dayOfWeek!.contains((i + 1).toString()));
    } else if (schedule.dayOfMonth != '*') {
      _frequency = ScheduleFrequency.monthly;
      _selectedMonthDay = int.tryParse(schedule.dayOfMonth!) ?? 1;
    } else if (schedule.hour != '*') {
      _frequency = ScheduleFrequency.daily;
    } else if (schedule.minute != '*') {
      _frequency = ScheduleFrequency.hourly;
    }

    if (schedule.hour != null && schedule.hour != '*') {
      _selectedTime = _selectedTime.replacing(hour: int.tryParse(schedule.hour!) ?? 0);
    }
    if (schedule.minute != null && schedule.minute != '*') {
      _selectedTime = _selectedTime.replacing(minute: int.tryParse(schedule.minute!) ?? 0);
    }
  }

  void _onSavePressed() {
    if (_formKey.currentState!.validate()) {
      _formKey.currentState!.save();

      // Translate our simple UI state into cron/period fields
      Map<String, dynamic> scheduleData = {};

      if (_frequency == ScheduleFrequency.periodic) {
        scheduleData['period_seconds'] = _periodInSeconds;
        // Clear cron fields
        scheduleData['minute'] = null;
        scheduleData['hour'] = null;
        scheduleData['day_of_month'] = null;
        scheduleData['month'] = null;
        scheduleData['day_of_week'] = null;
      } else {
        scheduleData['period_seconds'] = null;
        // Default to all
        scheduleData['minute'] = '*';
        scheduleData['hour'] = '*';
        scheduleData['day_of_month'] = '*';
        scheduleData['month'] = '*';
        scheduleData['day_of_week'] = '*';

        switch (_frequency) {
          case ScheduleFrequency.hourly:
            scheduleData['minute'] = _selectedTime.minute.toString();
            break;
          case ScheduleFrequency.daily:
            scheduleData['minute'] = _selectedTime.minute.toString();
            scheduleData['hour'] = _selectedTime.hour.toString();
            break;
          case ScheduleFrequency.weekly:
            scheduleData['minute'] = _selectedTime.minute.toString();
            scheduleData['hour'] = _selectedTime.hour.toString();
            scheduleData['day_of_week'] = _selectedWeekDays.asMap().entries
                .where((e) => e.value)
                .map((e) => (e.key + 1).toString()) // 1=Mon, 7=Sun
                .join(',');
            if(scheduleData['day_of_week'].isEmpty) scheduleData['day_of_week'] = '*';
            break;
          case ScheduleFrequency.monthly:
            scheduleData['minute'] = _selectedTime.minute.toString();
            scheduleData['hour'] = _selectedTime.hour.toString();
            scheduleData['day_of_month'] = _selectedMonthDay.toString();
            break;
          default:
            break;
        }
      }

      // Call the parent's onSave with the data
      widget.onSave(scheduleData);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Form(
      key: _formKey,
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // --- 1. The "Specific Fields" (Target or Priority) ---
            widget.specificFieldsBuilder(context),

            const SizedBox(height: 24),
            Text("Frequency", style: Theme.of(context).textTheme.titleSmall),

            // --- 2. Frequency Picker ---
            DropdownButtonFormField<ScheduleFrequency>(
              value: _frequency,
              onChanged: (newValue) {
                setState(() {
                  _frequency = newValue!;
                });
              },
              items: const [
                DropdownMenuItem(value: ScheduleFrequency.periodic, child: Text("Periodic")),
                DropdownMenuItem(value: ScheduleFrequency.hourly, child: Text("Hourly")),
                DropdownMenuItem(value: ScheduleFrequency.daily, child: Text("Daily")),
                DropdownMenuItem(value: ScheduleFrequency.weekly, child: Text("Weekly")),
                DropdownMenuItem(value: ScheduleFrequency.monthly, child: Text("Monthly")),
              ],
            ),
            const SizedBox(height: 16),

            // --- 3. Conditional UI ---
            _buildConditionalInputs(),

            const SizedBox(height: 32),

            // --- 4. Action Buttons ---
            Row(
              children: [
                TextButton(
                  onPressed: widget.onDelete,
                  child: const Text("Delete", style: TextStyle(color: Colors.red)),
                ),
                const Spacer(),
                ElevatedButton(
                  onPressed: _onSavePressed,
                  child: const Text("Save"),
                ),
              ],
            )
          ],
        ),
      ),
    );
  }

  // This widget builds the inputs that change based on frequency
  Widget _buildConditionalInputs() {
    switch (_frequency) {
      case ScheduleFrequency.periodic:
        return TextFormField(
          initialValue: _periodInSeconds.toString(),
          decoration: const InputDecoration(
            labelText: "Period (in seconds)",
            border: OutlineInputBorder(),
          ),
          keyboardType: TextInputType.number,
          validator: (val) => (val == null || int.tryParse(val) == null) ? "Must be a number" : null,
          onSaved: (val) => _periodInSeconds = int.parse(val!),
        );
      case ScheduleFrequency.hourly:
        return ListTile(
          title: Text("At minute: ${_selectedTime.minute.toString().padLeft(2, '0')}"),
          trailing: const Icon(Icons.timer_outlined),
          onTap: () async {
            final newTime = await showTimePicker(
              context: context,
              initialTime: _selectedTime,
            );
            if (newTime != null) {
              setState(() { _selectedTime = newTime; });
            }
          },
        );
      case ScheduleFrequency.daily:
        return ListTile(
          title: Text("At time: ${_selectedTime.format(context)}"),
          trailing: const Icon(Icons.timer_outlined),
          onTap: () async {
            final newTime = await showTimePicker(
              context: context,
              initialTime: _selectedTime,
            );
            if (newTime != null) {
              setState(() { _selectedTime = newTime; });
            }
          },
        );
      case ScheduleFrequency.weekly:
        return Column(
          children: [
            ListTile(
              title: Text("At time: ${_selectedTime.format(context)}"),
              trailing: const Icon(Icons.timer_outlined),
              onTap: () async {
                final newTime = await showTimePicker(
                  context: context,
                  initialTime: _selectedTime,
                );
                if (newTime != null) {
                  setState(() { _selectedTime = newTime; });
                }
              },
            ),
            const SizedBox(height: 8),
            ToggleButtons(
              isSelected: _selectedWeekDays,
              onPressed: (index) {
                setState(() { _selectedWeekDays[index] = !_selectedWeekDays[index]; });
              },
              children: const [
                Text("Mon"), Text("Tue"), Text("Wed"), Text("Thu"), Text("Fri"), Text("Sat"), Text("Sun")
              ],
            )
          ],
        );
      case ScheduleFrequency.monthly:
        return Column(
          children: [
            ListTile(
              title: Text("At time: ${_selectedTime.format(context)}"),
              trailing: const Icon(Icons.timer_outlined),
              onTap: () async {
                final newTime = await showTimePicker(
                  context: context,
                  initialTime: _selectedTime,
                );
                if (newTime != null) {
                  setState(() { _selectedTime = newTime; });
                }
              },
            ),
            const SizedBox(height: 8),
            DropdownButtonFormField<int>(
              value: _selectedMonthDay,
              decoration: const InputDecoration(labelText: "Day of Month"),
              onChanged: (day) {
                setState(() { _selectedMonthDay = day!; });
              },
              items: List.generate(31, (i) => i + 1)
                  .map((day) => DropdownMenuItem(value: day, child: Text(day.toString())))
                  .toList(),
            ),
          ],
        );
    }
  }
}