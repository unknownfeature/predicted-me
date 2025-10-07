import json
import unittest
from decimal import Decimal
from typing import Tuple

from backend.functions.occurance.index import handler
from backend.lib.db import Tag, Occurrence, Origin, \
    Note, OccurrenceSchedule
from backend.lib.util import get_user_ids_from_event
from backend.tests.integration.base import *

# test occurrence

task_one_display_summary = 'Some task with special characters, such as "%" 1'
task_one_summary = normalize_identifier(task_one_display_summary)
task_one_description = 'Some task with one description special characters, such as "%" 1'
task_two_display_summary = 'Some task with special characters, such as "%" 2 and a unique piece'
task_two_summary = normalize_identifier(task_two_display_summary)
task_two_description = 'Some task with two description special characters, such as "%" 2 and a unique piece'

schedule_priority = 4
schedule_recurrence = '1 * * * * *'

occurrence_priority_one = 1
occurrence_priority_two = 2
occurrence_priority_three = 3
occurrence_priority_four = 4
occurrence_priority_five = 5
occurrence_priority_six = 6

occurrence_one_completed = True
occurrence_two_completed = True
occurrence_three_completed = False
occurrence_four_completed = False
occurrence_five_completed = True
occurrence_six_completed = False

display_summary = 'Some human readable task with special characters, such as "%"'
description = 'Some human readable task description lalala  with special characters, such as "%"'
priority_one = 1
priority_two = 2
priority_three = 3

completed = True
other_completed = False
malicious_completed = False


