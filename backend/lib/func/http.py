import json
import math
import traceback
from typing import Callable, Dict, Any, List, Set, Tuple

from backend.lib.db import begin_session, get_utc_timestamp
from backend.lib import constants
from backend.lib.util import get_user_ids_from_event
from shared.variables import Common

from sqlalchemy.orm import Session

seconds_in_day = 24 * 60 * 60


class User:
    def __init__(self, id: int, external_id: str):
        self.id = id
        self.external_id = external_id


class RequestContext:
    def __init__(self, body: Dict[str, Any], query_params: Dict[str, Any], path_params: Dict[str, Any], user: User):
        self.body = body
        self.query_params = query_params
        self.path_params = path_params
        self.user = user


def delete_factory(handler: Callable[[Session, int, int], None]) -> Callable[
    [Session, RequestContext], Tuple[Dict[str, Any], int]]:
    def delete(session: Session, request_context: RequestContext) -> (Dict[str, Any], int):
        path_params = request_context.path_params
        id = path_params['id']
        res = handler(session, request_context.user.id, id)
        if res.rowcount == 0:
            session.rollback()
            return {'status': 'not found'}, 404
        session.commit()
        return {'status': 'success'}, 204

    return delete


def patch_factory(updatable_fields: Set[str], handler: Callable[[Session, Dict[str, Any], int, int], None]) -> Callable[
    [Session, RequestContext], Tuple[Dict[str, Any], int]]:
    def patch(session: Session, request_context: RequestContext) -> (Dict[str, Any], int):
        body = request_context.body
        path_params = request_context.path_params

        update_fields = {f: body[f] for f in body if f in updatable_fields}
        id = path_params['id']

        if update_fields:
            res = handler(session, update_fields, request_context.user.id, id)
            if res.rowcount == 0:
                session.rollback()
                return {'status': 'not found'}, 404
            session.commit()
        return {'status': 'success'}, 204

    return patch


def post_factory(entity_supplier: Callable[[RequestContext, Session], Any]) -> Callable[
    [Session, RequestContext], Tuple[Dict[str, Any], int]]:
    def post(session: Session, request_context: RequestContext) -> (Dict[str, Any], int):
        new_entity = entity_supplier(request_context, session)
        session.add(new_entity)
        session.commit()
        return {'status': 'success', 'id': new_entity.id}, 201

    return post


def handler_factory(per_method_handlers: Dict[
    str, Callable[[Session, RequestContext], Tuple[Dict[str, Any] | List[Dict[str, Any]], int]]]) -> Callable[
    [Dict[str, Any], Any], Any]:
    def handler(event: Dict[str, Any], _: Any) -> Dict[str, Any]:
        session = begin_session()

        try:
            body = event[constants.body]
            query_params = event.get(constants.query_params)
            path_params = event.get(constants.path_params)
            http_method = event[constants.http_method]

            if http_method not in per_method_handlers:
                return {'statusCode': 405, 'body': json.dumps({'error': 'Method not allowed'}),
                        'headers': Common.cors_headers, }

            #  move user id to context todo
            result, status_code = per_method_handlers[http_method](session,
                                                                   RequestContext(body, query_params, path_params, User(
                                                                       *get_user_ids_from_event(event, session))))

            return {
                'statusCode': status_code,
                'headers': {'Content-Type': 'application/json'} | Common.cors_headers,
                'body': json.dumps(result)
            }

        except Exception:
            if session:
                session.rollback()

            traceback.print_exc()
            return {'statusCode': 500, 'body': json.dumps({'error': constants.internal_server_error}),
                    'headers': Common.cors_headers, }

        finally:
            session.close()

    return handler


def get_offset_and_limit(query_params, default_offset=0, default_limit=100) -> Tuple[int, int]:
    offset = max(query_params.get(constants.offset, default_offset), default_offset)
    limit = max(min(query_params.get(constants.limit, default_limit),  default_limit), 0)
    return offset, limit


def get_ts_start_and_end(query_params) -> Tuple[int, int]:
    start_param = query_params.get(constants.start)
    end_param = query_params.get(constants.end)

    if not start_param and end_param:
        end_time = int(end_param)
        start_time = end_time - seconds_in_day
    elif start_param and not end_param:
        start_time = int(start_param)
        end_time = get_utc_timestamp()
    elif start_param and end_param:
        start_time = int(start_param)
        end_time = int(end_param)
    else:
        now_utc = get_utc_timestamp()
        start_time = now_utc - seconds_in_day
        end_time = now_utc

    if start_time >= end_time:
        raise ValueError('Start time must be before end time.')
    return start_time, end_time
