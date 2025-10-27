import 'constants.dart';



abstract class Identifiable {
  int? get id;
}

abstract class Named {
  String get name;
}


// --- Base Models ---

class Tag implements Identifiable, Named {
  @override
  final int? id;
  final String name;

  Tag({this.id, required this.name});

  factory Tag.fromJson(Map<String, dynamic> json) {
    return Tag(
      id: json[kId],
      name: json[kName],
    );
  }
}

class User implements Identifiable {
  @override
  final int? id;
  final String? name;

  User({required this.id, this.name});

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json[kId],
      name: json[kName],
    );
  }
}
class Note implements Identifiable {
  @override
  final int? id;
  final String? text;
  final int time;
  final String? imageKey;
  final String? audioKey;
  final bool imageDescribed;
  final bool audioTranscribed;
  final String? imageText;
  final String? imageDescription;
  final String? audioText;

  Note({
    this.id, // Changed to optional
    this.text,
    required this.time,
    this.imageKey,
    this.audioKey,
    required this.imageDescribed,
    required this.audioTranscribed,
    this.imageText,
    this.imageDescription,
    this.audioText,
  });

  factory Note.fromJson(Map<String, dynamic> json) {
    return Note(
      id: json[kId],
      text: json[kText],
      time: json[kTime],
      imageKey: json[kImageKey],
      audioKey: json[kAudioKey],
      imageDescribed: json[kImageDescribed],
      audioTranscribed: json[kAudioTranscribed],
      imageText: json[kImageText],
      imageDescription: json[kImageDescription],
      audioText: json[kAudioText],
    );
  }

  Note copy({
    int? id,
    String? text,
    int? time,
    String? imageKey,
    String? audioKey,
    bool? imageDescribed,
    bool? audioTranscribed,
    String? imageText,
    String? imageDescription,
    String? audioText,
  }) {
    return Note(
      id: id ?? this.id,
      text: text ?? this.text,
      time: time ?? this.time,
      imageKey: imageKey ?? this.imageKey,
      audioKey: audioKey ?? this.audioKey,
      imageDescribed: imageDescribed ?? this.imageDescribed,
      audioTranscribed: audioTranscribed ?? this.audioTranscribed,
      imageText: imageText ?? this.imageText,
      imageDescription: imageDescription ?? this.imageDescription,
      audioText: audioText ?? this.audioText,
    );
  }
}

class Link implements Identifiable, Named {
  @override
  final int? id;
  final int? noteId;
  final String url;
  final String summary;
  final String? description;
  final bool tagged;
  final int time;
  final List<String> tags;

  Link({
    this.id, // Changed to optional
    this.noteId,
    required this.url,
    required this.summary,
    this.description,
    required this.tagged,
    required this.time,
    required this.tags,
  });

  @override
  String get name => summary;

  factory Link.fromJson(Map<String, dynamic> json) {
    return Link(
      id: json[kId],
      noteId: json[kNoteId],
      url: json[kUrl],
      summary: json[kSummary],
      description: json[kDescription],
      tagged: json[kTagged],
      time: json[kTime],
      tags: List<String>.from(json[kTags] ?? []),
    );
  }

  Link copy({
    int? id,
    int? noteId,
    String? url,
    String? summary,
    String? description,
    bool? tagged,
    int? time,
    List<String>? tags,
  }) {
    return Link(
      id: id ?? this.id,
      noteId: noteId ?? this.noteId,
      url: url ?? this.url,
      summary: summary ?? this.summary,
      description: description ?? this.description,
      tagged: tagged ?? this.tagged,
      time: time ?? this.time,
      tags: tags ?? this.tags,
    );
  }
}

class Task implements Identifiable, Named {
  @override
  final int? id;
  final String summary;
  final String description;
  final List<String> tags;

  Task({
    this.id,
    required this.summary,
    required this.description,
    required this.tags,
  });

  factory Task.fromJson(Map<String, dynamic> json) {
    return Task(
      id: json[kId],
      summary: json[kSummary],
      description: json[kDescription],
      tags: List<String>.from(json[kTags] ?? []),
    );
  }

  @override
  String get name => summary;

  Task copy({
    int? id,
    String? summary,
    String? description,
    List<String>? tags,
  }) {
    return Task(id: id ?? this.id,
        summary: summary ?? this.summary,
        description: description ?? this.description,
        tags: tags ?? this.tags);
  }
}
class Metric implements Identifiable, Named {
  @override
  final int? id;
  @override
  final String name;
  final List<String> tags;

  Metric({
    this.id, // Changed to optional
    required this.name,
    required this.tags,
  });

  factory Metric.fromJson(Map<String, dynamic> json) {
    return Metric(
      id: json[kId],
      name: json[kName],
      tags: List<String>.from(json[kTags] ?? []),
    );
  }

  Metric copy({
    int? id,
    String? name,
    List<String>? tags,
  }) {
    return Metric(
      id: id ?? this.id,
      name: name ?? this.name,
      tags: tags ?? this.tags,
    );
  }
}

