import json
import unittest
from unittest.mock import patch

from backend.functions.note.index import handler
from backend.lib.db import Tag, Origin, DataSchedule, Data
from backend.lib.util import get_user_ids_from_event
from backend.tests.integration.base import *
from backend.tests.integration.functions.data import metric_one_name, metric_one_display_name, metric_two_name, \
    metric_two_display_name, schedule_target_value, schedule_units, data_one_value, data_two_value, data_three_value, \
    data_one_units, data_two_units, data_three_units, data_four_value, data_five_value, data_four_units, \
    data_five_units
from backend.tests.integration.functions.occurrence import schedule_recurrence

note_one_audio_key = 'one.mp4'
note_two_audio_key = 'two.mp4'
note_three_audio_key = 'three.mp4'

note_one_audio_text = 'one text mp4'
note_two_audio_text = 'two text mp4'
note_three_audio_text = 'three text mp4'

note_four_image_key = 'four.img'
note_five_image_key = 'five.img'

note_four_image_text = 'four image text img'
note_five_image_text = 'five image text img'

note_four_image_description = 'four image description img'
note_five_image_description = 'five image description img'

note_one_text = 'text for note one'
note_two_text = 'text for note two'
note_three_text = 'text for note three'
note_four_text = 'text for note four'
note_five_text = 'text for note five ' + unique_piece


