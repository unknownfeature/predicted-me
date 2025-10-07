import json
import os
import traceback
from typing import Dict, Any, List, Tuple

import boto3
from sqlalchemy import select, func, and_, inspect
from sqlalchemy.dialects.mysql import match
from sqlalchemy.orm import Session

from backend.lib import constants
from backend.lib.db import Note, Tag, Metric, Origin, Data
from backend.lib.func.http import handler_factory, RequestContext, get_ts_start_and_end, get_offset_and_limit
from backend.lib.util import  HttpMethod
from shared.variables import Env

sns_client = boto3.client('sns')
sns_topic_arn = os.getenv(Env.text_processing_topic_arn)


def send_text_to_sns(note_id: int, origin=Origin.text.value):

    sns_payload = {
        constants.note_id: note_id,
        constants.origin: origin
    }

    sns_client.publish(
        TopicArn=sns_topic_arn,
        Note=json.dumps(sns_payload),
        Subject='Ready for data extraction'
    )


def post(session: Session, request_context: RequestContext) -> Tuple[dict[str, Any], int]:
    body = request_context.body

    text = body.get(constants.text, constants.empty).strip()
    image_key = body.get(constants.image_key)
    audio_key = body.get(constants.audio_key)

    if not text and not image_key and not audio_key:
        return {constants.status: constants.error, constants.error: constants.any_text_is_required}, 500


    new_note = Note(
        user_id=request_context.user.id,
        text=text,
        image_key=image_key,
        audio_key=audio_key,
    )

    session.add(new_note)
    session.commit()

    if text:
        try:
           send_text_to_sns(new_note.id)
        except:
            session.rollback()
            traceback.print_exc()
            return {
                constants.status: constants.error,
            }, 500

    return {
        constants.status: constants.success,
        constants.id: new_note.id,
    }, 201


def get(session: Session, request_context: RequestContext) -> Tuple[List[Dict[str, Any]], int]:

    query_params = request_context.query_params
    path_params = request_context.path_params

    start_time, end_time = get_ts_start_and_end(query_params)

    offset, limit = get_offset_and_limit(query_params)

    id = path_params.get(constants.id)

    tags = query_params.get(constants.tags, constants.empty).split(constants.params_delim) if constants.tags in query_params else []

    metrics = query_params.get(constants.metrics, constants.empty).split(constants.params_delim) if constants.metrics in query_params else []

    search_text = query_params.get(constants.text, constants.empty)

    note_query = select(Note)

    conditions = [
        Note.user_id == request_context.user.id,
    ]

    if not id:
        conditions.extend([Note.time >= start_time, Note.time <= end_time])

        if tags or metrics:
            note_query = note_query.join(Note.data_points).join(Data.metric)

        if tags:
            conditions.append(Metric.tags.any(Tag.display_name.in_(tags)))

        if metrics:
            conditions.append(Metric.display_name.in_(metrics))

        if search_text:
            search_columns = inspect(Note).c.text, inspect(Note).c.image_text, inspect(Note).c.image_description, inspect(Note).c.audio_text
            conditions.append(match(*search_columns, against=search_text).in_natural_language_mode())

    else:

        conditions.append(Note.id == int(id))

    note_query = note_query.where(and_(*conditions)).offset(offset).limit(limit).order_by(Note.time.desc())

    notes = [{
        constants.id: note.id,
        constants.text: note.text,
        constants.time: note.time,
        constants.image_key: note.image_key,
        constants.audio_key: note.audio_key,
        constants.image_described: note.image_described,
        constants.audio_transcribed: note.audio_transcribed,
        constants.image_text: note.image_text,
        constants.image_description: note.image_description,
        constants.audio_text: note.audio_text,

    }
        for note in session.scalars(note_query).all()]

    return notes, 200

handler = handler_factory({
    HttpMethod.GET.value: get,
    HttpMethod.POST.value: post,

})
