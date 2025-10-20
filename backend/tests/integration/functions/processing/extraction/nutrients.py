from backend.tests.integration.base import *
import json
import unittest
from decimal import Decimal

from sqlalchemy import select, and_

from backend.functions.processing.extraction.nutrients.index import (
    text_supplier, get_user_id, on_response_from_model, get_or_create_tag,
    process_nutrient, process_ingredient, normalize_value_and_units
)
from backend.tests.integration.base import *
from backend.lib.db import (
    Metric, Data, Tag, Note, User, get_utc_timestamp, AggregationFunction, seconds_in_day
)
from backend.lib.func.sqs import MessageInput
from shared import constants

metric_one_display_name = '1 banana'
metric_two_display_name = '1 protein bar'
metric_one_name = normalize_identifier(metric_one_display_name)
metric_two_name = normalize_identifier(metric_two_display_name)

nutrient_tag_name = 'Nutrient'
ingredient_tag_name = 'Ingredient'

mock_llm_output = [
    {
        constants.id: 1,
        constants.nutrients: [
            {constants.name: 'Calories', constants.value: 105, constants.units: 'kcal'},
            {constants.name: 'Protein', constants.value: 1.3, constants.units: 'g'}
        ],
        constants.ingredients: []
    },
    {
        constants.id: 2,
        constants.nutrients: [
            {constants.name: 'Calories', constants.value: 200, constants.units: 'kcal'},
            {constants.name: 'Protein', constants.value: 20, constants.units: 'g'}
        ],
        constants.ingredients: ['Whey Protein', 'Oats', 'Honey']
    }
]


