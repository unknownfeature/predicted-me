import os
import traceback

import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

from shared import constants
from shared.variables import *

opensearch_endpoint = os.getenv(opensearch_endpoint)
opensearch_port = int(os.getenv(opensearch_port))
opensearch_index = os.getenv(opensearch_index)
opensearch_index_refresh_interval = os.getenv(opensearch_index_refresh_interval)
vector_dimension = int(os.getenv(embedding_vector_dimension))
region = os.getenv(aws_region)
credentials = boto3.Session().get_credentials()

aws_auth = AWS4Auth(credentials.access_key, credentials.secret_key, region, constants.es, session_token=credentials.token)


def handler(event, _):
    request_type = event[constants.request_type]

    if request_type == constants.create_request_type or request_type == constants.update_request_type:

        return on_create()

    return  {constants.resource_status: constants.resource_success}


def on_create():

    opensearch_client = OpenSearch(
        hosts=[{constants.host: opensearch_endpoint, constants.port: opensearch_port}],
        http_auth=aws_auth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection
    )

    index_mapping = {
        constants.settings: {constants.index: {constants.knn: True}},

        constants.mappings: {
            constants.properties: {
                constants.vector_field: {
                    constants.type: constants.knn_vector,
                    constants.dimension: int(vector_dimension)
                },
                constants.note_id: {constants.type: constants.integer},
                constants.user_id: {constants.type: constants.integer},

            }
        }
    }

    try:
        if not opensearch_client.indices.exists(index=opensearch_index):
            print(f'Index {opensearch_index} does not exist. Creating...')
            opensearch_client.indices.create(index=opensearch_index, body=index_mapping)
            print('Index creation successful.')
        else:
            print(f'Index {opensearch_index} already exists. No action taken.')

        return {constants.resource_status: constants.resource_success}

    except Exception as e:
        traceback.print_exc()
        return  {constants.resource_status: constants.resource_failed, constants.resource_reason: str(e)}