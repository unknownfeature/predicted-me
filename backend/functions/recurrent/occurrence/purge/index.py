import json
from datetime import datetime, timezone

from dateutil.relativedelta import relativedelta
from sqlalchemy import delete

from backend.lib import constants
from backend.lib.db import begin_session, Data, Occurrence


def handler(event, _):
    session = begin_session()
    try:

        three_months_ago = datetime.now(timezone.utc) - relativedelta(months=3)
        cutoff_timestamp = int(three_months_ago.timestamp())

        print(f'Deleting data older than: {three_months_ago.isoformat()} ({cutoff_timestamp})')

        delete_stmt = delete(Occurrence).where(Data.time < cutoff_timestamp)

        result = session.execute(delete_stmt)
        session.commit()

        print(f'Successfully deleted {result.rowcount} rows.')

        return {
            constants.status_code: 200,
            constants.body: json.dumps(f'Deleted {result.rowcount} rows.')
        }


    finally:
        session.close()
