
from sqlalchemy.orm import Session

from database.models import Question


def save_questions(
    db: Session,
    game_id: int,
    questions: list
) -> list:

    if not questions:
        raise ValueError("No hay preguntas para guardar.")

    new_questions = []

    try:
        for item in questions:

            question = Question(
                game_id=game_id,
                text=item["text"],
                image_path=None,
                option_a=item["option_a"],
                option_b=item["option_b"],
                option_c=item["option_c"],
                option_d=item["option_d"],
                correct_option=item["correct_option"],
                explanation=item["explanation"],
                verified=False
            )

            new_questions.append(question)

        db.add_all(new_questions)
        db.commit()

        return new_questions

    except Exception:
        db.rollback()
        raise
