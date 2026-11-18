
from pathlib import Path
from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile
)
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.database import get_db
from database.models import Game, Question
from backend.services.document_reader import read_document
from backend.services.question_generator import QuestionGenerator
from backend.services.question_storage import save_questions


router = APIRouter(
    prefix="/api/questions",
    tags=["Preguntas"]
)

BASE_DIR = Path(__file__).resolve().parents[2]
UPLOAD_DIR = BASE_DIR / "storage" / "uploads"

MAX_FILE_SIZE = 10 * 1024 * 1024


class QuestionUpdate(BaseModel):
    text: str = Field(min_length=1)
    option_a: str = Field(min_length=1)
    option_b: str = Field(min_length=1)
    option_c: str = Field(min_length=1)
    option_d: str = Field(min_length=1)
    correct_option: str = Field(pattern="^[ABCD]$")
    explanation: str = ""


@router.post("/generate")
async def generate_questions(
    game_id: int = Form(...),
    number: int = Form(...),
    difficulty: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):

    if not 1 <= number <= 50:
        raise HTTPException(
            status_code=400,
            detail="El número debe estar entre 1 y 50."
        )

    difficulty_map = {
        "facil": "facil",
        "fácil": "facil",
        "media": "media",
        "dificil": "dificil",
        "difícil": "dificil"
    }

    difficulty = difficulty_map.get(
        difficulty.strip().lower()
    )

    if not difficulty:
        raise HTTPException(
            status_code=400,
            detail="Dificultad no válida."
        )

    game = db.query(Game).filter(
        Game.id == game_id
    ).first()

    if game is None:
        raise HTTPException(
            status_code=404,
            detail="Juego no encontrado."
        )

    extension = Path(file.filename or "").suffix.lower()

    if extension not in (".pdf", ".docx"):
        raise HTTPException(
            status_code=400,
            detail="Solo se permiten archivos PDF y DOCX."
        )

    content = await file.read(MAX_FILE_SIZE + 1)

    if not content:
        raise HTTPException(
            status_code=400,
            detail="El documento está vacío."
        )

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="El archivo supera el límite de 10 MB."
        )

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    temporary_file = UPLOAD_DIR / (
        f"{uuid4().hex}{extension}"
    )

    try:
        temporary_file.write_bytes(content)

        document_text = read_document(
            str(temporary_file)
        )

        generator = QuestionGenerator()

        questions = await generator.generate_questions(
            document_text=document_text,
            number=number,
            difficulty=difficulty
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception as error:
        print(f"ERROR GENERANDO PREGUNTAS: {error}")

        raise HTTPException(
            status_code=502,
            detail="No se pudieron generar las preguntas. "
                   "Comprueba la disponibilidad de los proveedores IA."
        )

    finally:
        temporary_file.unlink(missing_ok=True)

    try:
        saved_questions = save_questions(
            db=db,
            game_id=game_id,
            questions=questions
        )

        # Las preguntas quedan disponibles directamente.
        for question in saved_questions:
            question.verified = True

        db.commit()

    except Exception as error:
        db.rollback()
        print(f"ERROR GUARDANDO PREGUNTAS: {error}")

        raise HTTPException(
            status_code=500,
            detail="No se pudieron guardar las preguntas."
        )

    return {
        "message": "Preguntas generadas correctamente.",
        "game_id": game_id,
        "generated": len(saved_questions),
        "status": "disponibles",
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
            for question in saved_questions
        ]
    }


@router.get("/pending/{game_id}")
def get_pending_questions(
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
        Question.verified == False
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


@router.put("/{question_id}")
def update_question(
    question_id: int,
    data: QuestionUpdate,
    db: Session = Depends(get_db)
):

    question = db.query(Question).filter(
        Question.id == question_id
    ).first()

    if question is None:
        raise HTTPException(
            status_code=404,
            detail="Pregunta no encontrada."
        )

    question.text = data.text.strip()
    question.option_a = data.option_a.strip()
    question.option_b = data.option_b.strip()
    question.option_c = data.option_c.strip()
    question.option_d = data.option_d.strip()
    question.correct_option = data.correct_option
    question.explanation = data.explanation.strip()

    try:
        db.commit()
        db.refresh(question)

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="No se pudo actualizar la pregunta."
        )

    return {
        "message": "Pregunta actualizada correctamente.",
        "question_id": question.id,
        "verified": question.verified
    }


@router.patch("/{question_id}/approve")
def approve_question(
    question_id: int,
    db: Session = Depends(get_db)
):

    question = db.query(Question).filter(
        Question.id == question_id
    ).first()

    if question is None:
        raise HTTPException(
            status_code=404,
            detail="Pregunta no encontrada."
        )

    if question.verified:
        raise HTTPException(
            status_code=400,
            detail="La pregunta ya está aprobada."
        )

    required_fields = [
        question.text,
        question.option_a,
        question.option_b,
        question.option_c,
        question.option_d
    ]

    if any(
        not value or not value.strip()
        for value in required_fields
    ):
        raise HTTPException(
            status_code=400,
            detail="La pregunta debe tener enunciado y cuatro respuestas."
        )

    if question.correct_option not in ("A", "B", "C", "D"):
        raise HTTPException(
            status_code=400,
            detail="La respuesta correcta debe ser A, B, C o D."
        )

    question.verified = True

    try:
        db.commit()
        db.refresh(question)

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="No se pudo aprobar la pregunta."
        )

    return {
        "message": "Pregunta aprobada correctamente.",
        "question_id": question.id,
        "verified": question.verified
    }
