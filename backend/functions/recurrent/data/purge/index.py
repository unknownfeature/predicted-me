import json
import json
from datetime import datetime, timezone

import boto3
from dateutil.relativedelta import relativedelta
from sqlalchemy import delete

from backend.lib.db import begin_session, Data

def handler(event, context):
    session = begin_session()
    try:

        three_months_ago = datetime.now(timezone.utc) - relativedelta(months=3)
        cutoff_timestamp = int(three_months_ago.timestamp())

        print(f"Deleting data older than: {three_months_ago.isoformat()} ({cutoff_timestamp})")

        delete_stmt = delete(Data).where(Data.time < cutoff_timestamp)

        result = session.execute(delete_stmt)
        session.commit()

        print(f"Successfully deleted { result.rowcount} rows.")

        return {
            constants.statusCode: 200,
            constants.body: json.dumps(f"Deleted { result.rowcount} rows.")
        }


    finally:
        session.close()