class Test(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.event = baseSetUp(Trigger.http)

    def test_incomplete_occurrence_post_returns_500(self):

        self.event[constants.body] = {
            constants.completed: completed,
            constants.summary: display_summary,

        }

        self.event[constants.http_method] = constants.post
        result = handler(self.event, None)

        assert result[constants.status_code] == 500

        assert json.loads(result[constants.body])['error'] == 'Internal server error'
        session = begin_session()

        try:
            assert len(get_tasks_by_display_summary(display_summary, session)) == 0
        finally:
            session.close()

    def test_occurrence_post_succeeds(self):

        task_id, occurrence_id = self._setup_task(display_summary, priority=priority_one, completed=completed)

        session = begin_session()

        try:

            #  make sure name and display name are expected
            tasks = get_tasks_by_display_summary(display_summary, session)
            assert len(tasks) == 1

            task = tasks[0]

            user_id, external_id = get_user_ids_from_event(self.event, session)

            # make sure user is correct
            assert user_id == task.user_id
            assert task.user.external_id == external_id

            # lan of occurrence is correct
            assert len(task.occurrences) == 1

            occurrence = task.occurrences[0]

            assert occurrence.priority == Decimal(str(priority_one))
            assert occurrence.completed == completed
            assert occurrence.time > 0

            self.event[constants.body] = {
                constants.priority: priority_two,
                constants.completed: completed,
            }
            self.event[constants.path_params][constants.id] = task_id
            self.event[constants.http_method] = constants.post

            result = handler(self.event, None)

            assert result[constants.status_code] == 201
            assert json.loads(result[constants.body])[constants.id] is not None

            # new cache
            session = refresh_cache(session)

            # make sure it didn't insert ore tasks
            tasks = get_tasks_by_display_summary(display_summary, session)
            assert len(tasks) == 1

            task = tasks[0]

            # should add one more
            assert len(task.occurrences) == 2
            occurrence = task.occurrences[1]

            # and second occurrence point got saved
            assert occurrence.priority == priority_two
            assert occurrence.completed == completed
            assert occurrence.time > 0

        finally:
            session.close()

    def test_occurrence_post_fails_for_malicious_user(self):
        task_id, _ = self._setup_task(display_summary)

        name = normalize_identifier(display_summary)

        session = begin_session()

        try:

            malicious_event = prepare_http_event(get_user_by_id(malicious_user_id, session).external_id)
            malicious_event[constants.http_method] = constants.post
            malicious_event[constants.query_params] = {}
            malicious_event[constants.body] = {

                constants.value: priority_two,
                constants.completed: completed,
            }
            malicious_event[constants.path_params][constants.id] = task_id
            result = handler(malicious_event, None)

            assert result[constants.status_code] == 404

            session = refresh_cache(session)

            # make sure it didn't insert ore tasks
            tasks = get_tasks_by_display_summary(display_summary, session)
            assert len(tasks) == 1

            task = tasks[0]

            # should add one more
            assert len(task.occurrences) == 0

            # just in case
            assert session.query(User).count() == 2


        finally:
            session.close()

    def test_occurrence_patch_succeeds(self):

        task_id, occurrence_id = self._setup_task(display_summary, priority=priority_one, completed=completed)

        session = begin_session()

        try:
            #  make sure name and display name are expected
            tasks = get_tasks_by_display_summary(display_summary, session)

            task = tasks[0]
            # lan of occurrence is correct
            assert len(task.occurrences) == 1
            assert task.id == task_id

            occurrence = task.occurrences[0]

            assert occurrence.priority == priority_one
            assert occurrence.completed == completed
            assert occurrence.time > 0

            self.event[constants.body] = {
                constants.priority: priority_two,
                constants.completed: other_completed,
                constants.time: 25
            }
            self.event[constants.path_params][constants.id] = occurrence_id
            self.event[constants.http_method] = constants.patch
            result = handler(self.event, None)

            assert result[constants.status_code] == 204

            # new cache bc sqlalchemy
            session = refresh_cache(session)

            # make sure it didn't insert ore tasks
            tasks = get_tasks_by_display_summary(display_summary, session)
            assert len(tasks) == 1

            task = tasks[0]

            # should still be one
            assert len(task.occurrences) == 1
            occurrence = task.occurrences[0]

            # but with updated fields
            assert occurrence.priority == priority_two
            assert occurrence.completed == other_completed
            assert occurrence.time == 25
            assert occurrence.id == occurrence_id

            # just in case
            assert session.query(User).count() == 2

        finally:
            session.close()

    def test_occurrence_patch_fails_for_malicious_user(self):

        task_id, occurrence_id = self._setup_task(display_summary, priority=priority_one, completed=completed)

        session = begin_session()

        try:

            malicious_event = prepare_http_event(get_user_by_id(malicious_user_id, session).external_id)
            malicious_event[constants.http_method] = constants.patch
            malicious_event[constants.query_params] = {}
            malicious_event[constants.body] = {

                constants.value: priority_three,
                constants.completed: malicious_completed,
            }
            malicious_event[constants.path_params][constants.id] = occurrence_id
            result = handler(malicious_event, None)

            assert result[constants.status_code] == 404

            # make sure new occurrence wans't added for the malicious user
            session = refresh_cache(session)

            # make sure it didn't insert ore tasks
            tasks = get_tasks_by_display_summary(display_summary, session)
            assert len(tasks) == 1

            task = tasks[0]
            assert len(task.occurrences) == 1

            occurrence = task.occurrences[0]

            # should be old values
            assert occurrence.priority == priority_one
            assert occurrence.completed == completed

            # just in case
            assert session.query(User).count() == 2


        finally:
            session.close()

    def test_occurrence_delete_succeeds(self):

        _, occurrence_id = self._setup_task(display_summary, priority=priority_one, completed=completed)

        session = begin_session()

        try:

            self.event = prepare_http_event(get_user_by_id(legit_user_id, session).external_id)
            self.event[constants.body] = {}
            self.event[constants.path_params][constants.id] = occurrence_id
            self.event[constants.http_method] = constants.delete
            result = handler(self.event, None)

            assert result[constants.status_code] == 204

            # new cache
            session = refresh_cache(session)

            # make sure it didn't insert ore tasks
            tasks = get_tasks_by_display_summary(display_summary, session)
            assert len(tasks) == 1

            task = tasks[0]

            # should be 0
            assert len(task.occurrences) == 0


        finally:
            session.close()

    def test_occurrence_delete_fails_for_malicious_user(self):

        _, occurrence_id = self._setup_task(display_summary, priority=priority_one, completed=completed)

        session = begin_session()

        try:
            malicious_event = prepare_http_event(get_user_by_id(malicious_user_id, session).external_id)
            malicious_event[constants.http_method] = constants.delete
            malicious_event[constants.query_params] = {}
            malicious_event[constants.body] = {}
            malicious_event[constants.path_params][constants.id] = 1
            result = handler(malicious_event, None)

            assert result[constants.status_code] == 404

            session = refresh_cache(session)

            #  make sure name and display name are expected
            tasks = get_tasks_by_display_summary(display_summary, session)

            task = tasks[0]
            # lan of occurrence is correct bc it wasn't deleted
            assert len(task.occurrences) == 1

            occurrence = task.occurrences[0]

            assert occurrence.priority == priority_one
            assert occurrence.completed == completed
            assert occurrence.time > 0

        finally:
            session.close()

    def test_occurrence_get_by_occurrence_id_succeeds(self):

        session = begin_session()
        try:
            self._setup_occurrences_for_search(session)
            self.event[constants.http_method] = constants.get

            self.event[constants.path_params][constants.id] = 1
            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 1
            assert items[0][constants.id] == 1

            self.event[constants.query_params] = {}
            self.event[constants.path_params] = {}
            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 2

        finally:
            session.close()

    def test_occurrence_get_by_occurrence_id_fails_for_malicious_user(self):

        session = begin_session()
        try:
            self._setup_occurrences_for_search(session)
            self.event[constants.http_method] = constants.get

            malicious_event = prepare_http_event(get_user_by_id(malicious_user_id, session).external_id)
            malicious_event[constants.http_method] = constants.get
            malicious_event[constants.query_params] = {}
            malicious_event[constants.path_params] = {}
            malicious_event[constants.path_params][constants.id] = 1
            result = handler(malicious_event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 0  # no items for this user


        finally:
            session.close()

    def test_occurrence_get_by_note_succeeds(self):
        session = begin_session()
        try:
            self._setup_occurrences_for_search(session)
            self.event[constants.http_method] = constants.get

            self.event[constants.query_params] = {
                constants.note_id: 1,
                # start and end will be  == now - 1 day which is outside for this particular occurrence point but it should be ignored
            }
            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 1
            assert items[0][constants.note_id] == 1
            assert items[0][constants.origin] == Origin.user.value

            self.event[constants.query_params] = {
            }
            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 2


        finally:
            session.close()

    def test_occurrence_get_by_completed_fails_for_malicious_user(self):
        session = begin_session()
        try:
            self._setup_occurrences_for_search(session)

            malicious_event = prepare_http_event(get_user_by_id(2, session).external_id)
            malicious_event[constants.http_method] = constants.get
            malicious_event[constants.query_params] = {
                constants.completed: True,
                constants.start: three_days_ago - seconds_in_day,
                constants.end: get_utc_timestamp()
            }
            malicious_event[constants.path_params] = {}

            result = handler(malicious_event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 0  # no items for this user
        finally:
            session.close()

    def test_occurrence_get_by_completed_succeeds(self):
        session = begin_session()
        try:
            self._setup_occurrences_for_search(session)
            self.event[constants.http_method] = constants.get

            self.event[constants.query_params] = {
                constants.completed: '1',
                constants.start: three_days_ago - seconds_in_day,
                constants.end: get_utc_timestamp()
            }
            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 3

            assert items[0][constants.priority] == occurrence_priority_five
            assert items[0][constants.completed]

            assert items[1][constants.priority] == occurrence_priority_two
            assert items[1][constants.completed]

            assert items[2][constants.priority] == occurrence_priority_one
            assert items[2][constants.completed]

            self.event[constants.query_params] = {
                constants.completed: '0',
                constants.start: three_days_ago - seconds_in_day,
                constants.end: get_utc_timestamp()
            }
            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            items = json.loads(result[constants.body])
            assert len(items) == 3

            assert items[0][constants.priority] == occurrence_priority_six
            assert not items[0][constants.completed]

            assert items[1][constants.priority] == occurrence_priority_four
            assert not items[1][constants.completed]

            assert items[2][constants.priority] == occurrence_priority_three
            assert not items[2][constants.completed]


        finally:
            session.close()

    def test_occurrence_get_by_note_fails_for_malicious_user(self):
        session = begin_session()
        try:
            self._setup_occurrences_for_search(session)

            malicious_event = prepare_http_event(get_user_by_id(2, session).external_id)
            malicious_event[constants.http_method] = constants.get
            malicious_event[constants.query_params] = {}
            malicious_event[constants.path_params] = {}
            malicious_event[constants.path_params][constants.id] = 1
            result = handler(malicious_event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 0  # no items for this user
        finally:
            session.close()

    def test_occurrence_get_by_tags_display_summaries_succeeds(self):

        session = begin_session()
        try:
            self._setup_occurrences_for_search(session)
            self.event[constants.http_method] = constants.get

            ##########################################
            self.event[constants.query_params] = {
                constants.tags: f'{tag_two_display_name}',
                constants.start: three_days_ago - seconds_in_day,
            }
            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 6

            ##########################################
            self.event[constants.query_params] = {
                constants.tags: f'{tag_three_display_name}|{tag_one_display_name}',
                constants.start: three_days_ago - seconds_in_day,
            }
            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 6

        finally:
            session.close()

    def test_occurrence_get_by_tags_display_summaries_fails_for_malicious_user(self):

        session = begin_session()
        try:
            self._setup_occurrences_for_search(session)
            malicious_event = prepare_http_event(get_user_by_id(2, session).external_id)
            malicious_event[constants.http_method] = constants.get
            malicious_event[constants.query_params] = {
                constants.tags: f'{tag_two_display_name}',
                constants.start: three_days_ago - seconds_in_day,
            }
            result = handler(malicious_event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 0
        finally:
            session.close()

    def test_occurrence_get_by_tasks_description_succeeds(self):

        session = begin_session()
        try:
            self._setup_occurrences_for_search(session)
            self.event[constants.http_method] = constants.get
            self.event[constants.query_params] = {
                constants.task: task_one_description,
                constants.start: three_days_ago - seconds_in_day,
            }
            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 6

            self.event[constants.query_params] = {
                constants.task: unique_piece,
                constants.start: three_days_ago - seconds_in_day,
            }
            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 3  # only 2nd task's occurrence

        finally:
            session.close()

    def test_occurrence_get_by_tasks_description_fails_for_malicious_user(self):
        session = begin_session()
        try:
            self._setup_occurrences_for_search(session)
            malicious_event = prepare_http_event(get_user_by_id(2, session).external_id)
            malicious_event[constants.http_method] = constants.get
            malicious_event[constants.query_params] = {
                constants.task: task_one_description,
                constants.start: three_days_ago - seconds_in_day
            }
            result = handler(malicious_event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 0
        finally:
            session.close()

    def test_occurrence_get_by_tasks_display_summary_succeeds(self):

        session = begin_session()
        try:
            self._setup_occurrences_for_search(session)
            self.event[constants.http_method] = constants.get
            self.event[constants.query_params] = {
                constants.task: task_one_display_summary,
                constants.start: three_days_ago - seconds_in_day,
            }
            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 6

            self.event[constants.query_params] = {
                constants.task: 'unique piece',
                constants.start: three_days_ago - seconds_in_day,
            }
            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 3  # only 2nd task's occurrence

        finally:
            session.close()

    def test_occurrence_get_by_tasks_display_summary_fails_for_malicious_user(self):
        session = begin_session()
        try:
            self._setup_occurrences_for_search(session)
            malicious_event = prepare_http_event(get_user_by_id(2, session).external_id)
            malicious_event[constants.http_method] = constants.get
            malicious_event[constants.query_params] = {
                constants.task: task_one_display_summary,
                constants.start: three_days_ago - seconds_in_day,
            }
            result = handler(malicious_event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 0
        finally:
            session.close()

    def test_occurrence_get_by_date_succeeds(self):
        session = begin_session()
        try:
            #  m1_d2 & m2_d5 3d |   m1_d1 2d |  m1_d3  1d | m2_d4 & m2_d6  now

            self._setup_occurrences_for_search(session)
            self.event[constants.http_method] = constants.get
            self.event[constants.query_params] = {
                constants.start: three_days_ago - seconds_in_day,
                constants.end: three_days_ago,
            }
            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 2

            assert items[0][constants.priority] == occurrence_priority_five
            assert items[1][constants.priority] == occurrence_priority_two
            
            assert items[0][constants.completed] == occurrence_five_completed
            assert items[1][constants.completed] == occurrence_two_completed

            assert items[0][constants.task][constants.summary] == task_two_display_summary
            assert items[1][constants.task][constants.summary] == task_one_display_summary

            assert items[0][constants.task][constants.schedule][constants.priority] == schedule_priority
            assert items[0][constants.task][constants.schedule][constants.recurrence_schedule] == schedule_recurrence

            assert len(items[0][constants.task][constants.tags]) == 2
            
            assert items[1][constants.task][constants.tags][0] == tag_one_display_name
            assert items[1][constants.task][constants.tags][1] == tag_two_display_name

            #############################################

            self.event[constants.query_params] = {}  # should default to now - 1d

            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 2

            assert items[0][constants.priority] == occurrence_priority_six
            assert items[1][constants.priority] == occurrence_priority_four
            assert items[0][constants.completed] == occurrence_six_completed
            assert items[1][constants.completed] == occurrence_four_completed
            
            assert items[0][constants.task][constants.summary] == task_two_display_summary
            assert items[1][constants.task][constants.summary] == task_two_display_summary

            #############################################
            self.event[constants.query_params] = {
                constants.start: two_days_ago,
            }

            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 3

            assert items[0][constants.completed] == occurrence_four_completed
            assert items[1][constants.completed] == occurrence_six_completed
            assert items[2][constants.completed] == occurrence_three_completed

            assert items[0][constants.priority] == occurrence_priority_six
            assert items[1][constants.priority] == occurrence_priority_four
            assert items[2][constants.priority] == occurrence_priority_three
            
            assert items[0][constants.task][constants.summary] == task_two_display_summary
            assert items[1][constants.task][constants.summary] == task_two_display_summary
            assert items[2][constants.task][constants.summary] == task_one_display_summary

            ##############################################
            self.event[constants.query_params] = {
                constants.end: two_days_ago,
            }
            result = handler(self.event, None)
            items = json.loads(result[constants.body])
            assert len(items) == 1

            assert items[0][constants.priority] == occurrence_priority_one
            assert items[0][constants.completed] == occurrence_one_completed
            
            assert items[0][constants.task][constants.summary] == task_one_display_summary

            assert session.query(Task).count() == 2
            assert session.query(Occurrence).count() == 6

        finally:
            session.close()

    def test_occurrence_get_by_date_fails_for_malicious_user(self):
        session = begin_session()
        try:
            #  m1_d2 & m2_d5 3d |   m1_d1 2d |  m1_d3  1d | m2_d4 & m2_d6  now

            self._setup_occurrences_for_search(session)

            malicious_event = prepare_http_event(get_user_by_id(2, session).external_id)
            malicious_event[constants.http_method] = constants.get
            malicious_event[constants.query_params] = {
                constants.start: three_days_ago - seconds_in_day,
                constants.end: get_utc_timestamp(),  #
            }
            malicious_event[constants.path_params] = {}
            result = handler(malicious_event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 0  # no items for this user
        finally:
            session.close()

    def _setup_task(self, display_summary: str, priority=None, completed=None) -> Tuple[int, int | None]:
        session = begin_session()

        try:
            user_id, external_user_id = get_user_ids_from_event(self.event, session)

            tag_one = Tag(name=tag_one_name, display_name=tag_one_display_name)
            tag_two = Tag(name=tag_two_name, display_name=tag_two_display_name)

            user = session.query(User).get(user_id)
            task_one = Task(display_summary=display_summary, summary=task_one_display_summary,
                            description=task_one_description, user=user,
                            tags=[tag_one, tag_two])

            if priority and completed:
                task_one.occurrences.append(Occurrence(priority=priority, completed=completed, origin=Origin.user))
            session.add(task_one)
            session.commit()

            if priority and completed:
                return task_one.id, task_one.occurrences[0].id
            return task_one.id, None

        finally:
            session.close()

    def _setup_occurrences_for_search(self, session):
        user_id, external_user_id = get_user_ids_from_event(self.event, session)

        tag_one = Tag(name=tag_one_name, display_name=tag_one_display_name)
        tag_two = Tag(name=tag_two_name, display_name=tag_two_display_name)

        tag_three = Tag(name=tag_three_name, display_name=tag_three_display_name)

        user = session.query(User).get(user_id)

        assert user.external_id == external_user_id
        note = Note(user=user)
        session.add(note)
        session.flush()

        task_one = Task(summary=task_one_summary, display_summary=task_one_display_summary,
                        description=task_one_description, user=user,
                        tags=[tag_one, tag_two])
        task_two = Task(summary=task_two_summary, display_summary=task_two_display_summary, user=user,
                        description=task_two_description,
                        tags=[tag_two, tag_three],
                        schedule=OccurrenceSchedule(priority=schedule_priority,
                                                    recurrence_schedule=schedule_recurrence))
        # m1_d2 & m2_d5 3d  m1_d1 2d  m1_d3  1d  m2_d4 & m2_d6  now

        task_one.occurrences.extend(
            [Occurrence(priority=occurrence_priority_one, completed=occurrence_one_completed, time=three_days_ago + 60,
                        origin=Origin.user),
             Occurrence(priority=occurrence_priority_two, completed=occurrence_two_completed, time=three_days_ago - 60,
                        origin=Origin.user),
             Occurrence(priority=occurrence_priority_three, completed=occurrence_three_completed,
                        time=two_days_ago + 60, origin=Origin.user, note=note), ])
        task_two.occurrences.extend(
            [Occurrence(priority=occurrence_priority_four, completed=occurrence_four_completed, time=day_ago + 60,
                        origin=Origin.user),
             Occurrence(priority=occurrence_priority_five, completed=occurrence_five_completed,
                        time=three_days_ago - 60, origin=Origin.user),
             Occurrence(priority=occurrence_priority_six, completed=occurrence_six_completed, time=day_ago + 60,
                        origin=Origin.user), ])
        session.add_all([note, task_one, task_two])
        session.commit()

    def tearDown(self):
        baseTearDown()