// --- Nested Schedule Models ---

abstract class BaseSchedule implements Identifiable {
  @override
  final int? id;
  final String minute;
  final String hour;
  final String dayOfMonth;
  final String month;
  final String dayOfWeek;
  final int? periodSeconds;
  final int nextRun;

  BaseSchedule({
    required this.id,
    required this.minute,
    required this.hour,
    required this.dayOfMonth,
    required this.month,
    required this.dayOfWeek,
    this.periodSeconds,
    required this.nextRun,
  });

  Map<String, dynamic> toJson() => {
    kId: id,
    kMinute: minute,
    kHour: hour,
    kDayOfMonth: dayOfMonth,
    kMonth: month,
    kDayOfWeek: dayOfWeek,
    kPeriodSeconds: periodSeconds,
    kNextRun: nextRun,
  };

  BaseSchedule copy({
    String? minute,
    String? hour,
    String? dayOfMonth,
    String? month,
    String? dayOfWeek,
    int? periodSeconds,
    int? nextRun,
  });
}

class DataSchedule extends BaseSchedule {
  final double targetValue;
  final String? units;

  DataSchedule({
    required super.id,
    required super.minute,
    required super.hour,
    required super.dayOfMonth,
    required super.month,
    required super.dayOfWeek,
    super.periodSeconds,
    required super.nextRun,
    required this.targetValue,
    this.units,
  });

  factory DataSchedule.fromJson(Map<String, dynamic> json) {
    return DataSchedule(
      id: json[kId],
      minute: json[kMinute],
      hour: json[kHour],
      dayOfMonth: json[kDayOfMonth],
      month: json[kMonth],
      dayOfWeek: json[kDayOfWeek],
      periodSeconds: json[kPeriodSeconds],
      nextRun: json[kNextRun],
      targetValue: (json[kTargetValue] as num).toDouble(),
      units: json[kUnits],
    );
  }
  factory DataSchedule.dailyMetric({
    int? id,
    required double targetValue,
    String? units,
  }) {
    return DataSchedule(
      id: id,
      minute: '0',                   // Default minute: 0
      hour: '9',                     // Default hour: 9
      dayOfMonth: '*',             // Default dayOfMonth: '*'
      month: '*',                  // Default month: '*'
      dayOfWeek: '*',              // Default dayOfWeek: '*'
      periodSeconds: null,
      nextRun: 0,                  // Assume 0 or logic to calculate next run
      targetValue: targetValue,
      units: units,
    );
  }

  DataSchedule copy({
    String? minute,
    String? hour,
    String? dayOfMonth,
    String? month,
    String? dayOfWeek,
    int? periodSeconds,
    int? nextRun,
  }) {
    return DataSchedule(
      id: id,
      minute: minute ?? this.minute,
      hour: hour ?? this.hour,
      dayOfMonth: dayOfMonth ?? this.dayOfMonth,
      month: month ?? this.month,
      dayOfWeek: dayOfWeek ?? this.dayOfWeek,
      periodSeconds: periodSeconds ?? this.periodSeconds,
      nextRun: nextRun ?? this.nextRun,
      targetValue: targetValue,
      units: units,
    );
  }

  @override
  Map<String, dynamic> toJson() => super.toJson()..addAll({
    kTargetValue: targetValue,
    kUnits: units,
  });
}

class OccurrenceSchedule extends BaseSchedule {
  final int priority;

  OccurrenceSchedule({
    required super.id,
    required super.minute,
    required super.hour,
    required super.dayOfMonth,
    required super.month,
    required super.dayOfWeek,
    super.periodSeconds,
    required super.nextRun,
    required this.priority,
  });

  factory OccurrenceSchedule.fromJson(Map<String, dynamic> json) {
    return OccurrenceSchedule(
      id: json[kId],
      minute: json[kMinute],
      hour: json[kHour],
      dayOfMonth: json[kDayOfMonth],
      month: json[kMonth],
      dayOfWeek: json[kDayOfWeek],
      periodSeconds: json[kPeriodSeconds],
      nextRun: json[kNextRun],
      priority: json[kPriority],
    );
  }

  factory OccurrenceSchedule.dailyOccurrence({
    required int id,
    required int priority,
  }) {
    return OccurrenceSchedule(
      id: id,
      minute: '0',                   // Default minute: 0
      hour: '9',                     // Default hour: 9
      dayOfMonth: '*',             // Default dayOfMonth: '*'
      month: '*',                  // Default month: '*'
      dayOfWeek: '*',              // Default dayOfWeek: '*'
      periodSeconds: null,
      nextRun: 0,                  // Assume 0 or logic to calculate next run
      priority: priority,
    );
  }


