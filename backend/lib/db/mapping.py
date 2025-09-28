import uuid
from datetime import datetime
from sqlalchemy import (
    BigInteger,
    Boolean,
    String,
    Text,
    ForeignKey,
    Numeric,
    Table,
    Column
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship
)

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

    messages: Mapped[list["Message"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, name={self.name!r})"


class Message(Base):
    __tablename__ = "message"

    # Columns
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_key: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    audio_key: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    image_described: Mapped[bool] = mapped_column(Boolean, default=False)
    audio_transcribed: Mapped[bool] = mapped_column(Boolean, default=False)
    image_text:  Mapped[str | None] = mapped_column(Text, nullable=True)
    audio_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    from_user: Mapped[bool] = mapped_column(Boolean, default=False)
    response_to_id: Mapped[int | None] = mapped_column(ForeignKey("message.id"), nullable=True)
    time: Mapped[datetime] = mapped_column(default=datetime.utcnow)


    user: Mapped["User"] = relationship(back_populates="messages")

    original_message: Mapped["Message"] = relationship(
        remote_side=[id],
        back_populates="responses",
        lazy="joined"
    )

    responses: Mapped[list["Message"]] = relationship(back_populates="original_message")

    metrics: Mapped[list["Metrics"]] = relationship(
        back_populates="message",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"Message(id={self.id!r}, user_id={self.user_id!r}, time={self.time.isoformat()})"


# todo add recurrent config
class Metrics(Base):
    __tablename__ = "metrics"

    # Columns
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    normalized_name: Mapped[str] = mapped_column(String(1000))
    original_name: Mapped[str] = mapped_column(String(1000))
    value: Mapped[float] = mapped_column(Numeric)
    units: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tagged: Mapped[bool] = mapped_column(Boolean, default=False)
    message_id: Mapped[int | None] = mapped_column(ForeignKey("message.id"), nullable=True)
    is_recurrent: Mapped[bool] = mapped_column(Boolean, default=False)
    recurrence_schedule: Mapped[str | None] = mapped_column(String(50), nullable=True)
    target_value: Mapped[float | None] = mapped_column(Numeric, nullable=True)

    message: Mapped["Message"] = relationship(back_populates="metrics")

    tags: Mapped[list[str]] = relationship(
        secondary=metrics_tags_association,
        primaryjoin=metrics_tags_association.c.metrics_id == id,
        secondaryjoin=metrics_tags_association.c.metrics_id == id,
        viewonly=True,
        lazy="joined"
    )

    def __repr__(self) -> str:
        return f"Metrics(id={self.id!r}, name={self.normalized_name!r}, value={self.value!r})"