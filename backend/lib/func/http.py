import json
import traceback
from typing import Callable, Dict, Any, List, Set

from backend.lib.db import begin_session
from backend.lib.util import get_user_id_from_event
from shared.variables import Common

from sqlalchemy.orm import Session


class RequestContext:
    def __init__(self, body: Dict[str, Any], query_params: Dict[str, Any], path_params: Dict[str, Any]):
        self.body = body
        self.query_params = query_params
        self.path_params = path_params

def delete_factory(handler: Callable[[Session, int, int], None]) -> Callable[[Session, int, RequestContext], (Dict[str, Any], int)]:

    def delete(session: Session, user_id: int, request_context: RequestContext) -> (Dict[str, Any], int):
        path_params = request_context.path_params
        id = path_params['id']
        handler(session, user_id, id)
        session.commit()
        return {'status': 'success'}, 204

    return delete

def patch_factory(updatable_fields: Set[str], handler: Callable[[Session, Dict[str, Any], int, int], None]) -> Callable[[Session, int, RequestContext], (Dict[str, Any], int)]:

    def patch(session: Session, user_id: int, request_context: RequestContext) -> (Dict[str, Any], int):
        body = request_context.body
        path_params = request_context.path_params

        update_fields = {f: body[f] for f in body if f in updatable_fields}
        id = path_params['id']

        if update_fields:
          handler(session, update_fields, user_id, id)
          session.commit()
        return {'status': 'success'}, 204

    return patch


def handler_factory(per_method_handlers: Dict[
    str, Callable[[Session, int, RequestContext], (Dict[str, Any] | List[Dict[str, Any]], int)]]) -> Callable[
    [Dict[str, Any], Any], Any]:

    def handler(event: Dict[str, Any], _: Any) -> Dict[str, Any]:
        session = None

        try:
            session = begin_session()

            body = event['body']
            query_params = event.get('queryStringParameters')
            path_params = event.get("pathParameters", {})
            http_method = event['httpMethod']

            user_id = get_user_id_from_event(event, session)

            if http_method not in per_method_handlers:
                return {'statusCode': 405, 'body': json.dumps({'error': 'Method not allowed'}),
                        'headers': Common.cors_headers, }

            result, status_code = per_method_handlers[http_method](session, user_id,
                                                                   RequestContext(body, query_params, path_params))

            return {
                'statusCode': status_code,
                'headers': {'Content-Type': 'application/json'} | Common.cors_headers,
                'body': json.dumps(result)
            }

        except Exception:
            if session:
                session.rollback()

            traceback.print_exc()
            return {'statusCode': 500, 'body': json.dumps({'error': 'Internal server error'}),
                    'headers': Common.cors_headers, }

        finally:
            if session:
                session.close()

    return handler
