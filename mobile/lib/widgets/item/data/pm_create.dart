import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:pm/common/models.dart';
import 'package:pm/controllers/base_controller.dart';
import 'package:pm/widgets/base_state.dart';
import 'package:pm/widgets/config/constants.dart';
import 'package:pm/widgets/config/theme.dart';
import 'package:pm/widgets/pm_autocomplete.dart';

// todo review and fix AI
class FloatingDataForm extends StatefulWidget {
  final Controller<MetricDetails> metricController;
  final Controller<DataPoint> dataController;
  final Function(DataPoint) onDataPointCreated;

  const FloatingDataForm({
    Key? key,
    required this.metricController,
    required this.dataController,
    required this.onDataPointCreated,
  }) : super(key: key);

  @override
  State<StatefulWidget> createState() => _FloatingDataFormState();
}

class _FloatingDataFormState extends PredictedMeBaseState<FloatingDataForm> {
  final _formKey = GlobalKey<FormState>();
  final _metricNameController = TextEditingController();
  final _valueController = TextEditingController();
  final _unitsController = TextEditingController();
  final _focusNode = FocusNode();

  MetricDetails? _selectedMetric;
  bool _isExpanded = false;

  @override
  void initState() {
    super.initState();
    _focusNode.addListener(_onFocusChange);
  }

  @override
  void dispose() {
    _focusNode.removeListener(_onFocusChange);
    _metricNameController.dispose();
    _valueController.dispose();
    _unitsController.dispose();
    _focusNode.dispose();
    super.dispose();
  }

  void _onFocusChange() {
    setState(() {
      _isExpanded = _focusNode.hasFocus;
    });
  }

  Future<Iterable<MetricDetails>> _metricSuggestions(String query, int limit) async {
    final criteria = SearchCriteria(text: query, tsUtcStart: 0, tsUtcEnd: 0);
    return await widget.metricController.list(criteria, 0);
  }

  void _onMetricSelected(MetricDetails metric) {
    setState(() {
      _selectedMetric = metric;
      _metricNameController.text = metric.name;
      _unitsController.text = metric.defaultUnits ?? '';
    });
  }

  void _onNewMetric(String name) {
    setState(() {
      _selectedMetric = null;
      _unitsController.text = '';
    });
  }

  Future<void> _onSubmit() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }
    _formKey.currentState!.save();

    try {
      MetricDetails metricToSave;

      if (_selectedMetric != null) {
        metricToSave = _selectedMetric!;
      } else {
        metricToSave = await widget.metricController.save(
          MetricDetails(
            name: _metricNameController.text,
            tagged: false,
            tags: [],
            defaultUnits: _unitsController.text.isNotEmpty ? _unitsController.text : null,
          ),
        );
      }

      final dataPoint = DataPoint(
        value: double.parse(_valueController.text),
        units: _unitsController.text.isNotEmpty ? _unitsController.text : null,
        origin: 'user',
        time: DateTime.now().toUtc().millisecondsSinceEpoch ~/ 1000,
        metric: metricToSave,
      );

      final newDataPoint = await widget.dataController.save(dataPoint);
      widget.onDataPointCreated(newDataPoint);

      _valueController.clear();
      _unitsController.clear();
      _metricNameController.clear();
      _selectedMetric = null;
      _focusNode.unfocus();

    } catch (e) {
      showSnackBar(context, e.toString());
    }
  }

  @override
  Widget build(BuildContext context) {
    bool showUnits = _selectedMetric == null || _selectedMetric?.defaultUnits == null;

    return Material(
      elevation: 8.0,
      shadowColor: pinkShadow.withOpacity(0.5),
      borderRadius: BorderRadius.circular(Dimensions.borderRadiusExtraLarge),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeInOut,
        padding: const EdgeInsets.symmetric(horizontal: Dimensions.paddingSmall),
        decoration: BoxDecoration(
          color: background,
          borderRadius: BorderRadius.circular(Dimensions.borderRadiusExtraLarge),
        ),
        child: Form(
          key: _formKey,
          child: Row(
            children: [
              // 1. The Autocomplete
              Expanded(
                child: PredictedMeAutocomplete(
                  suggestionsSupplier: _metricSuggestions,
                  onSelected: _onMetricSelected,
                  onNew: _onNewMetric,
                  multiValued: false,
                  focusNode: _focusNode,
                  textController: _metricNameController,
                  hintText: 'Quick Add...',
                ),
              ),

              // 2. The expanding Value field
              AnimatedContainer(
                duration: const Duration(milliseconds: 300),
                curve: Curves.easeInOut,
                width: _isExpanded ? 80 : 0, // Animated width
                child: ClipRect(
                  child: Padding(
                    padding: const EdgeInsets.only(left: Dimensions.paddingSmall),
                    child: TextFormField(
                      controller: _valueController,
                      decoration: const InputDecoration(hintText: 'Value', border: InputBorder.none),
                      keyboardType: const TextInputType.numberWithOptions(decimal: true),
                      inputFormatters: [
                        FilteringTextInputFormatter.allow(RegExp(r'^\d+\.?\d*')),
                      ],
                      validator: (val) => (_isExpanded && (val == null || val.isEmpty)) ? "!" : null,
                    ),
                  ),
                ),
              ),

              // 3. The expanding Units field
              AnimatedContainer(
                duration: const Duration(milliseconds: 300),
                curve: Curves.easeInOut,
                width: _isExpanded && showUnits ? 60 : 0, // Animated width
                child: ClipRect(
                  child: Padding(
                    padding: const EdgeInsets.only(left: Dimensions.paddingSmall),
                    child: TextFormField(
                      controller: _unitsController,
                      decoration: const InputDecoration(hintText: 'Units', border: InputBorder.none),
                    ),
                  ),
                ),
              ),

              // 4. The expanding Submit button
              AnimatedContainer(
                duration: const Duration(milliseconds: 300),
                curve: Curves.easeInOut,
                width: _isExpanded ? 48 : 0, // Animated width for the button
                child: ClipRect(
                  child: IconButton(
                    icon: const Icon(Icons.check_circle, color: greyPrimary),
                    iconSize: Dimensions.iconSizeLarge,
                    onPressed: _onSubmit,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}