class Test(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.event = baseSetUp(Trigger.http)

    def tearDown(self):
        baseTearDown()

    def _setup_data(self, tagged=False):
        session = begin_session()
        try:
            user = session.get(User, legit_user_id)
            note = Note(user=user)
            session.add(note)
            session.commit()

            metric_one = Metric(tagged=tagged, user=user, display_name=metric_one_display_name,
                                name=metric_one_name)
            metric_two = Metric(tagged=tagged, user=user, display_name=metric_two_display_name,
                                name=metric_two_name)

            data_one = Data(value=1, note=note, metric=metric_one, time=get_utc_timestamp())
            data_two = Data(value=1, note=note, metric=metric_two, time=get_utc_timestamp())

            session.add_all([metric_one, metric_two, data_one, data_two])
            session.commit()
            return note.id
        finally:
            session.close()

    def test_text_supplier_by_note_id_succeeds(self):
        note_id = self._setup_data()
        session = begin_session()
        try:
            text = text_supplier(session, MessageInput(note_id=note_id))
            results = json.loads(text)

            assert len(results) == 2
            assert results[0][constants.id] == 1
            assert results[0][constants.name] == metric_one_display_name
            assert results[1][constants.id] == 2
            assert results[1][constants.name] == metric_two_display_name
        finally:
            session.close()

    def test_text_supplier_by_data_id_succeeds(self):
        self._setup_data()
        session = begin_session()
        try:
            text = text_supplier(session, MessageInput(data_id=1))
            results = json.loads(text)
            assert len(results) == 1
            assert results[0][constants.id] == 1
            assert results[0][constants.name] == metric_one_display_name
        finally:
            session.close()

    def test_text_supplier_returns_none_if_tagged(self):
        self._setup_data(tagged=True)
        session = begin_session()
        try:
            text_note = text_supplier(session, MessageInput(note_id=1))
            assert text_note is None

            text_data = text_supplier(session, MessageInput(data_id=1))
            assert text_data is None
        finally:
            session.close()

    def test_text_supplier_returns_none_if_no_data(self):
        session = begin_session()
        try:
            text = text_supplier(session, MessageInput(note_id=999))
            assert text is None
        finally:
            session.close()

    def test_get_user_id_by_note_id(self):
        note_id = self._setup_data()
        session = begin_session()
        try:
            user_id = get_user_id(session, MessageInput(note_id=note_id))
            assert user_id == legit_user_id
        finally:
            session.close()

    def test_get_user_id_by_data_id(self):
        self._setup_data()
        session = begin_session()
        try:
            user_id = get_user_id(session, MessageInput(data_id=1))
            assert user_id == legit_user_id
        finally:
            session.close()

    def test_get_user_id_fails_on_empty_input(self):
        session = begin_session()
        try:
            with self.assertRaises(ValueError):
                get_user_id(session, MessageInput())
        finally:
            session.close()

    def test_on_response_from_model_succeeds_by_note_id(self):
        note_id = self._setup_data()
        session = begin_session()
        try:
            on_response_from_model(session, MessageInput(note_id=note_id), mock_llm_output)
            session = refresh_cache(session)

            calories_metric = get_metrics_by_name("calories", session)[0]
            protein_metric = get_metrics_by_name("protein", session)[0]

            assert calories_metric.tagged
            assert calories_metric.tags[0].display_name == nutrient_tag_name

            banana_calories_data = session.scalars(
                select(Data).where(and_(Data.metric_id == calories_metric.id, Data.parent_data_id == 1))
            ).one()
            assert banana_calories_data.value == 105

            bar_protein_data = session.scalars(
                select(Data).where(and_(Data.metric_id == protein_metric.id, Data.parent_data_id == 2))
            ).one()
            assert bar_protein_data.value == 20

            whey_metric = get_metrics_by_name("whey_protein", session)[0]
            assert whey_metric.tagged
            assert whey_metric.tags[0].display_name == ingredient_tag_name

            whey_data = whey_metric.data_points[0]
            assert whey_data.value == 1
            assert whey_data.parent_data_id == 2

            all_tags = session.scalars(select(Tag)).all()
            assert len(all_tags) == 2
            tag_names = {t.display_name for t in all_tags}
            assert nutrient_tag_name in tag_names
            assert ingredient_tag_name in tag_names

        finally:
            session.close()

    def test_on_response_from_model_succeeds_by_data_id(self):
        self._setup_data()
        session = begin_session()
        try:
            banana_llm_output = [mock_llm_output[0]]

            on_response_from_model(session, MessageInput(data_id=1), banana_llm_output)
            session = refresh_cache(session)

            calories_metric = get_metrics_by_name("calories", session)[0]
            assert calories_metric.tagged
            assert len(calories_metric.data_points) == 1

            calories_data_banana = calories_metric.data_points[0]
            assert calories_data_banana.value == 105
            assert calories_data_banana.parent_data_id == 1

            whey_metric = get_metrics_by_name("whey_protein", session)
            assert len(whey_metric) == 0

        finally:
            session.close()

    def test_process_nutrient_sets_default_fields(self):
        self._setup_data()
        session = begin_session()
        try:
            nutrient_data = {constants.name: 'Test Vitamin', constants.value: 50, constants.units: 'mg'}
            nutrient_tag = get_or_create_tag(constants.nutrient_tag, session, legit_user_id)

            process_nutrient(1, nutrient_data, nutrient_tag, session, legit_user_id)
            session.commit()
            session = refresh_cache(session)

            vitamin_metric = get_metrics_by_name("test_vitamin", session)[0]
            assert vitamin_metric is not None
            assert vitamin_metric.tagged
            assert vitamin_metric.tags[0].display_name == constants.nutrient_tag
            assert vitamin_metric.data_points[0].value == 50
            assert vitamin_metric.data_points[0].parent_data_id == 1

            assert vitamin_metric.default_units == 'mg'
            assert vitamin_metric.default_aggregator_function == AggregationFunction.sum
            assert vitamin_metric.default_aggregation_period_seconds == seconds_in_day

        finally:
            session.close()

    def test_process_ingredient_sets_default_fields(self):
        self._setup_data()
        session = begin_session()
        try:
            ingredient_data = "Test Ingredient"
            ingredient_tag = get_or_create_tag(constants.ingredient_tag, session, legit_user_id)

            process_ingredient(1, ingredient_data, ingredient_tag, session, legit_user_id)
            session.commit()
            session = refresh_cache(session)

            ingredient_metric = get_metrics_by_name("test_ingredient", session)[0]
            assert ingredient_metric is not None
            assert ingredient_metric.tagged
            assert ingredient_metric.tags[0].display_name == constants.ingredient_tag
            assert ingredient_metric.data_points[0].value == 1
            assert ingredient_metric.data_points[0].parent_data_id == 1

            assert ingredient_metric.default_units == 'item'
            assert ingredient_metric.default_aggregator_function == AggregationFunction.count
            assert ingredient_metric.default_aggregation_period_seconds == seconds_in_day
        finally:
            session.close()

    def test_process_nutrient_does_not_overwrite_existing_defaults(self):
        self._setup_data()
        session = begin_session()
        try:
            # Create a metric with pre-existing defaults
            metric_name = "calories"
            metric = Metric(
                name=metric_name,
                display_name="Calories",
                user_id=legit_user_id,
                default_units="kcal_test",
                default_aggregator_function=AggregationFunction.avg,
                default_aggregation_period_seconds=3600
            )
            session.add(metric)
            session.commit()

            nutrient_data = {constants.name: 'Calories', constants.value: 150, constants.units: 'kcal'}
            nutrient_tag = get_or_create_tag(constants.nutrient_tag, session, legit_user_id)

            process_nutrient(1, nutrient_data, nutrient_tag, session, legit_user_id)
            session.commit()
            session = refresh_cache(session)

            calories_metric = get_metrics_by_name(metric_name, session)[0]
            assert calories_metric.default_units == 'kcal_test'
            assert calories_metric.default_aggregator_function == AggregationFunction.avg
            assert calories_metric.default_aggregation_period_seconds == 3600

        finally:
            session.close()

    def test_normalize_value_and_units_converts_vitamin_d(self):
        value, units = normalize_value_and_units(100.0, "Vitamin D", "IU")
        assert value == Decimal('2.5')
        assert units == 'mcg'

    def test_normalize_value_and_units_converts_vitamin_a(self):
        value, units = normalize_value_and_units(1000.0, "Vitamin A", "IU")
        assert value == Decimal('300.0')
        assert units == 'mcg'

    def test_normalize_value_and_units_converts_vitamin_e(self):
        value, units = normalize_value_and_units(100.0, "Vitamin E", "IU")
        assert value == Decimal('67.00')
        assert units == 'mg'

    def test_normalize_value_and_units_handles_case_and_spacing(self):
        value, units = normalize_value_and_units(100.0, "vitamin_d_supplement", " iu ")
        assert value == Decimal('2.5')
        assert units == 'mcg'

    def test_normalize_value_and_units_ignores_unknown_iu(self):
        value, units = normalize_value_and_units(50.0, "Vitamin K", "IU")
        assert value == Decimal('50.0')
        assert units == 'IU'

    def test_normalize_value_and_units_ignores_non_iu_units(self):
        value, units = normalize_value_and_units(20.0, "Protein", "g")
        assert value == Decimal('20.0')
        assert units == 'g'

    def test_normalize_value_and_units_handles_no_unit(self):
        value, units = normalize_value_and_units(10.0, "Calories", None)
        assert value == Decimal('10.0')
        assert units is None

    def test_normalize_value_and_units_handles_no_value(self):
        value, units = normalize_value_and_units(None, "Calories", "kcal")
        assert value is None
        assert units == 'kcal'