  OccurrenceSchedule copy({
    String? minute,
    String? hour,
    String? dayOfMonth,
    String? month,
    String? dayOfWeek,
    int? periodSeconds,
    int? nextRun,
  }) {
    return OccurrenceSchedule(
      id: id,
      minute: minute ?? this.minute,
      hour: hour ?? this.hour,
      dayOfMonth: dayOfMonth ?? this.dayOfMonth,
      month: month ?? this.month,
      dayOfWeek: dayOfWeek ?? this.dayOfWeek,
      periodSeconds: periodSeconds ?? this.periodSeconds,
      nextRun: nextRun ?? this.nextRun,
      priority: priority,
    );
  }


  @override
  Map<String, dynamic> toJson() => super.toJson()..addAll({
    kPriority: priority,
  });
}

// --- Nested Response Models (from GET endpoints) ---

class MetricDetails implements Identifiable, Named {
  @override
  final int? id;
  @override
  final String name;
  final String? defaultUnits;
  final bool tagged;
  final List<String> tags;
  final DataSchedule? schedule;

  MetricDetails({
    this.id,
    required this.name,
    required this.tagged,
    required this.tags,
    this.defaultUnits,
    this.schedule,
  });

  factory MetricDetails.fromJson(Map<String, dynamic> json) {
    return MetricDetails(
      id: json[kId],
      name: json[kName],
      tagged: json[kTagged],
      tags: List<String>.from(json[kTags] ?? []),
      defaultUnits: json[kDefaultUnits],
      schedule: json[kSchedule] != null && (json[kSchedule] as Map).isNotEmpty
          ? DataSchedule.fromJson(json[kSchedule])
          : null,
    );
  }

  MetricDetails copy({
    int? id,
    String? name,
    bool? tagged,
    List<String>? tags,
    DataSchedule? schedule,
    String? defaultUnits
  }) {
    return MetricDetails(
      id: id ?? this.id,
      name: name ?? this.name,
      tagged: tagged ?? this.tagged,
      tags: tags ?? this.tags,
      schedule: (schedule ?? this.schedule)?.copy(),
      defaultUnits: defaultUnits ?? this.defaultUnits
    );
  }
}
class DataPoint implements Identifiable {
  @override
  final int? id; // Made nullable
  final int? noteId;
  final double value;
  final String? units;

  final int time;
  final MetricDetails metric;

  DataPoint({
    this.id, // Made optional
    this.noteId,
    required this.value,
    this.units,
    required this.time,
    required this.metric,
  });

  factory DataPoint.fromJson(Map<String, dynamic> json) {
    return DataPoint(
      id: json[kId],
      noteId: json[kNoteId],
      value: (json[kValue] as num).toDouble(),
      units: json[kUnits],
      time: json[kTime],
      metric: MetricDetails.fromJson(json[kMetric]),
    );
  }

  DataPoint copy({
    int? id,
    int? noteId,
    double? value,
    String? units,
    int? time,
    MetricDetails? metric,
  }) {
    return DataPoint(
      id: id ?? this.id,
      noteId: noteId ?? this.noteId,
      value: value ?? this.value,
      units: units ?? this.units,
      time: time ?? this.time,
      metric: (metric ?? this.metric).copy(),
    );
  }
}

class TaskDetails implements Identifiable {
  @override
  final int? id;
  final String description;
  final String summary;
  final bool tagged;
  final List<String> tags;
  final OccurrenceSchedule? schedule;

  TaskDetails({
    required this.id,
    required this.description,
    required this.summary,
    required this.tagged,
    required this.tags,
    this.schedule,
  });

  factory TaskDetails.fromJson(Map<String, dynamic> json) {
    return TaskDetails(
      id: json[kId],
      description: json[kDescription],
      summary: json[kSummary],
      tagged: json[kTagged],
      tags: List<String>.from(json[kTags] ?? []),
      schedule: json[kSchedule] != null && (json[kSchedule] as Map).isNotEmpty
          ? OccurrenceSchedule.fromJson(json[kSchedule])
          : null,
    );
  }
}

class Occurrence implements Identifiable {
  @override
  final int? id;
  final int? noteId;
  final int priority;
  final bool completed;
  final int time;
  final TaskDetails task;

  Occurrence({
    required this.id,
    this.noteId,
    required this.priority,
    required this.completed,
    required this.time,
    required this.task,
  });

  factory Occurrence.fromJson(Map<String, dynamic> json) {
    return Occurrence(
      id: json[kId],
      noteId: json[kNoteId],
      priority: json[kPriority],
      completed: json[kCompleted],
      time: json[kTime],
      task: TaskDetails.fromJson(json[kTask]),
    );
  }
}

// --- Utility Models ---

class PresignedUrlResponse {
  final String url;
  final String key;
  final String contentType;

  PresignedUrlResponse({
    required this.url,
    required this.key,
    required this.contentType,
  });

  factory PresignedUrlResponse.fromJson(Map<String, dynamic> json) {
    return PresignedUrlResponse(
      url: json[kUrl],
      key: json[kKey],
      contentType: json[kContentType],
    );
  }
}