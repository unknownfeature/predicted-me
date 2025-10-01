import json
import json
import time
import traceback
from typing import Dict, Any, List

from sqlalchemy import select, update
from sqlalchemy.orm import session, joinedload

from backend.lib.db import Note, Data, Metrics, DataSchedule, begin_session
from backend.lib.util import seconds_in_day, get_user_id_from_event, get_ts_start_and_end


def parse_numeric_timestamp_safe(ts_str: str | None, default_ts: int) -> int:
    # (Implementation remains the same: safely converts string to integer timestamp)
    if ts_str is None: return default_ts
    try:
        return int(float(ts_str))
    except ValueError:
        raise ValueError(f"Invalid timestamp value: '{ts_str}'. Must be a numeric string.")


def handle_numeric_time_filters(user_id: int, query_params: Dict[str, Any]) -> List[Any]:
    # (Implementation remains the same, adapted for Data model filtering)
    now_ts = int(time.time())


    start_ts_str = query_params.get('start')
    end_ts_str = query_params.get('end')
    data_id = query_params.get('id')

    conditions = [
        # Filter by metrics_id (or message_id) associated with the user
        # We must join to Message to filter by User ID, as Data has no direct User FK.
        # This is a placeholder; actual query must use a JOIN or a subquery on Message.
        # For simplicity, we assume a join will be built into the main handler's query.
    ]

    if data_id:
        conditions.append(Data.id == int(data_id))
        # Note: If filtering by ID, time filter is ignored in the main query.
    else:
        # Determine final numeric range
        final_start_ts = parse_numeric_timestamp_safe(start_ts_str, now_ts - seconds_in_day)
        final_end_ts = parse_numeric_timestamp_safe(end_ts_str, now_ts)

        if final_start_ts >= final_end_ts:
            raise ValueError("Start time must be strictly before end time.")

        # Filter by Data measurement time
        # NOTE: Data table doesn't have a 'time' column! We must use the Message.time column
        # OR add a timestamp column to the Data table.
        # Assuming Data has a 'timestamp' column for this implementation:
        # conditions.append(Data.timestamp >= final_start_ts)
        # conditions.append(Data.timestamp <= final_end_ts)

        # FIX: Since Data does NOT have time, this query must join to Message and use Message.time
        # We will build the joined query directly in handle_get_data.
        pass

    return conditions


def get(session: session, user_id: int, query_params: Dict[str, Any]) -> List[Dict[str, Any]]:
    conditions = [
        DataSchedule.user_id == user_id
    ]

    metric_id = query_params.get('id')
    note_id = query_params.get('note_id')
    end_time, start_time = get_ts_start_and_end(query_params)

    if not note_id and not data_id:
        conditions.append(Data.time >= start_time)
        conditions.append(Data.time <= end_time)
    elif data_id:
        conditions.append(Data.id == int(data_id))
    elif note_id:
        conditions.append(Data.note.id == int(note_id))

    query = select(Data).join(Note).join(Data.metric_type).join(Metrics.tags).join(
        Metrics.schedules).filter(DataSchedule.user_id == user_id).where(and_(*conditions))

    data_points = session.scalars(query).all()

    return [{
        'id': dp.id,
        'message_id': dp.message_id,
        'value': float(dp.value),
        'units': dp.units,
        'origin': dp.origin.value,
        'metric': {
            'id': dp.metric_type.id,
            'name': dp.metric_type.name,
            'is_tagged': dp.metric_type.tagged,
            'tags': [tag for tag in dp.metric_type.tags],
            'schedule': {} if dp.metric_type.schedules is None else {
                'recurrence_schedule': dp.metric_type.schedules[0].recurrence_schedule,
                'target_value': dp.metric_type.schedules[0].target_value,
                'units': dp.metric_type.schedules[0].units,
            }
        }} for dp in data_points]



query = select(Data).join(Note).options(
        joinedload(Data.metric_type).joinedload(Metrics.tags)
    ).where(Note.user_id == user_id)

    # 2. Apply Time/ID Filters
    data_id = query_params.get('id')

    if data_id:
        query = query.where(Data.id == int(data_id))
    else:
        # If no ID, apply time filter using Message.time (assuming Message.time is BigInt timestamp)
        now_ts = int(time.time())
        seconds_in_day = 86400

        final_start_ts = parse_numeric_timestamp_safe(query_params.get('start'), now_ts - seconds_in_day)
        final_end_ts = parse_numeric_timestamp_safe(query_params.get('end'), now_ts)

        query = query.where(Message.time >= final_start_ts).where(Message.time <= final_end_ts)

    data_points = session.scalars(query).all()

    # 3. Serialize Results
    results = []
    for dp in data_points:
        metric = dp.metric_type
        results.append({
            'id': dp.id,
            'message_id': dp.message_id,
            'value': float(dp.value),
            'units': dp.units,
            'origin': dp.origin.value,
            'metric': {
                'id': metric.id,
                'name': metric.name,
                'is_tagged': metric.tagged,
                'tags': [tag for tag in metric.tags]
            }
        })
    return results


