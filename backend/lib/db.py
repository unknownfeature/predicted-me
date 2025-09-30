import json
import os
import uuid
from datetime import datetime, timezone
from enum import Enum
import boto3
from sqlalchemy import (
    BigInteger,
    Boolean,
    String,
    Text,
    ForeignKey,
    Numeric,
    Table,
    Column,
    Enum as SQLEnum,
    UniqueConstraint,
    Index,
    create_engine
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    sessionmaker
)

from shared.variables import Env
from .util import get_utc_timestamp_int


class Base(DeclarativeBase):
    pass


metrics_tags_association = Table(
    "metrics_tags",
    Base.metadata,
    Column("metrics_id", BigInteger, ForeignKey("metrics.id"), primary_key=True),
    Column("tag", String(500), primary_key=True)
)


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    external_id: Mapped[uuid.UUID] = mapped_column(unique=True, default=uuid.uuid4)
    name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    accepted_terms: Mapped[bool] = mapped_column(Boolean, default=False)
    parent_user_id: Mapped[int | None] = mapped_column(ForeignKey("user.id"), nullable=True)

    parent_user: Mapped["User"] = relationship(
        remote_side=[id],  # Specifies the local column to link to (the parent's ID)
        back_populates="child_users",
        lazy="joined"
    )

    child_users: Mapped[list["User"]] = relationship(back_populates="parent_user")

    notes: Mapped[list["Note"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, name={self.name!r})"


class Note(Base):
    __tablename__ = "note"

    Index(
        'ft_note_content',
        'text', 'image_text', 'image_description', 'audio_text',
        mysql_prefix='FULLTEXT',
        mysql_default_charset='utf8mb4'
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

    user: Mapped["User"] = relationship(back_populates="notes")

    data_points: Mapped[list["Data"]] = relationship(
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
    name: Mapped[str] = mapped_column(String(1000), unique=True)
    tagged: Mapped[bool] = mapped_column(Boolean, default=False)

    tags: Mapped[list[str]] = relationship(
        secondary=metrics_tags_association,
        primaryjoin=metrics_tags_association.c.metrics_id == id,
        secondaryjoin=metrics_tags_association.c.metrics_id == id,
        viewonly=True,
        lazy="joined"
    )
    data_points: Mapped[list["Data"]] = relationship(
        back_populates="metric_type",
        cascade="all, delete-orphan",
        lazy="select"
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

    #  default inherited from the note
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

    recurrence_schedule: Mapped[str] = mapped_column(String(50))
    target_value: Mapped[float | None] = mapped_column(Numeric, nullable=True)  # Renamed to target_value for clarity
    units: Mapped[str | None] = mapped_column(String(100), nullable=True)

    metric_type: Mapped["Metrics"] = relationship(backref="schedules")

    def __repr__(self) -> str:
        return (f"DataSchedule(metric_id={self.metrics_id!r}, "
                f"schedule={self.recurrence_schedule!r}, target={self.target_value!r})")


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
