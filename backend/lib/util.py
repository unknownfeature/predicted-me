import json
import traceback
import uuid
from typing import Dict, Any, List

import boto3
from sqlalchemy import select
from sqlalchemy.orm import session

from backend.lib.db import User, get_utc_timestamp_int, MetricOrigin

seconds_in_day = 24 * 60 * 60

text_getters = {
    MetricOrigin.text.value: lambda x: x.text,
    MetricOrigin.audio_text.value: lambda x: x.audio_text,
    MetricOrigin.img_text.value: lambda x: x.img_text,
    MetricOrigin.img_desc.value: lambda x: x.image_description,

}


def get_user_id_from_event(event: Dict[str, Any], session: session) -> int:
    user_query = select(User.id).where(User.external_id == event['requestContext']['authorizer']['jwt']['claims']['username'])
    return session.scalar(user_query)

def get_ts_start_and_end(query_params):
    now_utc = get_utc_timestamp_int()
    start_time = int(query_params.get('start_ts')) if 'start_ts' in query_params else (now_utc - seconds_in_day)
    end_time = int(query_params.get('end_ts')) if 'end_ts' in query_params else now_utc
    if start_time >= end_time:
        raise ValueError("Start time must be before end time.")
    return start_time, end_time



def call_bedrock(model: str, prompt: str, text_content: str, max_tokens = 1024) -> List[Dict[str, Any]]:
    try:
        bedrock_runtime = boto3.client('bedrock-runtime')

        id = uuid.uuid4().hex
        response = bedrock_runtime.invoke_model(
            modelId=model,
            contentType="application/json",
            accept="application/json",
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "notes": [{"role": "user", "content": [{"type": "text", "text": prompt + (
                    f"TEXT FOR ANALYSIS:    ---START_USER_INPUT {id} ---  {text_content} ---END_USER_INPUT  {id} ---"
                ) if text_content else ""}]}],
            })
        )

        response_body = json.loads(response['body'].read())
        metrics_json_str = response_body['content'][0]['text'].strip()

        if metrics_json_str.startswith('```'):
            metrics_json_str = metrics_json_str.split('\n', 1)[-1].strip('`')

        return json.loads(metrics_json_str)

    except Exception as e:
        traceback.print_exc()
        raise e