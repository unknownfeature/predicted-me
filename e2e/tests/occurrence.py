import asyncio
import uuid

import pytest

from e2e.clients import occurrence, task, tag, occurrence_schedule
from e2e.common import get_utc_timestamp
from shared import constants


@pytest.mark.asyncio
async def test_occurrence_can_be_added_modified_manually(jwt: str):
    test_task_summary = uuid.uuid4().hex
    test_task_tags = [uuid.uuid4().hex for _ in range(3)]
    task_id = task.create(summary=test_task_summary, description=test_task_summary, tags=test_task_tags, jwt=jwt)
    stored_task = task.get(task_id, jwt=jwt)[0]

    assert stored_task and stored_task[constants.summary] == test_task_summary
    assert stored_task and sorted(stored_task[constants.tags]) == sorted(test_task_tags)

    found_tag = tag.get(query_params={constants.summary: test_task_tags[0]}, jwt=jwt)
    assert found_tag and found_tag[0] == test_task_tags[0]

    id = occurrence.create(task_id, 1,  jwt=jwt)
    stored_occurrence = occurrence.get(id, jwt=jwt)[0]
    assert stored_occurrence and stored_occurrence[constants.value] == 1
    assert stored_occurrence[constants.description] == test_task_summary
    assert stored_occurrence[constants.task][constants.summary] == test_task_summary

    new_test_task_tags = [uuid.uuid4().hex for _ in range(3)]
    task.edit(task_id, test_task_summary, new_test_task_tags, jwt=jwt)
    schedule_id = occurrence_schedule.create(task_id, 4, '*', jwt=jwt)
    stored_occurrence_all = occurrence.get(id, jwt=jwt)
    assert stored_occurrence_all and len(stored_occurrence_all) == 1
    stored_occurrence = stored_occurrence_all[0]

    assert sorted(stored_occurrence[constants.task][constants.tags]) == sorted(new_test_task_tags)
    assert stored_occurrence[constants.task][constants.schedule][constants.minute] == '*'
    await asyncio.sleep(61)
    stored_occurrence_all = occurrence.get(None, query_params={constants.task: test_task_summary} , jwt=jwt)
    assert stored_occurrence_all and len(stored_occurrence_all) == 2 # scheduled
    occurrence_schedule.delete(schedule_id, jwt=jwt)
    occurrence.delete(id, jwt=jwt)



