import 'constants.dart';

// --- Base Models ---

class Tag {
  final int id;
  final String name;

  Tag({required this.id, required this.name});

  factory Tag.fromJson(Map<String, dynamic> json) {
    return Tag(
      id: json[kId],
      name: json[kName],
    );
  }
}

class User {
  final int id;
  final String? name;

  User({required this.id, this.name});

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json[kId],
      name: json[kName],
    );
  }
}

class Note {
  final int id;
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
    required this.id,
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
}

class Link {
  final int id;
  final int? noteId;
  final String url;
  final String summary;
  final String? description;
  final bool tagged;
  final int time;
  final List<String> tags;

  Link({
    required this.id,
    this.noteId,
    required this.url,
    required this.summary,
    this.description,
    required this.tagged,
    required this.time,
    required this.tags,
  });

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
}

class Task {
  final int id;
  final String summary;
  final String description;
  final List<String> tags;

  Task({
    required this.id,
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
}

class Metric {
  final int id;
  final String name;
  final List<String> tags;

  Metric({
    required this.id,
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
}

// --- Nested Schedule Models ---

abstract class BaseSchedule {
  final int id;
  final String? minute;
  final String? hour;
  final String? dayOfMonth;
  final String? month;
  final String? dayOfWeek;
  final int? periodSeconds;
  final int nextRun;

  BaseSchedule({
    required this.id,
    this.minute,
    this.hour,
    this.dayOfMonth,
    this.month,
    this.dayOfWeek,
    this.periodSeconds,
    required this.nextRun,
  });
}

class DataSchedule extends BaseSchedule {
  final double targetValue;
  final String? units;

  DataSchedule({
    required super.id,
    super.minute,
    super.hour,
    super.dayOfMonth,
    super.month,
    super.dayOfWeek,
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
}

class OccurrenceSchedule extends BaseSchedule {
  final int priority;

  OccurrenceSchedule({
    required super.id,
    super.minute,
    super.hour,
    super.dayOfMonth,
    super.month,
    super.dayOfWeek,
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
}

// --- Nested Response Models (from GET endpoints) ---

class MetricDetails {
  final int id;
  final String name;
  final bool tagged;
  final List<String> tags;
  final DataSchedule? schedule;

  MetricDetails({
    required this.id,
    required this.name,
    required this.tagged,
    required this.tags,
    this.schedule,
  });

  factory MetricDetails.fromJson(Map<String, dynamic> json) {
    return MetricDetails(
      id: json[kId],
      name: json[kName],
      tagged: json[kTagged],
      tags: List<String>.from(json[kTags] ?? []),
      schedule: json[kSchedule] != null && (json[kSchedule] as Map).isNotEmpty
          ? DataSchedule.fromJson(json[kSchedule])
          : null,
    );
  }
}

class DataPoint {
  final int id;
  final int? noteId;
  final double value;
  final String? units;
  final String origin;
  final int time;
  final MetricDetails metric;

  DataPoint({
    required this.id,
    this.noteId,
    required this.value,
    this.units,
    required this.origin,
    required this.time,
    required this.metric,
  });

  factory DataPoint.fromJson(Map<String, dynamic> json) {
    return DataPoint(
      id: json[kId],
      noteId: json[kNoteId],
      value: (json[kValue] as num).toDouble(),
      units: json[kUnits],
      origin: json[kOrigin],
      time: json[kTime],
      metric: MetricDetails.fromJson(json[kMetric]),
    );
  }
}

class TaskDetails {
  final int id;
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

class Occurrence {
  final int id;
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