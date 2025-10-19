import uuid

import pytest

from e2e.clients import link, tag
from shared import constants


@pytest.mark.asyncio
async def test_link_can_be_added_modified_manually(jwt: str):
    test_link_summary = uuid.uuid4().hex
    test_link_tags = [uuid.uuid4().hex for _ in range(3)]
    test_link_url = 'http://fff'
    link_id = link.create(description=test_link_summary, url=test_link_url, summary=test_link_summary, tags=test_link_tags, jwt=jwt)
    stored_link = link.get(link_id, jwt=jwt)[0]

    assert stored_link and stored_link[constants.summary] == test_link_summary
    assert stored_link and sorted(stored_link[constants.tags]) == sorted(test_link_tags)

    found_tag = tag.get(query_params={constants.summary: test_link_tags[0]}, jwt=jwt)
    assert found_tag and found_tag[0] == test_link_tags[0]



    new_test_link_tags = [uuid.uuid4().hex for _ in range(3)]
    new_test_link_url = 'http://fffnew'

    link.edit(link_id, url=new_test_link_url, description=test_link_summary, summary=test_link_summary, tags=new_test_link_tags, jwt=jwt)
    stored_data = link.get(link_id, jwt=jwt)[0]
    assert sorted(stored_data[constants.link][constants.tags]) == sorted(new_test_link_tags)
    assert stored_data[constants.link][constants.url] == new_test_link_url