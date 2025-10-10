import os
from typing import List

import boto3
from boto3 import Session
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

from backend.lib import constants
from backend.lib.func.sqs import handler_factory, process_record_factory, Params, note_text_supplier, Model
from shared.variables import Env

opensearch_endpoint = os.getenv(Env.opensearch_endpoint)
opensearch_port = int(os.getenv(Env.opensearch_port))
opensearch_index = os.getenv(Env.opensearch_index)

embedding_model = os.getenv(Env.embedding_model)

region = os.getenv(Env.aws_region)
bedrock_client = boto3.client(constants.bedrock_runtime)

service = constants.es
credentials = boto3.Session().get_credentials()
aws_auth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)

opensearch_client = OpenSearch(
    hosts=[{constants.host: opensearch_endpoint, constants.port: 443}],
    http_auth=aws_auth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection
)


def on_response_from_model(_: Session, note_id: int, origin: str, data: List[float]):
    document = {
        constants.origin: origin,
        constants.vector_field: data,
        constants.note_id: note_id
    }
    opensearch_client.index(
        index=opensearch_index,
        body=document,
        id=f'{note_id}_{origin}'
    )


handler = handler_factory(
    process_record_factory(Params(None, note_text_supplier, Model(embedding_model)), on_response_from_model))