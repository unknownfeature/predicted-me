from sqlalchemy import select, update

from backend.lib.db import begin_session, get_utc_timestamp, OccurrenceSchedule, Occurrence, Origin
from backend.lib.util import get_next_run_timestamp, cron_expression_from_schedule


#  todo this should be rewritten because of race condition plus because run can take long
def handler(_, __):
    session = begin_session()
    try:

        now_ts = get_utc_timestamp()

        due_schedules_stmt = select(OccurrenceSchedule).where(OccurrenceSchedule.next_run <= now_ts)
        due_schedules = session.scalars(due_schedules_stmt).all()

        for schedule in due_schedules:
            next_run = get_next_run_timestamp(cron_expression_from_schedule(schedule), period_seconds=schedule.period_seconds)

            update_stmt = (
                update(OccurrenceSchedule)
                .where(OccurrenceSchedule.id == schedule.id)
                .values(
                    next_run=int(next_run),

                )
            )
            session.execute(update_stmt)
            data_to_insert = Occurrence(priority=schedule.priority,  task=schedule.task)
            session.add(data_to_insert)

        session.commit()



    finally:
        session.close()
