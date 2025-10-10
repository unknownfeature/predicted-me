import datetime
import json
import os
import re
from decimal import Decimal
from enum import Enum
from typing import List, Optional

import boto3
from sqlalchemy import (
    BigInteger,
    Integer,
    Boolean,
    String,
    Text,
    ForeignKey,
    Numeric,
    Enum as SQLEnum,
    UniqueConstraint,
    Index,
    create_engine,
    Table, Column, CheckConstraint
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    sessionmaker,
    validates
)

from shared.variables import Env


class Origin(str, Enum):
    text = 'text'
    audio_text = 'audio_text'
    img_desc = 'img_desc'
    img_text = 'img_text'
    user = 'user'
    scheduled = 'scheduled'


def get_utc_timestamp() -> int:
    return int(datetime.datetime.now(datetime.timezone.utc).timestamp())

# todo rewrite and test
def normalize_identifier(name):
    if not name or not name.strip():
        raise ValueError('Identifier cannot be empty.')
    s = name.lower()
    s = s.replace('\s+', '_')
    s = re.sub(r'[^a-z0-9_]', '', s)
    return s


class Base(DeclarativeBase):
    pass


metric_tags_association = Table(
    'metrics_tags',
    Base.metadata,
    Column('metric_id', BigInteger, ForeignKey('metric.id', ondelete='cascade'), primary_key=True),
    Column('tag_id', BigInteger, ForeignKey('tag.id'), primary_key=True),
)

link_tags_association = Table(
    'links_tags',
    Base.metadata,
    Column('link_id', BigInteger, ForeignKey('link.id', ondelete='cascade'), primary_key=True),
    Column('tag_id', BigInteger, ForeignKey('tag.id'), primary_key=True),
)

task_tags_association = Table(
    'tasks_tags',
    Base.metadata,
    Column('task_id', BigInteger, ForeignKey('task.id', ondelete='cascade'), primary_key=True),
    Column('tag_id', BigInteger, ForeignKey('tag.id'), primary_key=True),
)

