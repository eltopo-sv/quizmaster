
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.database import get_db
from database.models import Game, Question


router = APIRouter(
    prefix="/api/questions",
    tags=["Preguntas"]
)


@router.get("/approved/{game_id}")
def get_approved_questions(
    game_id: int,
    db: Session = Depends(get_db)
):
    game = db.query(Game).filter(
        Game.id == game_id
    ).first()

    if game is None:
        raise HTTPException(
            status_code=404,
            detail="Juego no encontrado."
        )

    questions = db.query(Question).filter(
        Question.game_id == game_id,
        Question.verified == True
    ).order_by(Question.id.asc()).all()

    return {
        "game_id": game_id,
        "total": len(questions),
        "questions": [
            {
                "id": question.id,
                "text": question.text,
                "option_a": question.option_a,
                "option_b": question.option_b,
                "option_c": question.option_c,
                "option_d": question.option_d,
                "correct_option": question.correct_option,
                "explanation": question.explanation,
                "verified": question.verified
            }
            for question in questions
        ]
    }


@router.get("/all/{game_id}")
def get_all_questions(
    game_id: int,
    db: Session = Depends(get_db)
):
    game = db.query(Game).filter(
        Game.id == game_id
    ).first()

    if game is None:
        raise HTTPException(
            status_code=404,
            detail="Juego no encontrado."
        )

    questions = db.query(Question).filter(
        Question.game_id == game_id
    ).order_by(Question.id.asc()).all()

    return {
        "game_id": game_id,
        "total": len(questions),
        "questions": [
            {
                "id": question.id,
                "text": question.text,
                "option_a": question.option_a,
                "option_b": question.option_b,
                "option_c": question.option_c,
                "option_d": question.option_d,
                "correct_option": question.correct_option,
                "explanation": question.explanation,
                "verified": question.verified
            }
            for question in questions
        ]
    }
