import datetime
import json
import os
from enum import Enum
from typing import List

import boto3
from sqlalchemy import (
    BigInteger,
    Boolean,
    String,
    Text,
    ForeignKey,
    Numeric,
    Enum as SQLEnum,
    UniqueConstraint,
    Index,
    create_engine
)
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    sessionmaker
)

from shared.variables import Env


def get_utc_timestamp_int() -> int:
    return int(datetime.datetime.now(datetime.timezone.utc).timestamp())


class Base(DeclarativeBase):
    pass


class Tag(Base):
    __tablename__ = "tag"

    metrics_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("metrics.id"), nullable=False, primary_key=True, )
    tag: Mapped[str] = mapped_column(String(500), nullable=False, primary_key=True)
    metric_type: Mapped["Metrics"] = relationship(back_populates="tags")


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    external_id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    accepted_terms: Mapped[bool] = mapped_column(Boolean, default=False)
    parent_user_id: Mapped[int | None] = mapped_column(ForeignKey("user.id", ondelete="SET NULL"), nullable=True)

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, name={self.name!r})"


class Note(Base):
    __tablename__ = "note"

    Index(
        'ft_note_content',
        'text', 'image_text', 'image_description', 'audio_text',
        mysql_prefix='FULLTEXT',
    ),
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_key: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    audio_key: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    image_described: Mapped[bool] = mapped_column(Boolean, default=False)
    audio_transcribed: Mapped[bool] = mapped_column(Boolean, default=False)
    image_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    audio_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    time: Mapped[int] = mapped_column(BigInteger, default=get_utc_timestamp_int)
    data_points: Mapped[list["Data"]] = relationship(
        lazy=True,
        back_populates="note",
        cascade="all, delete-orphan"
    )

    links: Mapped[list["Link"]] = relationship(
        lazy=True,
        back_populates="note",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"Note(id={self.id!r}, user_id={self.user_id!r}, time={self.time.isoformat()})"


class MetricOrigin(str, Enum):
    text = 'text'
    audio_text = 'audio_text'
    img_desc = 'img_desc'
    img_text = 'img_text'


class Metrics(Base):
    __tablename__ = "metrics"
    __table_args__ = (
        UniqueConstraint('name', name='uq_metrics_name'),
        Index('idx_metric_name', 'name'),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(500), unique=True)
    tagged: Mapped[bool] = mapped_column(Boolean, default=False)
    tags: Mapped[List["Tag"]] = relationship(back_populates="metric_type",
                                                     cascade="all, delete-orphan",
                                                     lazy="select")


    data_points: Mapped[list["Data"]] = relationship(
        back_populates="metric_type",
        cascade="all, delete-orphan",
        lazy=True
    )
    schedules: Mapped[list["DataSchedule"]] = relationship(
        back_populates="metric_type",
        cascade="all, delete-orphan",
        lazy=True
    )
    def __repr__(self) -> str:
        return f"Metrics(id={self.id!r}, name={self.name!r}, tagged={self.tagged!r})"


class Data(Base):
    __tablename__ = "data"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    metrics_id: Mapped[int] = mapped_column(ForeignKey("metrics.id"))
    note_id: Mapped[int | None] = mapped_column(ForeignKey("note.id"), nullable=True)

    value: Mapped[float] = mapped_column(Numeric)
    units: Mapped[str | None] = mapped_column(String(100), nullable=True)

    time: Mapped[int] = mapped_column(BigInteger)

    origin: Mapped[MetricOrigin] = mapped_column(
        SQLEnum(MetricOrigin),
        nullable=False
    )

    metric_type: Mapped["Metrics"] = relationship(back_populates="data_points")

    note: Mapped["Note"] = relationship(back_populates="data_points")

    def __repr__(self) -> str:
        return (f"Data(id={self.id!r}, metric_id={self.metrics_id!r}, "
                f"value={self.value!r}, units={self.units!r}, origin={self.origin.value!r})")


class DataSchedule(Base):
    __tablename__ = "data_schedule"
    __table_args__ = (
        UniqueConstraint('metrics_id', name='uq_metric_schedule'),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    metrics_id: Mapped[int] = mapped_column(ForeignKey("metrics.id"), unique=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))

    recurrence_schedule: Mapped[str] = mapped_column(String(50))
    target_value: Mapped[float | None] = mapped_column(Numeric, nullable=True)  # Renamed to target_value for clarity
    units: Mapped[str | None] = mapped_column(String(100), nullable=True)

    metric_type: Mapped["Metrics"] = relationship(backref="schedules")

    def __repr__(self) -> str:
        return (f"DataSchedule(metric_id={self.metrics_id!r}, "
                f"schedule={self.recurrence_schedule!r}, target={self.target_value!r})")


class Link(Base):
    __tablename__ = "link"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    note_id: Mapped[int | None] = mapped_column(ForeignKey("note.id"), nullable=True)

    value: Mapped[str] = mapped_column(String(1000))
    description: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    time: Mapped[int] = mapped_column(BigInteger)

    origin: Mapped[MetricOrigin] = mapped_column(
        SQLEnum(MetricOrigin),
        nullable=False
    )

    note: Mapped["Note"] = relationship(back_populates="links")

    def __repr__(self) -> str:
        return (f"Link(id={self.id!r},  "
                f"value={self.value!r}, description={self.description!r}, origin={self.origin.value!r})")


secret_arn = os.getenv(Env.db_secret_arn)
db_endpoint = os.getenv(Env.db_endpoint)
db_name = os.getenv(Env.db_name)
db_port = 3306

secrets_client = boto3.client('secretsmanager')


def begin_session():
    secret_response = secrets_client.get_secret_value(SecretId=secret_arn)
    secret_dict = json.loads(secret_response['SecretString'])

    username = secret_dict['username']
    password = secret_dict['password']
    connection_string = (
        f'mysql+mysqlconnector://{username}:{password}@{db_endpoint}:{db_port}/{db_name}'
    )

    engine = create_engine(connection_string, pool_recycle=300)

    return sessionmaker(bind=engine)()