#  todo in a distant future maybe UI should pass tag ids as well tho nam + user_id lookup is indexed
#   and it's better to check that particular tag bwlongs to the user so not sure
class Tag(Base):
    __tablename__ = 'tag'

    __table_args__ = (
        Index(
            'ft_display_name',
            'display_name',
            mysql_prefix='FULLTEXT',
        ),
        UniqueConstraint('name', 'user_id', name='uq_tag_name'),

    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    name: Mapped[str] = mapped_column(String(500), nullable=False)
    display_name: Mapped[str] = mapped_column(String(500))
    metrics: Mapped[List['Metric']] = relationship(
        secondary=metric_tags_association, back_populates='tags'
    )
    links: Mapped[List['Link']] = relationship(
        secondary=link_tags_association, back_populates='tags'
    )
    tasks: Mapped[List['Task']] = relationship(
        secondary=task_tags_association, back_populates='tags'
    )
    user: Mapped['User'] = relationship()

    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'))

    def __repr__(self) -> str:
        return f'Tag(id={self.id!r}, name={self.name!r})'

    @validates('name')
    def validate_name(self, _, name):
        return normalize_identifier(name)


class User(Base):
    __tablename__ = 'user'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    external_id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    accepted_terms: Mapped[bool] = mapped_column(Boolean, default=False)
    parent_user_id: Mapped[int | None] = mapped_column(ForeignKey('user.id', ondelete='SET NULL'), nullable=True)
    time: Mapped[int] = mapped_column(BigInteger, default=get_utc_timestamp)

    def __repr__(self) -> str:
        return f'User(id={self.id!r}, name={self.name!r})'


class Note(Base):
    __tablename__ = 'note'
    __table_args__ = (
        Index(
            'ft_note_content',
            'text', 'image_text', 'image_description', 'audio_text',
            mysql_prefix='FULLTEXT',
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'))
    user: Mapped['User'] = relationship()
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_key: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    audio_key: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    image_described: Mapped[bool] = mapped_column(Boolean, default=False)
    audio_transcribed: Mapped[bool] = mapped_column(Boolean, default=False)
    image_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    audio_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    time: Mapped[int] = mapped_column(BigInteger, default=get_utc_timestamp)
    data_points: Mapped[list['Data']] = relationship(
        lazy=True,
        back_populates='note',
        cascade='all, delete-orphan'
    )

    links: Mapped[list['Link']] = relationship(
        lazy=True,
        back_populates='note',
        cascade='all, delete-orphan'
    )

    tasks: Mapped[list['Task']] = relationship(
        lazy=True,
        back_populates='note',
        cascade='all, delete-orphan'
    )

    def __repr__(self) -> str:
        return f'Note(id={self.id!r}, user_id={self.user_id!r}, time={self.time})'


class Metric(Base):
    __tablename__ = 'metric'
    __table_args__ = (
        UniqueConstraint('name', 'user_id',  name='uq_metric_name'),
        Index('idx_metric_name', 'name'),
        Index(
            'ft_display_name',
            'display_name',
            mysql_prefix='FULLTEXT',
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(500))
    display_name: Mapped[str] = mapped_column(String(500))

    tagged: Mapped[bool] = mapped_column(Boolean, default=False)
    tags: Mapped[List['Tag']] = relationship(
        secondary=metric_tags_association, back_populates='metrics', lazy=False,
    )

    data_points: Mapped[List['Data']] = relationship(
        back_populates='metric',
        cascade='all, delete-orphan',
        lazy=True
    )
    schedule: Mapped[Optional['DataSchedule']] = relationship(
        back_populates='metric',
        cascade='all, delete-orphan',
        lazy=False
    )

    user: Mapped['User'] = relationship()

    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'))

    def __repr__(self) -> str:
        return f'Metrics(id={self.id!r}, name={self.name!r}, tagged={self.tagged!r})'

    @validates('name')
    def validate_name(self, _, name):
        return normalize_identifier(name)


class Data(Base):
    __tablename__ = 'data'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    metric_id: Mapped[int] = mapped_column(ForeignKey('metric.id'))
    note_id: Mapped[int | None] = mapped_column(ForeignKey('note.id'), nullable=True)

    value: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    units: Mapped[str | None] = mapped_column(String(100), nullable=True)

    time: Mapped[int] = mapped_column(BigInteger, default=get_utc_timestamp)

    origin: Mapped[Origin] = mapped_column(
        SQLEnum(Origin),
        nullable=False
    )
    #  todo think how to do orphan delete where orphan is metric
    metric: Mapped['Metric'] = relationship()

    note: Mapped[Optional['Note']] = relationship()

    def __repr__(self) -> str:
        return (f'Data(id={self.id!r}, metric_id={self.metric_id!r}, '
                f'value={self.value!r}, units={self.units!r}, origin={self.origin.value!r})')


class DataSchedule(Base):
    __tablename__ = 'data_schedule'
    __table_args__ = (
        UniqueConstraint('metric_id', name='uq_metric_schedule'),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    metric_id: Mapped[int] = mapped_column(ForeignKey('metric.id'), unique=True)

    minute: Mapped[str] = mapped_column(String(100), nullable=False)
    hour: Mapped[str] = mapped_column(String(100), nullable=False)
    day_of_month: Mapped[str] = mapped_column(String(100), nullable=False)
    month: Mapped[str] = mapped_column(String(100), nullable=False)
    day_of_week: Mapped[str] = mapped_column(String(100), nullable=False)

    target_value: Mapped[float | None] = mapped_column(Numeric, nullable=False)
    units: Mapped[str | None] = mapped_column(String(100), nullable=True)

    metric: Mapped['Metric'] = relationship(back_populates='schedule')
    next_run: Mapped[int] = mapped_column(BigInteger, nullable=False)

    def __repr__(self) -> str:
        return (f'DataSchedule(metric_id={self.metric_id!r},  target={self.target_value!r})') #todo add repr


class Link(Base):
    __tablename__ = 'link'

    __table_args__ = (
        UniqueConstraint('url', 'user_id', name='uq_link_url'),
        UniqueConstraint('summary', 'user_id', name='uq_link_summary'),

        Index(
            'ft_link_content',
            'description', 'display_summary', 'url',
            mysql_prefix='FULLTEXT',
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    note_id: Mapped[int | None] = mapped_column(ForeignKey('note.id'), nullable=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'))

    url: Mapped[str] = mapped_column(String(500))
    summary: Mapped[str] = mapped_column(String(500), nullable=False)
    display_summary: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    tagged: Mapped[bool] = mapped_column(Boolean, default=False)

    time: Mapped[int] = mapped_column(BigInteger, default=get_utc_timestamp)

    origin: Mapped[Origin] = mapped_column(
        SQLEnum(Origin),
        nullable=False
    )

    note: Mapped[Optional['Note']] = relationship(back_populates='links')
    user: Mapped['User'] = relationship()
    tags: Mapped[List['Tag']] = relationship(
        secondary=link_tags_association, back_populates='links', lazy=False
    )

    @validates('summary')
    def validate_name(self, _, summary):
        return normalize_identifier(summary)

    def __repr__(self) -> str:
        return (f'Link(id={self.id!r},  '
                f'value={self.url!r}, description={self.description!r}, origin={self.origin.value!r})')


class Task(Base):
    __tablename__ = 'task'

    __table_args__ = (
        UniqueConstraint('summary', 'user_id', name='uq_task_summary'),
        Index(

            'ft_task_content',
            'display_summary', 'description',
            mysql_prefix='FULLTEXT',
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    note_id: Mapped[int | None] = mapped_column(ForeignKey('note.id'), nullable=True)
    summary: Mapped[str] = mapped_column(String(500), nullable=False)
    display_summary: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(String(1000), nullable=False)
    tagged: Mapped[bool] = mapped_column(Boolean, default=False)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'))
    user: Mapped['User'] = relationship()
    note: Mapped[Optional['Note']] = relationship(back_populates='tasks')
    tags: Mapped[List['Tag']] = relationship(
        secondary=task_tags_association, back_populates='tasks', lazy=False
    )

    occurrences: Mapped[List['Occurrence']] = relationship(
        back_populates='task',
        cascade='all, delete-orphan',
        lazy=True
    )
    schedule: Mapped[Optional['OccurrenceSchedule']] = relationship(
        back_populates='task',
        cascade='all, delete-orphan',
        lazy=False
    )

    @validates('summary')
    def validate_name(self, _, summary):
        return normalize_identifier(summary)

    def __repr__(self) -> str:
        return (f'Link(id={self.id!r},  '
                f'value={self.description!r}, display_summary={self.display_summary!r}, origin={self.origin.value!r})')


class OccurrenceSchedule(Base):
    __tablename__ = 'occurrence_schedule'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey('task.id'), unique=True)
    task: Mapped['Task'] = relationship(back_populates='schedule')

    minute: Mapped[str] = mapped_column(String(100), nullable=False)
    hour: Mapped[str] = mapped_column(String(100), nullable=False)
    day_of_month: Mapped[str] = mapped_column(String(100), nullable=False)
    month: Mapped[str] = mapped_column(String(100), nullable=False)
    day_of_week: Mapped[str] = mapped_column(String(100), nullable=False)
    next_run: Mapped[int] = mapped_column(BigInteger, nullable=False)

    priority: Mapped[int] = mapped_column(BigInteger, nullable=False)

    __table_args__ = (
        UniqueConstraint('task_id', name='uq_task_schedule'),
        CheckConstraint(priority >= 1, name='schedule_priority_not_zero'),
        CheckConstraint(priority <= 10, name='schedule_priority_less_than_ten')
    )

    def __repr__(self) -> str:
        return (f'TaskSchedule(task_id={self.task_id!r}, priority={self.priority!r} )')


class Occurrence(Base):
    __tablename__ = 'occurrence'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey('task.id'))
    note_id: Mapped[int | None] = mapped_column(ForeignKey('note.id'), nullable=True)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    time: Mapped[int] = mapped_column(BigInteger, default=get_utc_timestamp)
    priority: Mapped[int] = mapped_column(BigInteger, nullable=False)

    origin: Mapped[Origin] = mapped_column(
        SQLEnum(Origin),
        nullable=False
    )

    task: Mapped['Task'] = relationship()

    note: Mapped['Note'] = relationship()

    __table_args__ = (
        CheckConstraint(priority >= 1, name='priority_not_zero'),
        CheckConstraint(priority <= 10, name='priority_less_than_ten')
    )

    def __repr__(self) -> str:
        return (f'Occurrence(id={self.id!r}, task_id={self.task_id!r}, '
                f'priority={self.priority!r}, completed={self.completed!r}, origin={self.origin.value!r})')


secret_arn = os.getenv(Env.db_secret_arn)
db_endpoint = os.getenv(Env.db_endpoint)
db_name = os.getenv(Env.db_name)
db_test = os.getenv(Env.db_test)
db_port = os.getenv(Env.db_port)

secrets_client = boto3.client('secretsmanager', region_name=os.getenv(Env.aws_region))


def begin_session(auto_flush=True):
    engine = setup_engine()

    return sessionmaker(bind=engine, autoflush=auto_flush)()


def setup_engine():
    if not db_test:
        secret_response = secrets_client.get_secret_value(SecretId=secret_arn)
        secret_dict = json.loads(secret_response['SecretString'])

        username = secret_dict['username']
        password = secret_dict['password']
    else:
        username = os.getenv(Env.db_user)
        password = os.getenv(Env.db_pass)
    connection_string = (
        f'mysql+mysqlconnector://{username}:{password}@{db_endpoint}:{db_port}/{db_name}'
    )
    engine = create_engine(connection_string, pool_recycle=300, echo=db_test is not None)
    return engine