class Test(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.event = baseSetUp(Trigger.http)

    def test_incomplete_post_returns_500(self):

        self.event[constants.body] = {

        }

        self.event[constants.http_method] = constants.post
        result = handler(self.event, None)

        assert result[constants.status_code] == 500

        assert json.loads(result[constants.body])[constants.error] == constants.any_text_is_required
        session = begin_session()

        try:
            assert len(get_notes_by_text(note_one_text, session)) == 0
        finally:
            session.close()

    @patch('backend.functions.note.index.send_text_to_sns')
    def test_note_post_succeeds(self, mock_send_text_to_sns):

        self.event[constants.body] = {
            constants.text: note_one_text,
            constants.audio_key: note_two_audio_key,
            constants.image_key: note_four_image_key,

        }

        self.event[constants.http_method] = constants.post

        result = handler(self.event, None)
        assert result[constants.status_code] == 201
        assert json.loads(result[constants.body])[constants.id] is not None
        mock_send_text_to_sns.assert_called_once_with(1)  # note id

        session = begin_session()

        try:

            notes = get_notes_by_text(note_one_text, session)
            assert len(notes) == 1

            note = notes[0]

            user_id, external_id = get_user_ids_from_event(self.event, session)

            # make sure user is correct
            assert user_id == note.user_id
            assert note.user.external_id == external_id


        finally:
            session.close()

    def test_note_get_by_id_succeeds(self):

        self._setup_notes()

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
            assert len(items) == 2

        finally:
            session.close()

    def test_note_get_by_id_fails_for_malicious_user(self):

        self._setup_notes()

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

    def test_note_get_by_metrcis_display_names_succeeds(self):
        self._setup_notes()

        session = begin_session()

        try:
            self.event[constants.http_method] = constants.get

            ##########################################
            self.event[constants.query_params] = {
                constants.metrics: f'{metric_one_display_name}',
                constants.start: three_days_ago - seconds_in_day,
                constants.end: get_utc_timestamp()
            }
            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 3

            assert items[0][constants.text] == note_three_text
            assert items[0][constants.audio_key] == note_three_audio_key
            assert items[0][constants.audio_text] == note_three_audio_text
            assert items[0][constants.audio_transcribed]
            assert items[0][constants.time] > 0

            assert items[1][constants.text] == note_one_text
            assert items[1][constants.audio_key] == note_one_audio_key
            assert items[1][constants.audio_text] == note_one_audio_text
            assert items[1][constants.audio_transcribed]
            assert items[1][constants.time] > 0

            assert items[2][constants.text] == note_two_text
            assert items[2][constants.audio_key] == note_two_audio_key
            assert items[2][constants.audio_text] == note_two_audio_text
            assert items[2][constants.audio_transcribed]
            assert items[2][constants.time] > 0

            ##########################################
            self.event[constants.query_params] = {
                constants.metrics: f'{metric_two_display_name}|{metric_one_display_name}',
                constants.start: three_days_ago - seconds_in_day,
                constants.end: get_utc_timestamp()
            }
            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 5

        finally:
            session.close()

    def test_note_get_by_metrics_display_names_fails_for_malicious_user(self):

        self._setup_notes()

        session = begin_session()

        try:
            malicious_event = prepare_http_event(get_user_by_id(malicious_user_id, session).external_id)
            malicious_event[constants.http_method] = constants.get

            ##########################################
            malicious_event[constants.query_params] = {
                constants.metrics: f'{metric_one_display_name}',
                constants.start: three_days_ago - seconds_in_day,
                constants.end: get_utc_timestamp()
            }
            result = handler(malicious_event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 0



        finally:
            session.close()

    def test_note_get_by_tags_display_names_succeeds(self):

        self._setup_notes()

        session = begin_session()

        try:
            self.event[constants.http_method] = constants.get

            ##########################################
            self.event[constants.query_params] = {
                constants.tags: f'{tag_two_display_name}',
                constants.start: three_days_ago - seconds_in_day,
                constants.end: get_utc_timestamp()
            }
            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 5

            ##########################################
            self.event[constants.query_params] = {
                constants.tags: f'{tag_three_display_name}|{tag_one_display_name}',
                constants.start: three_days_ago - seconds_in_day,
                constants.end: get_utc_timestamp()
            }
            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 5

        finally:
            session.close()

    def test_note_get_by_tags_display_names_fails_for_malicious_user(self):

        self._setup_notes()

        session = begin_session()

        try:
            malicious_event = prepare_http_event(get_user_by_id(malicious_user_id, session).external_id)
            malicious_event[constants.http_method] = constants.get

            ##########################################
            malicious_event[constants.query_params] = {
                constants.tags: f'{tag_two_display_name}',
                constants.start: three_days_ago - seconds_in_day,
                constants.end: get_utc_timestamp()
            }
            result = handler(malicious_event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 0

            ##########################################
            malicious_event[constants.query_params] = {
                constants.tags: f'{tag_three_display_name}|{tag_one_display_name}',
                constants.start: three_days_ago - seconds_in_day,
                constants.end: get_utc_timestamp()
            }
            result = handler(malicious_event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 0

        finally:
            session.close()

    def test_note_get_text_succeeds(self):

        self._setup_notes()

        session = begin_session()

        try:
            self.event[constants.http_method] = constants.get
            self.event[constants.query_params] = {
                constants.text: 'one',
                constants.start: three_days_ago - seconds_in_day,
                constants.end: get_utc_timestamp(),

            }
            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 1
            prev_note_id = items[0][constants.id]

            self.event[constants.query_params] = {
                constants.text: unique_piece,
                constants.start: three_days_ago - seconds_in_day,
                constants.end: get_utc_timestamp(),
            }

            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 1  # in url and description
            this_note_id = items[0][constants.id]

            assert prev_note_id != this_note_id

        finally:
            session.close()

    def test_note_get_by_text_fails_for_malicious_user(self):
        self._setup_notes()

        session = begin_session()

        try:
            malicious_event = prepare_http_event(get_user_by_id(malicious_user_id, session).external_id)
            malicious_event[constants.http_method] = constants.get
            malicious_event[constants.query_params] = {
                constants.text: note_one_text,
                constants.start: three_days_ago - seconds_in_day,
            }
            result = handler(malicious_event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 0


        finally:
            session.close()

    def test_notes_get_by_date_succeeds(self):

        self._setup_notes()
        session = begin_session()
        try:
            self.event[constants.http_method] = constants.get
            self.event[constants.query_params] = {
                constants.start: three_days_ago - seconds_in_day,
                constants.end: three_days_ago,
            }
            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 0

            #############################################

            self.event[constants.query_params] = {}  # should default to now - 1d

            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 2

            assert items[0][constants.text] == note_three_text
            assert items[0][constants.audio_key] == note_three_audio_key
            assert items[0][constants.audio_text] == note_three_audio_text
            assert items[0][constants.audio_transcribed]
            assert items[0][constants.time] > 0

            assert items[1][constants.text] == note_four_text
            assert items[1][constants.image_key] == note_four_image_key
            assert items[1][constants.image_description] == note_four_image_description
            assert items[1][constants.image_text] == note_four_image_text
            assert items[1][constants.image_described]
            assert items[1][constants.time] > 0

            #############################################
            self.event[constants.query_params] = {
                constants.start: two_days_ago,
            }

            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 3

            assert items[0][constants.text] == note_three_text
            assert items[0][constants.audio_key] == note_three_audio_key
            assert items[0][constants.audio_text] == note_three_audio_text
            assert items[0][constants.audio_transcribed]
            assert items[0][constants.time] > 0

            assert items[1][constants.text] == note_four_text
            assert items[1][constants.image_key] == note_four_image_key
            assert items[1][constants.image_description] == note_four_image_description
            assert items[1][constants.image_text] == note_four_image_text
            assert items[1][constants.image_described]
            assert items[1][constants.time] > 0

            assert items[2][constants.text] == note_five_text
            assert items[2][constants.image_key] == note_five_image_key
            assert items[2][constants.image_description] == note_five_image_description
            assert items[2][constants.image_text] == note_five_image_text
            assert items[2][constants.image_described]
            assert items[2][constants.time] > 0

            ##############################################

            self.event[constants.query_params] = {
                constants.end: two_days_ago,
            }
            result = handler(self.event, None)
            items = json.loads(result[constants.body])
            assert len(items) == 2

            assert items[0][constants.text] == note_one_text
            assert items[0][constants.audio_key] == note_one_audio_key
            assert items[0][constants.audio_text] == note_one_audio_text
            assert items[0][constants.audio_transcribed]
            assert items[0][constants.time] > 0

            assert items[1][constants.text] == note_two_text
            assert items[1][constants.audio_key] == note_two_audio_key
            assert items[1][constants.audio_text] == note_two_audio_text
            assert items[1][constants.audio_transcribed]
            assert items[1][constants.time] > 0
            ###############################################
            # pagination
            ##############################################

            # offset defaults to 0 and limit to 100 so all 5 return
            self.event[constants.query_params] = {
                constants.start: three_days_ago - seconds_in_day,
                constants.end: get_utc_timestamp(),

            }
            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            assert len(json.loads(result[constants.body])) == 5

            # offset defaults to 0, limit 4 so 4 return
            self.event[constants.query_params] = {
                constants.start: three_days_ago - seconds_in_day,
                constants.end: get_utc_timestamp(),
                constants.limit: 4,

            }

            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            assert len(json.loads(result[constants.body])) == 4

            # offset defaults 4, limit 100 abd we only have 5 left so 1 will return
            self.event[constants.query_params] = {
                constants.start: three_days_ago - seconds_in_day,
                constants.end: get_utc_timestamp(),
                constants.offset: 4,

            }

            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            assert len(json.loads(result[constants.body])) == 1

            assert session.query(Note).count() == 5

        finally:
            session.close()

    def test_notes_get_by_date_fails_for_malicious_user(self):

        self._setup_notes()
        session = begin_session()
        try:

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

    def _setup_notes(self):

        session = begin_session()
        try:
            user_id, external_user_id = get_user_ids_from_event(self.event, session)

            tag_one = Tag(user_id=user_id, name=tag_one_name, display_name=tag_one_display_name)
            tag_two = Tag(user_id=user_id, name=tag_two_name, display_name=tag_two_display_name)

            tag_three = Tag(user_id=user_id, name=tag_three_name, display_name=tag_three_display_name)

            user = session.query(User).get(user_id)

            assert user.external_id == external_user_id

            note_one = Note(text=note_one_text, user=user, audio_key=note_one_audio_key, audio_text=note_one_audio_text,
                            audio_transcribed=True, time=two_days_ago - 60)
            note_two = Note(text=note_two_text, user=user, audio_key=note_two_audio_key, audio_text=note_two_audio_text,
                            audio_transcribed=True, time=three_days_ago + 60)
            note_three = Note(text=note_three_text, user=user, audio_key=note_three_audio_key,
                              audio_text=note_three_audio_text,
                              audio_transcribed=True, time=get_utc_timestamp())

            note_four = Note(text=note_four_text, user=user, image_key=note_four_image_key,
                             image_text=note_four_image_text, image_description=note_four_image_description,
                             image_described=True, time=get_utc_timestamp() - 60)
            note_five = Note(text=note_five_text, user=user, image_key=note_five_image_key,
                             image_text=note_five_image_text, image_description=note_five_image_description,
                             image_described=True, time=day_ago - 60)

            metric_one = Metric(name=metric_one_name, display_name=metric_one_display_name, user=user,
                                tagged=True,
                                tags=[tag_one, tag_two])
            metric_two = Metric(name=metric_two_name, display_name=metric_two_display_name, user=user,
                                tags=[tag_two, tag_three],
                                tagged=True,
                                schedule=DataSchedule(target_value=schedule_target_value, units=schedule_units,
                                                      recurrence_schedule=schedule_recurrence))

            metric_one.data_points.extend(
                [Data(value=data_one_value, units=data_one_units, time=three_days_ago + 60, origin=Origin.audio_text,
                      note=note_one, ),
                 Data(value=data_two_value, units=data_two_units, time=three_days_ago - 60, origin=Origin.text,
                      note=note_two, ),
                 Data(value=data_three_value, units=data_three_units,
                      time=two_days_ago + 60, origin=Origin.text, note=note_three, ), ])
            metric_two.data_points.extend(
                [Data(value=data_four_value, units=data_four_units, time=day_ago + 60, origin=Origin.img_desc,
                      note=note_four, ),
                 Data(value=data_five_value, units=data_five_units, time=three_days_ago - 60, origin=Origin.img_text,
                      note=note_five, ), ])

            session.add_all([note_one, note_two, note_three, note_four, note_five, metric_one, metric_two])
            session.commit()
        finally:
            session.close()

    def tearDown(self):
        baseTearDown()
