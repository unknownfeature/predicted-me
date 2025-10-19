import os
from typing import List

import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
from sqlalchemy.orm import Session
from backend.lib.db import Note
from shared import constants
from backend.lib.func.sqs import handler_factory, process_record_factory, Params, note_text_supplier, Model
from shared.variables import *

opensearch_endpoint = os.getenv(opensearch_endpoint)
opensearch_port = int(os.getenv(opensearch_port))
opensearch_index = os.getenv(opensearch_index)

embedding_model = os.getenv(embedding_model)

region = os.getenv(aws_region)
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


def on_response_from_model(session: Session, note_id: int, __: str, data: List[float]):
    note = session.query(Note).filter(Note.id == note_id).first()
    if not note:
        print(f"Note {note_id} not found")
        return
    document = {
        constants.vector_field: data,
        constants.note_id: note_id,
        constants.user_id: note.user_id,
    }
    opensearch_client.index(
        index=opensearch_index,
        body=document,
        id=note_id
    )


handler = handler_factory(
    process_record_factory(Params(None, note_text_supplier, Model(embedding_model)), on_response_from_model))