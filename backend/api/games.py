
import os
import secrets
from pathlib import Path

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.database import get_db
from database.models import Game


# Cargar el archivo .env situado en la raíz del proyecto
PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

router = APIRouter(prefix="/api/games", tags=["Juegos"])


class GameCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    topic: str = Field(default="", max_length=150)
    difficulty: str = Field(default="Media", max_length=30)


def verify_admin_password(
    admin_password: str | None = Header(
        default=None,
        alias="X-Admin-Password"
    )
):
    configured_password = os.getenv("QUIZMASTER_ADMIN_PASSWORD")

    if not configured_password:
        raise HTTPException(
            status_code=503,
            detail="La contraseña de administración no está configurada."
        )

    if not admin_password or not secrets.compare_digest(
        admin_password,
        configured_password
    ):
        raise HTTPException(
            status_code=401,
            detail="Contraseña de administración incorrecta."
        )

    return True


@router.get("/")
def list_games(db: Session = Depends(get_db)):
    games = db.query(Game).order_by(Game.created_at.desc()).all()

    return [
        {
            "id": game.id,
            "title": game.title,
            "topic": game.topic,
            "difficulty": game.difficulty,
            "questions_count": len(game.questions)
        }
        for game in games
    ]


@router.post("/")
def create_game(
    data: GameCreate,
    db: Session = Depends(get_db),
    authorized: bool = Depends(verify_admin_password)
):
    game = Game(
        title=data.title.strip(),
        topic=data.topic.strip(),
        difficulty=data.difficulty
    )

    if not game.title:
        raise HTTPException(
            status_code=400,
            detail="El título es obligatorio"
        )

    db.add(game)
    db.commit()
    db.refresh(game)

    return {
        "message": "Juego creado correctamente",
        "id": game.id,
        "title": game.title
    }


@router.delete("/{game_id}")
def delete_game(
    game_id: int,
    db: Session = Depends(get_db),
    authorized: bool = Depends(verify_admin_password)
):
    game = db.query(Game).filter(Game.id == game_id).first()

    if game is None:
        raise HTTPException(
            status_code=404,
            detail="Juego no encontrado"
        )

    db.delete(game)
    db.commit()

    return {"message": "Juego eliminado correctamente"}
