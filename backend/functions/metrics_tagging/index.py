import os
import json
import traceback
from typing import List, Dict, Any

import boto3
from sqlalchemy import create_engine, select, update, insert, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.mysql import insert as mysql_insert

from backend.lib.db import Metrics, Message, MetricOrigin, metrics_tags_association, Data
from backend.lib.db.util import begin_session


sns_client = boto3.client('sns')
bedrock_runtime = boto3.client('bedrock-runtime')

SNS_TOPIC_ARN = os.environ.get('TAGGING_TOPIC_ARN')
text_extraction_model = os.environ.get('TEXT_EXTRACTION_MODEL')

tagging_prompt = """
You are an expert taxonomy and categorization engine. Analyze the provided metrics data (name, value, units, origin) 
and assign 1 to 3 relevant categories from the following global taxonomy: 
[HEALTH_FITNESS, NUTRITION, SOCIAL_MEDIA, FINANCIAL_WELLBEING, RECURRENT_GOAL, EMOTIONAL_STATE, ACTIVITY].

Output ONLY a JSON array where each object contains the original 'id' of the metric and a list of 'tags' assigned.
"""


def call_bedrock_for_tags(untagged_metrics) -> List[Dict[str, Any]]:

    prompt = (
            tagging_prompt +
            f"\n\nMetrics to Tag:\n{json.dumps([{
                'id': m.id,
                'name': m.name,
                'units': m.units,
                'origin': m.origin.value} for m in untagged_metrics
            ])}"
    )

    try:
        response = bedrock_runtime.invoke_model(
            modelId=text_extraction_model,
            contentType="application/json",
            accept="application/json",
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}],
            })
        )

        response_body = json.loads(response['body'].read())
        tags_json_str = response_body['content'][0]['text'].strip()

        if tags_json_str.startswith('```'):
            tags_json_str = tags_json_str.split('\n', 1)[-1].strip('`').strip('json').strip()

        return json.loads(tags_json_str)

    except Exception as e:
        print(f"Bedrock tagging failed: {e}")
        traceback.print_exc()
        raise e


def handler(event, context):
    session = None

    try:
        session = begin_session()

        for record in event['Records']:
            sns_notification = json.loads(record['body'])
            payload = json.loads(sns_notification['Message'])
            message_id = payload.get('message_id')

            if not message_id:
                print("Skipping record: message_id not found in payload.")
                continue

            print(f"Starting tagging process for Message ID: {message_id}")

            query = select(Metrics).join(Data, Metrics.data_points).where(Data.message_id == message_id)

            untagged_metrics =  session.scalars(query).all()

            if not untagged_metrics:
                print(f"All metrics for ID {message_id} are already tagged. Skipping.")
                continue

            llm_tag_results = call_bedrock_for_tags(untagged_metrics)

            if not llm_tag_results:
                print(f"Bedrock returned no tags for {len(untagged_metrics)} metrics.")
                continue

            metrics_to_update, tags_to_insert = get_tags_and_metrics_for_update(llm_tag_results)

            if tags_to_insert:
                tag_insert_stmt = (
                    insert(metrics_tags_association)
                    .values(tags_to_insert)
                    .prefix_with('IGNORE')
                )
                session.execute(tag_insert_stmt)
                print(f"Attempted to insert {len(tags_to_insert)} unique metric-tag associations.")

            update_stmt = (
                    update(Metrics)
                    .where(Metrics.id.in_(metrics_to_update))
                    .values(tagged=True)
                )
            session.execute(update_stmt)

        session.commit()

    except Exception as e:
        if session:
            session.rollback()
        print(f"FATAL TRANSACTION FAILURE: {e}")
        traceback.print_exc()
        raise e

    finally:
        if session:
            session.close()

    return {'statusCode': 200, 'body': f"Successfully processed {len(event['Records'])} SQS messages."}


def get_tags_and_metrics_for_update(llm_tag_results):
    tags_to_insert = []
    metrics_to_update = []
    for result in llm_tag_results:
        metric_id = result.get('id')
        tags = result.get('tags', [])

        if metric_id and tags:
            metrics_to_update.append(metric_id)

            for tag_name in tags:
                tags_to_insert.append({
                    'metrics_id': metric_id,
                    'tag': tag_name.upper()
                })
    return metrics_to_update, tags_to_insert