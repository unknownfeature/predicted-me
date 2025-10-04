import uuid
from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.lib.db import Base, User, Note, Metric, Data, DataOrigin


@pytest.fixture(scope="module")
def session():
    engine = create_engine("sqlite:///:memory:", echo=False)

    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db_session = Session()
    yield db_session
    db_session.close()


def test_mapping(session):

    session.query(Data).delete()
    session.query(Note).delete()
    session.query(User).delete()
    session.query(Metric).delete()
    session.commit()

    parent_user = User(external_id=str(uuid.uuid4()), name="Parent")
    session.add(parent_user)
    session.flush()

    child_user = User(external_id=str(uuid.uuid4()), name="Child", parent_user_id=parent_user.id)
    session.add(child_user)
    session.flush()

    note1 = Note(user_id=child_user.id, text="Parent's first note", time=int(datetime.utcnow().timestamp()))
    note2 = Note(user_id=child_user.id, text="Parent's second note", time=int(datetime.utcnow().timestamp()))
    session.add_all([note1, note2])
    session.flush()

    metric = Metric(name="Heart Rate", user = child_user)
    data_point = Data(note=note1, metric=metric, value=75.5, units="bpm", origin=DataOrigin.text,
                      time=int(datetime.utcnow().timestamp()))

    session.add_all([metric, data_point])
    session.flush()
    session.commit()
