
from datetime import datetime

from sqlalchemy import (
    String,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.database import Base


class Game(Base):
    __tablename__ = "games"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    topic: Mapped[str] = mapped_column(String(150), default="")
    difficulty: Mapped[str] = mapped_column(String(30), default="Media")
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    questions: Mapped[list["Question"]] = relationship(
        back_populates="game",
        cascade="all, delete-orphan"
    )


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"))
    text: Mapped[str] = mapped_column(Text)
    image_path: Mapped[str] = mapped_column(String(500), default="")
    option_a: Mapped[str] = mapped_column(String(500))
    option_b: Mapped[str] = mapped_column(String(500))
    option_c: Mapped[str] = mapped_column(String(500))
    option_d: Mapped[str] = mapped_column(String(500))
    correct_option: Mapped[str] = mapped_column(String(1))
    explanation: Mapped[str] = mapped_column(Text, default="")
    verified: Mapped[bool] = mapped_column(Boolean, default=False)

    game: Mapped["Game"] = relationship(back_populates="questions")


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Nombre interno único para identificar el equipo.
    name: Mapped[str] = mapped_column(String(150), unique=True)

    avatar: Mapped[str] = mapped_column(
        String(200),
        default="default.png"
    )

    color: Mapped[str] = mapped_column(
        String(30),
        default="#6C5CE7"
    )

    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(primary_key=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"))

    status: Mapped[str] = mapped_column(
        String(30),
        default="preparing"
    )

    # Índice de la pregunta actual, empezando por cero.
    current_question: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    # Posición del equipo cuyo turno corresponde.
    current_team_position: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )


class MatchTeam(Base):
    __tablename__ = "match_teams"

    id: Mapped[int] = mapped_column(primary_key=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id"))
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))

    # Nombre visible en esta partida.
    display_name: Mapped[str] = mapped_column(
        String(100),
        default=""
    )

    avatar: Mapped[str] = mapped_column(
        String(200),
        default="🦁"
    )

    color: Mapped[str] = mapped_column(
        String(30),
        default="#6C5CE7"
    )

    score: Mapped[int] = mapped_column(Integer, default=100)
    position: Mapped[int] = mapped_column(Integer, default=0)


class MatchAnswer(Base):
    __tablename__ = "match_answers"

    id: Mapped[int] = mapped_column(primary_key=True)

    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id"))
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"))

    # Equipo que responde durante ese turno.
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))

    selected_option: Mapped[str] = mapped_column(
        String(1),
        default=""
    )

    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)

    # Puntos obtenidos por el equipo que responde.
    points_awarded: Mapped[int] = mapped_column(Integer, default=0)

    # IDs de los equipos seleccionados como objetivo.
    targeted_team_ids: Mapped[str] = mapped_column(
        Text,
        default="[]"
    )

    answered_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    # Una pregunta solo puede responderse una vez por partida.
    __table_args__ = (
        UniqueConstraint(
            "match_id",
            "question_id",
            name="uq_match_question"
        ),
    )
