import json
import unittest
from backend.tests.integration.base import *

from backend.functions.task.index import handler
from backend.lib.util import get_user_ids_from_event

task_one_display_summary = 'display summary one'
task_two_display_summary = 'display summary two'
task_three_display_summary = 'display summary  three' + unique_piece
task_four_display_summary = 'display summary our'
task_five_display_summary = 'display summary five'

task_one_description = 'description for task one'
task_two_description = 'description for task two'
task_three_description = 'description for task three'
task_four_description = 'description for task four'
task_five_description = 'description for task five ' + unique_piece


class Test(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.event = baseSetUp(Trigger.http)

    def test_incomplete_post_returns_500(self):

        self.event[constants.body] = {
            constants.description: task_one_description,
        }

        self.event[constants.http_method] = constants.post
        result = handler(self.event, None)

        assert result[constants.status_code] == 500

        assert json.loads(result[constants.body])[constants.error] == constants.internal_server_error
        session = begin_session()

        try:
            assert len(get_tasks_by_description(task_one_description, session)) == 0
        finally:
            session.close()

    def test_task_post_fails_for_duplicate(self):

        self._setup_tasks()
        session = begin_session()

        try:

            self.event[constants.body] = {
                constants.summary: task_two_display_summary,
                constants.description: task_two_description + unique_piece,
            }
            self.event[constants.http_method] = constants.post
            result = handler(self.event, None)

            assert result[constants.status_code] == 500


        finally:
            session.close()



    def test_link_post_succeeds_for_duplicate_from_another_user(self):

         self._setup_tasks()
         session = begin_session()

         try:
             malicious_event = prepare_http_event(get_user_by_id(malicious_user_id, session).external_id)
             malicious_event[constants.body] = {
                 constants.summary: task_two_display_summary,
                 constants.description: task_two_description + unique_piece,
             }
             malicious_event[constants.http_method] = constants.post
             result = handler(malicious_event, None)

             assert result[constants.status_code] == 201
             session = refresh_cache(session)
             assert len(get_tasks_by_display_summary(task_two_display_summary, session)) == 2
             tasks = get_tasks_by_description(task_two_description + unique_piece, session)
             assert len(tasks) == 1
             task = tasks[0]
             assert not task.tagged

         finally:
             session.close()


    def test_task_post_succeeds(self):

        self.event[constants.body] = {
            constants.summary: task_one_display_summary,
            constants.description: task_one_description,
            constants.tags: [tag_two_display_name, tag_three_display_name]
        }

        self.event[constants.http_method] = constants.post

        result = handler(self.event, None)
        assert result[constants.status_code] == 201
        assert json.loads(result[constants.body])[constants.id] is not None

        session = begin_session()

        try:

            tasks = get_tasks_by_description(task_one_description, session)
            assert len(tasks) == 1

            task = tasks[0]

            user_id, external_id = get_user_ids_from_event(self.event, session)

            # make sure task is correct
            assert user_id == task.user_id
            assert task.tagged
            assert len(task.tags) == 2
            assert task.user.external_id == external_id



        finally:
            session.close()

    def test_task_patch_succeeds(self):
        self._setup_tasks()

        session = begin_session()

        try:

            tasks = get_tasks_by_description(task_one_description, session)

            assert len(tasks) == 1
            task = tasks[0]

            assert task.display_summary == task_one_display_summary
            assert len(task.tags) == 2

            old_tag_names = [tag.display_name for tag in task.tags]
            assert tag_one_display_name in old_tag_names
            assert tag_two_display_name in old_tag_names
            task_id = task.id

            new_tag_name = 'new_tag'
            self.event[constants.body] = {
                constants.summary: task_two_display_summary + unique_piece,
                constants.description: task_two_description,
                #  one exists and one new, both should replace old ones
                constants.tags: [new_tag_name, tag_three_display_name]
            }
            self.event[constants.path_params][constants.id] = task_id
            self.event[constants.http_method] = constants.patch
            result = handler(self.event, None)

            assert result[constants.status_code] == 204

            # new cache bc sqlalchemy
            session = refresh_cache(session)

            # make sure it didn't insert ore metrics
            task = get_task_by_id(task_id, session)

            # but with updated fields
            assert task.display_summary == task_two_display_summary + unique_piece
            assert task.description == task_two_description
            assert task.tagged
            assert len(task.tags) == 2

            new_tag_names = [tag.display_name for tag in task.tags]
            assert new_tag_name in new_tag_names
            assert tag_three_display_name in new_tag_names

            #  make sure new tag was added and old tags were
            assert session.query(Tag).count() == 4

            # just in case
            assert session.query(User).count() == 2

        finally:
            session.close()

    def test_task_patch_fails_for_malicious_user(self):

        self._setup_tasks()
        session = begin_session()

        try:

            tasks = get_tasks_by_description(task_one_description, session)

            assert len(tasks) == 1
            task = tasks[0]

            assert task.display_summary == task_one_display_summary

            task_id = task.id

            malicious_event = prepare_http_event(get_user_by_id(malicious_user_id, session).external_id)
            malicious_event[constants.body] = {
                constants.summary: task_two_display_summary,
                constants.description: task_two_description,
            }
            malicious_event[constants.path_params][constants.id] = task_id
            malicious_event[constants.http_method] = constants.patch
            result = handler(malicious_event, None)

            assert result[constants.status_code] == 400

            # new cache bc sqlalchemy
            session = refresh_cache(session)

            task = get_task_by_id(task_id, session)

            # but with updated fields
            assert task.display_summary == task_one_display_summary
            assert task.description == task_one_description

            # just in case
            assert session.query(User).count() == 2

        finally:
            session.close()


    def test_task_get_by_task_id_succeeds(self):

        self._setup_tasks()

        session = begin_session()
        try:
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
            assert len(items) == 5 # all of them

        finally:
            session.close()

    def test_task_get_by_task_id_fails_for_malicious_user(self):

        self._setup_tasks()

        session = begin_session()

        try:
            malicious_event = prepare_http_event(get_user_by_id(malicious_user_id, session).external_id)
            malicious_event[constants.http_method] = constants.get

            malicious_event[constants.path_params][constants.id] = 1
            result = handler(malicious_event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 0

            malicious_event[constants.query_params] = {}
            malicious_event[constants.path_params] = {}

            result = handler(malicious_event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 0

        finally:
            session.close()


    def test_task_get_by_tags_display_names_succeeds(self):

        self._setup_tasks()

        session = begin_session()

        try:
            self.event[constants.http_method] = constants.get

            ##########################################
            self.event[constants.query_params] = {
                constants.tags: f'{tag_two_display_name}',

            }
            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 4

            ##########################################
            self.event[constants.query_params] = {
                constants.tags: f'{tag_three_display_name}|{tag_one_display_name}',

            }
            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 5

            ###############################################
            # pagination
            ##############################################

            # offset defaults to 0 and limit to 100 so all 5 return
            self.event[constants.query_params] = {

            }
            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            assert len(json.loads(result[constants.body])) == 5

            # offset defaults to 0, limit 4 so 4 return
            self.event[constants.query_params] = {
                constants.limit: 4,

            }

            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            assert len(json.loads(result[constants.body])) == 4

            # offset defaults 4, limit 100 abd we only have 5 left so 1 will return
            self.event[constants.query_params] = {
                constants.offset: 4,

            }

            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            assert len(json.loads(result[constants.body])) == 1

            assert session.query(Task).count() == 5

        finally:
            session.close()

    def test_task_get_by_tags_display_names_fails_for_malicious_user(self):

        self._setup_tasks()

        session = begin_session()

        try:
            malicious_event = prepare_http_event(get_user_by_id(malicious_user_id, session).external_id)
            malicious_event[constants.http_method] = constants.get

            ##########################################
            malicious_event[constants.query_params] = {
                constants.tags: f'{tag_two_display_name}',

            }
            result = handler(malicious_event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 0

            ##########################################
            malicious_event[constants.query_params] = {
                constants.tags: f'{tag_three_display_name}|{tag_one_display_name}',
            }
            result = handler(malicious_event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 0

        finally:
            session.close()

    def test_task_get_by_display_summary_and_description_succeeds(self):

        self._setup_tasks()

        session = begin_session()

        try:
            self.event[constants.http_method] = constants.get
            self.event[constants.query_params] = {
                constants.text: 'one',

            }
            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 1
            prev_task_id = items[0][constants.id]

            self.event[constants.query_params] = {
                constants.text: unique_piece,
            }

            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 2  # in display_summary and description
            this_task_id = items[0][constants.id]

            assert prev_task_id != this_task_id

        finally:
            session.close()

    def test_task_get_by_description_fails_for_malicious_user(self):
        self._setup_tasks()

        session = begin_session()

        try:
            malicious_event = prepare_http_event(get_user_by_id(malicious_user_id, session).external_id)
            malicious_event[constants.http_method] = constants.get
            malicious_event[constants.query_params] = {
                constants.text: task_one_description,
            }
            result = handler(malicious_event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 0


        finally:
            session.close()

    def _setup_tasks(self):

        session = begin_session()
        try:
            user_id, external_user_id = get_user_ids_from_event(self.event, session)

            tag_one = Tag(user_id=user_id, name=tag_one_name, display_name=tag_one_display_name)
            tag_two = Tag(user_id=user_id, name=tag_two_name, display_name=tag_two_display_name)

            tag_three = Tag(user_id=user_id, name=tag_three_name, display_name=tag_three_display_name)

            user = session.query(User).get(user_id)

            assert user.external_id == external_user_id
            note = Note(user=user)
            session.add(note)
            session.flush()
            task_one = Task(note=note, user=user, summary=normalize_identifier(task_one_display_summary), display_summary=task_one_display_summary,
                            description=task_one_description, tagged=True,
                            tags=[tag_one, tag_two])
            task_two = Task(user=user, summary=normalize_identifier(task_two_display_summary), display_summary=task_two_display_summary, description=task_two_description,
                            tagged=True,
                            tags=[tag_one, tag_three])
            task_three = Task(note=note, user=user, summary=normalize_identifier(task_three_display_summary), display_summary=task_three_display_summary,
                              description=task_three_description, tagged=True,
                              tags=[tag_three, tag_two])
            task_four = Task(note=note, user=user, summary=normalize_identifier(task_four_display_summary), display_summary=task_four_display_summary,
                             description=task_four_description, tagged=True,
                             tags=[tag_two, tag_three])
            task_five = Task(user=user, summary=normalize_identifier(task_five_display_summary), display_summary=task_five_display_summary, description=task_five_description,
                             tagged=True,
                             tags=[tag_one, tag_two])
            session.add_all([note, task_one, task_two, task_three, task_four, task_five])
            session.commit()
        finally:
            session.close()

    def tearDown(self):
        baseTearDown()
