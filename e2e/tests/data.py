import asyncio
import uuid

import pytest

from e2e.clients import data, metric, tag, data_schedule
from e2e.common import get_utc_timestamp
from shared import constants


@pytest.mark.asyncio
async def test_data_can_be_added_modified_manually(jwt: str):
    test_metric_name = uuid.uuid4().hex
    test_metric_tags = [uuid.uuid4().hex for _ in range(3)]
    metric_id = metric.create(name=test_metric_name, tags=test_metric_tags, jwt=jwt)
    stored_metric = metric.get(metric_id, jwt=jwt)[0]

    assert stored_metric and stored_metric[constants.name] == test_metric_name
    assert stored_metric and sorted(stored_metric[constants.tags]) == sorted(test_metric_tags)

    found_tag = tag.get(query_params={constants.name: test_metric_tags[0]}, jwt=jwt)
    assert found_tag and found_tag[0] == test_metric_tags[0]

    id = data.create(metric_id, 1, 'ml', get_utc_timestamp(), jwt=jwt)
    stored_data = data.get(id, jwt=jwt)[0]
    assert stored_data and stored_data[constants.value] == 1
    assert stored_data[constants.units] == 'ml'
    assert stored_data[constants.metric][constants.name] == test_metric_name

    new_test_metric_tags = [uuid.uuid4().hex for _ in range(3)]
    metric.edit(metric_id, test_metric_name, new_test_metric_tags, jwt=jwt)
    schedule_id = data_schedule.create(metric_id, 4, 'g', '*', jwt=jwt)
    stored_data_all = data.get(id, jwt=jwt)
    assert stored_data_all and len(stored_data_all) == 1
    stored_data = stored_data_all[0]

    assert sorted(stored_data[constants.metric][constants.tags]) == sorted(new_test_metric_tags)
    assert stored_data[constants.metric][constants.schedule][constants.minute] == '*'
    assert stored_data[constants.metric][constants.schedule][constants.hour] == '*'

    await asyncio.sleep(61)
    stored_data_all = data.get(None, query_params={constants.metric: test_metric_name} , jwt=jwt)
    assert stored_data_all and len(stored_data_all) == 2 # scheduled
    data_schedule.delete(schedule_id, jwt=jwt)
    data.delete(id, jwt=jwt)