def handle_update_data(session: sessionmaker, data_id: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Updates the value, units, and/or time of a single data measurement."""

    # 1. Retrieve the data point
    target_data = session.get(Data, data_id)
    if not target_data:
        raise ValueError(f"Data point ID {data_id} not found.")

    update_fields = {}

    # Update logic (applying only fields present in the body)
    if 'value' in body:
        update_fields[Data.value] = body['value']
    if 'units' in body:
        update_fields[Data.units] = body['units']
    if 'time' in body:
        # NOTE: You need a 'time' column in the Data table for this,
        # but for now, we'll update the parent Message time if data doesn't have its own time.
        # Assuming 'time' in body refers to the time of the parent Message:
        if target_data.message:
            target_data.message.time = parse_numeric_timestamp_safe(body['time'], int(time.time()))
            session.add(target_data.message)

    if update_fields:
        # Execute the update on the specific Data row
        update_stmt = update(Data).where(Data.id == data_id).values(**update_fields)
        session.execute(update_stmt)

    return {'status': 'success', 'data_id': data_id}



def handle_setup_schedule(session: sessionmaker, metric_id: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Sets or updates the recurrent schedule/goal for a specific Metric definition."""

    # 1. Validate inputs
    schedule = body.get('recurrence_schedule')
    target_value = body.get('target_value')
    units = body.get('units')

    if not schedule:
        raise ValueError("Must provide 'recurrence_schedule'.")
    if target_value is None:
        raise ValueError("Must provide 'target_value'.")

    # 2. Check if schedule already exists (UniqueConstraint on metrics_id handles this too)
    target_schedule = session.scalar(
        select(DataSchedule).where(DataSchedule.metrics_id == metric_id)
    )

    if target_schedule:
        # Update existing schedule
        target_schedule.recurrence_schedule = schedule
        target_schedule.target_value = target_value
        target_schedule.units = units
        session.add(target_schedule)
        status = 'updated'
    else:
        # Create new schedule
        new_schedule = DataSchedule(
            metrics_id=metric_id,
            recurrence_schedule=schedule,
            target_value=target_value,
            units=units
        )
        session.add(new_schedule)
        session.flush()  # Flush to get the ID for the response
        metric_id = new_schedule.metrics_id
        status = 'created'

    return {'status': status, 'metric_id': metric_id}


def handler(event: Dict[str, Any], _: Any) -> Dict[str, Any]:
    session = None

    try:

        session = begin_session()
        user_id = get_user_id_from_event(event, session)

        http_method = event['httpMethod']
        path = event['path']
        body = json.loads(event.get('body', '{}'))
        query_params = event.get('queryStringParameters') or {}
        path_params = event.get("pathParameters", {})



        if http_method == 'GET':
            response_data = get(session, user_id, query_params)
            status_code = 200

        elif http_method == 'PATCH':
            data_id = path_params['id']
            response_data = handle_update_data(session, int(data_id), body)
            status_code = 200

        elif http_method == 'POST' and path == '/data/schedule':
            metric_id  = path_params['metrics_id']
            if not metric_id:
                raise ValueError("Missing 'metrics_id' for schedule setup.")

            response_data = handle_setup_schedule(session, int(metric_id), body)
            status_code = 201

        else:
            return {'statusCode': 405, 'body': json.dumps({'error': 'Method/Path not allowed'})}

        session.commit()

        return {
            'statusCode': status_code,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(response_data)
        }

    except PermissionError as e:
        return {'statusCode': 403, 'body': json.dumps({'error': str(e)})}
    except ValueError as e:
        return {'statusCode': 400, 'body': json.dumps({'error': str(e)})}
    except Exception as e:
        if session:
            session.rollback()
        traceback.print_exc()
        return {'statusCode': 500, 'body': json.dumps({'error': 'Internal server error'})}

    finally:
        if session:
            session.close()