import json
import traceback
from typing import Dict, Any, List, Union

from sqlalchemy import select, update, and_, delete as sql_delete, func
from sqlalchemy.orm import Session, joinedload

from backend.lib.db import begin_session, Note, Tag, User, Link
from backend.lib.util import get_user_id_from_event, get_ts_start_and_end

from shared.variables import Common


#  todo add ability to add link manually
def delete(session: Session, id: int, user_id: int) -> tuple[dict[str, Union[int, str]], int]:
    session.execute(sql_delete(Link).where(
        and_(
            Link.id == id,
            Link.note.has(Note.user_id == user_id)
        )
    )
    )
    return {'status': 'success'}, 204


def get(session: Session, user_id: int, query_params: Dict[str, Any]) -> tuple[List[Dict[str, Any]], int]:
    link_id = query_params.get('id')
    note_id = query_params.get('note_id')
    tags = query_params.get('tags').split(',') if 'tags' in query_params else []
    search_text = query_params.get('search_text')
    end_time, start_time = get_ts_start_and_end(query_params)
    conditions = [
        Link.note.user_id == user_id
    ]
    query = select(Link)

    if not note_id and not link_id:
        conditions.extend([
            Link.time >= start_time,
            Link.time <= end_time
        ])

        if tags:
            conditions.append(Link.tags.any(Tag.name.in_(tags)))
        if search_text:
            search_columns = Link.description, Link.url

            full_text_condition = func.match(*search_columns).against(
                search_text,
                natural=True
            )

            conditions.append(full_text_condition)
    elif link_id:
        conditions.append(Link.id == int(link_id))
    elif note_id:
        conditions.append(Note.id == int(note_id))
    query = query.where(and_(*conditions)) \
        .order_by(Link.time.desc()) \
        .options(
        joinedload(Link.tags)
    )

    links = session.scalars(query).all()

    return [{
        'id': link.id,
        'note_id': link.note_id,
        'url': link.url,
        'description': link.description,
        'origin': link.origin.value,
        'tagged': link.tagged,
        'time': link.time,
        'tags': [tag for tag in link.tags],
    } for link in links], 200


# todo add the ability to modify tags, requires remapping
def patch(session: Session, id: int, user_id, body: Dict[str, Any]) -> tuple[Dict[str, Any], int]:
    update_fields = {f: body[f] for f in body if f in {'url', 'description', 'time'}}

    if update_fields:
        update_stmt = update(Link).where(and_([Link.id == id, User.id == user_id])).values(
            **update_fields)
        session.execute(update_stmt)

    return {'status': 'success', 'id': id}, 200


def handler(event: Dict[str, Any], _: Any) -> Dict[str, Any]:
    session = None

    try:

        session = begin_session()
        user_id = get_user_id_from_event(event, session)

        http_method = event['httpMethod']
        body = json.loads(event.get('body', '{}'))
        query_params = event.get('queryStringParameters') or {}
        path_params = event.get("pathParameters", {})

        if http_method == 'GET':
            response_data, status_code = get(session, user_id, query_params)

        elif http_method == 'PATCH':
            id = path_params['id']
            response_data, status_code = patch(session, id, user_id, body)
            session.commit()

        elif http_method == 'DELETE':
            id = path_params['id']
            response_data, status_code = delete(session, id, user_id)
            session.commit()

        else:
            return {'statusCode': 405, 'body': json.dumps({'error': 'Method not allowed'}),
                    'headers': Common.cors_headers, }

        return {
            'statusCode': status_code,
            'headers': {'Content-Type': 'application/json'} | Common.cors_headers,
            'body': json.dumps(response_data)
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
