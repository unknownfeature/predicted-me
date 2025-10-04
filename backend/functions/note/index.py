import json
import os
from typing import Dict, Any, List

import boto3
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session

from backend.lib.db import Note, Tag, Metric, MetricOrigin, Data
from backend.lib.func.http import handler_factory, RequestContext
from backend.lib.util import get_ts_start_and_end, HttpMethod
from shared.variables import Env

sns_client = boto3.client('sns')
sns_topic_arn = os.getenv(Env.text_processing_topic_arn)


# todo extract this function
def send_text_to_sns(text, note_id):
    if not text:
        return

    sns_payload = {
        'note_id': note_id,
        'origin': MetricOrigin.text
    }

    sns_client.publish(
        TopicArn=sns_topic_arn,
        Note=json.dumps(sns_payload),
        Subject='Text ready for metrics extraction for Note ID {note_id} and origin {origin}.'
    )

    print(f"Sent SNS note for structuring of Note ID {note_id}.")


def post(session: Session, request_context: RequestContext) -> tuple[dict[str, Any], int]:
    body = request_context.body

    new_note = Note(
        user_id=request_context.user.id,
        text=body.get('text'),
        image_key=body.get('image_key'),
        audio_key=body.get('audio_key'),
    )

    session.add(new_note)
    session.flush()
    session.commit()
    send_text_to_sns(body.get('text'), new_note.id)
    return {
        'id': new_note.id,
        'time': new_note.time
    }, 201


def get(session: Session, request_context: RequestContext) -> tuple[List[Dict[str, Any]], int]:
    query_params = request_context.query_params
    path_params = request_context.path_params

    start_time, end_time = get_ts_start_and_end(query_params)

    note_id = path_params.get('id')
    tags = query_params.get('tags').split(',') if 'tags' in query_params else []
    metrics = query_params.get('metrics').split(',') if 'metrics' in query_params else []

    search_text = query_params.get('search_text')

    note_query = select(Note)

    conditions = [
        Note.user_id == request_context.user.id,
    ]

    if not note_id:
        conditions.extend([Note.time >= start_time, Note.time <= end_time])
        if tags or metrics:
            note_query = note_query.join(Note.data_points).join(Data.metric)

        if tags:
            conditions.append(Metric.tags.any(Tag.name.in_(tags)))
        if metrics:
            conditions.append(Metric.name.in_(metrics))

        if search_text:
            search_columns = Note.text, Note.image_text, Note.image_description, Note.audio_text

            full_text_condition = func.match(*search_columns).against(
                search_text,
                natural=True
            )

            conditions.append(full_text_condition)
    else:
        conditions.append(Note.id == int(note_id))

    note_query = note_query.where(
        and_(*conditions)
    ).order_by(Note.time.desc())

    notes = [{
        'id': note.id,
        'text': note.text,
        'time': note.time,
        'image_key': note.image_key,
        'audio_key': note.audio_key,
        'image_described': note.image_described,
        'audio_transcribed': note.audio_transcribed,
        'image_text': note.image_text,
        'image_description': note.audio_transcribed,
        'audio_text': note.image_text,

    }
        for note in session.scalars(note_query).all()]

    return notes, 200

handler = handler_factory({
    HttpMethod.GET.value: get,
    HttpMethod.POST.value: post,

})
