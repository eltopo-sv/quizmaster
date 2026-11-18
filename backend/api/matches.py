
import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.database import get_db
from database.models import (
    Game,
    Question,
    Match,
    Team,
    MatchTeam,
    MatchAnswer
)


router = APIRouter(
    prefix="/api/matches",
    tags=["Partidas"]
)


# ==========================================
# MODELOS DE DATOS
# ==========================================

class TeamInput(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    avatar: str = Field(default="🦁", max_length=200)
    color: str = Field(default="#6C5CE7", max_length=30)


class MatchCreate(BaseModel):
    game_id: int
    teams: list[TeamInput] = Field(min_length=3, max_length=10)


class AnswerInput(BaseModel):
    selected_option: str = Field(min_length=1, max_length=1)
    targeted_team_ids: list[int] = Field(min_length=1)


# ==========================================
# FUNCIONES AUXILIARES
# ==========================================

def get_match_or_404(match_id: int, db: Session):
    match = db.query(Match).filter(
        Match.id == match_id
    ).first()

    if match is None:
        raise HTTPException(
            status_code=404,
            detail="Partida no encontrada."
        )

    return match


def get_match_teams(match_id: int, db: Session):
    return db.query(MatchTeam).filter(
        MatchTeam.match_id == match_id
    ).order_by(MatchTeam.position.asc()).all()


def get_team_name(match_team, db: Session):
    if match_team.display_name:
        return match_team.display_name

    team = db.query(Team).filter(
        Team.id == match_team.team_id
    ).first()

    return team.name if team else "Equipo"


def get_team_avatar(match_team, db: Session):
    if match_team.avatar:
        return match_team.avatar

    team = db.query(Team).filter(
        Team.id == match_team.team_id
    ).first()

    return team.avatar if team else "🦁"


def get_team_color(match_team, db: Session):
    if match_team.color:
        return match_team.color

    team = db.query(Team).filter(
        Team.id == match_team.team_id
    ).first()

    return team.color if team else "#6C5CE7"


def serialize_team(match_team, db: Session):
    return {
        "id": match_team.team_id,
        "name": get_team_name(match_team, db),
        "avatar": get_team_avatar(match_team, db),
        "color": get_team_color(match_team, db),
        "score": match_team.score,
        "position": match_team.position
    }


def get_questions(match_id: int, db: Session):
    match = get_match_or_404(match_id, db)

    return db.query(Question).filter(
        Question.game_id == match.game_id
    ).order_by(Question.id.asc()).all()


# ==========================================
# CREAR PARTIDA
# ==========================================

@router.post("/")
def create_match(
    data: MatchCreate,
    db: Session = Depends(get_db)
):
    game = db.query(Game).filter(
        Game.id == data.game_id
    ).first()

    if game is None:
        raise HTTPException(
            status_code=404,
            detail="Juego no encontrado."
        )

    questions = db.query(Question).filter(
        Question.game_id == data.game_id
    ).order_by(Question.id.asc()).all()

    if not questions:
        raise HTTPException(
            status_code=400,
            detail="Este juego todavía no tiene preguntas."
        )

    names = [team.name.strip().casefold() for team in data.teams]

    if any(not name for name in names):
        raise HTTPException(
            status_code=400,
            detail="Todos los equipos deben tener un nombre."
        )

    if len(names) != len(set(names)):
        raise HTTPException(
            status_code=400,
            detail="Los nombres de los equipos no pueden repetirse."
        )

    try:
        match = Match(
            game_id=data.game_id,
            status="in_progress",
            current_question=0,
            current_team_position=0
        )

        db.add(match)
        db.flush()

        created_teams = []

        for position, team_data in enumerate(data.teams):
            clean_name = team_data.name.strip()

            # El nombre interno evita conflictos con la restricción
            # de unicidad global de Team.name.
            internal_name = (
                f"{clean_name[:110]}__m{match.id}_t{position}"
            )

            team = Team(
                name=internal_name,
                avatar=team_data.avatar,
                color=team_data.color,
                active=True
            )

            db.add(team)
            db.flush()

            match_team = MatchTeam(
                match_id=match.id,
                team_id=team.id,
                display_name=clean_name,
                avatar=team_data.avatar,
                color=team_data.color,
                score=100,
                position=position
            )

            db.add(match_team)

            created_teams.append({
                "id": team.id,
                "name": clean_name,
                "avatar": team_data.avatar,
                "color": team_data.color,
                "score": 100,
                "position": position
            })

        db.commit()
        db.refresh(match)

        return {
            "message": "Partida creada correctamente.",
            "match_id": match.id,
            "game_id": game.id,
            "game_title": game.title,
            "status": match.status,
            "total_questions": len(questions),
            "teams": created_teams
        }

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="No se pudo crear la partida."
        )


# ==========================================
# CONSULTAR PARTIDA Y CLASIFICACIÓN
# ==========================================

@router.get("/{match_id}")
def get_match(
    match_id: int,
    db: Session = Depends(get_db)
):
    match = get_match_or_404(match_id, db)

    game = db.query(Game).filter(
        Game.id == match.game_id
    ).first()

    match_teams = get_match_teams(match_id, db)
    questions = get_questions(match_id, db)

    teams = [
        serialize_team(item, db)
        for item in match_teams
    ]

    ranking = sorted(
        teams,
        key=lambda team: (-team["score"], team["position"])
    )

    current_team = None

    if (
        match.status == "in_progress"
        and match.current_team_position < len(match_teams)
    ):
        current_team = serialize_team(
            match_teams[match.current_team_position],
            db
        )

    return {
        "match_id": match.id,
        "game_id": match.game_id,
        "game_title": game.title if game else "",
        "status": match.status,
        "current_question": match.current_question,
        "current_team_position": match.current_team_position,
        "total_questions": len(questions),
        "current_team": current_team,
        "teams": teams,
        "ranking": ranking,
        "winner": ranking[0] if match.status == "completed" and ranking else None
    }


# ==========================================
# CONSULTAR PREGUNTA ACTUAL
# ==========================================

@router.get("/{match_id}/current-question")
def get_current_question(
    match_id: int,
    db: Session = Depends(get_db)
):
    match = get_match_or_404(match_id, db)

    if match.status != "in_progress":
        raise HTTPException(
            status_code=400,
            detail="La partida no está en curso."
        )

    questions = get_questions(match_id, db)
    match_teams = get_match_teams(match_id, db)

    if match.current_question >= len(questions):
        raise HTTPException(
            status_code=400,
            detail="No quedan preguntas."
        )

    if match.current_team_position >= len(match_teams):
        raise HTTPException(
            status_code=500,
            detail="No se ha podido determinar el equipo del turno."
        )

    question = questions[match.current_question]
    active_team = match_teams[match.current_team_position]

    return {
        "match_id": match.id,
        "question_number": match.current_question + 1,
        "total_questions": len(questions),
        "active_team": serialize_team(active_team, db),
        "question": {
            "id": question.id,
            "text": question.text,
            "option_a": question.option_a,
            "option_b": question.option_b,
            "option_c": question.option_c,
            "option_d": question.option_d,
            "image_path": question.image_path
        },
        "available_targets": [
            serialize_team(team, db)
            for team in match_teams
            if team.team_id != active_team.team_id
        ]
    }


# ==========================================
# RESPONDER PREGUNTA Y CALCULAR PUNTOS
# ==========================================

@router.post("/{match_id}/answer")
def submit_answer(
    match_id: int,
    data: AnswerInput,
    db: Session = Depends(get_db)
):
    match = get_match_or_404(match_id, db)

    if match.status != "in_progress":
        raise HTTPException(
            status_code=400,
            detail="La partida ya ha terminado."
        )

    questions = get_questions(match_id, db)
    match_teams = get_match_teams(match_id, db)

    if match.current_question >= len(questions):
        raise HTTPException(
            status_code=400,
            detail="No quedan preguntas."
        )

    if match.current_team_position >= len(match_teams):
        raise HTTPException(
            status_code=500,
            detail="No se ha podido determinar el equipo del turno."
        )

    question = questions[match.current_question]
    active_team = match_teams[match.current_team_position]

    selected_option = data.selected_option.strip().upper()

    if selected_option not in ["A", "B", "C", "D"]:
        raise HTTPException(
            status_code=400,
            detail="La respuesta debe ser A, B, C o D."
        )

    # El equipo activo nunca puede ser objetivo.
    target_ids = data.targeted_team_ids

    if len(target_ids) != len(set(target_ids)):
        raise HTTPException(
            status_code=400,
            detail="No se pueden repetir equipos objetivo."
        )

    if active_team.team_id in target_ids:
        raise HTTPException(
            status_code=400,
            detail="No puedes seleccionarte a ti mismo como objetivo."
        )

    available_team_ids = {
        team.team_id
        for team in match_teams
    }

    if not set(target_ids).issubset(available_team_ids):
        raise HTTPException(
            status_code=400,
            detail="Has seleccionado un equipo que no pertenece a esta partida."
        )

    # Comprobar que la pregunta no se haya respondido previamente.
    previous_answer = db.query(MatchAnswer).filter(
        MatchAnswer.match_id == match.id,
        MatchAnswer.question_id == question.id
    ).first()

    if previous_answer:
        raise HTTPException(
            status_code=400,
            detail="Esta pregunta ya ha sido respondida."
        )

    is_correct = (
        selected_option == question.correct_option.strip().upper()
    )

    # Calcular y actualizar los puntos de todos los equipos.
    score_changes = []

    for match_team in match_teams:

        if match_team.team_id in target_ids:
            points = 10 if is_correct else -10
        else:
            points = 5

        match_team.score += points

        score_changes.append({
            "team_id": match_team.team_id,
            "team_name": get_team_name(match_team, db),
            "points": points,
            "new_score": match_team.score
        })

    # Registrar la respuesta y los equipos objetivo.
    answer = MatchAnswer(
        match_id=match.id,
        question_id=question.id,
        team_id=active_team.team_id,
        selected_option=selected_option,
        is_correct=is_correct,
        points_awarded=5,
        targeted_team_ids=json.dumps(target_ids)
    )

    db.add(answer)

    # Avanzar a la siguiente pregunta y al siguiente equipo.
    match.current_question += 1

    match.current_team_position = (
        match.current_team_position + 1
    ) % len(match_teams)

    # Finalizar cuando se hayan respondido todas las preguntas.
    finished = match.current_question >= len(questions)

    if finished:
        match.status = "completed"

    db.commit()

    # Preparar clasificación actualizada.
    db.refresh(match)

    for match_team in match_teams:
        db.refresh(match_team)

    ranking = sorted(
        [
            serialize_team(team, db)
            for team in match_teams
        ],
        key=lambda team: (-team["score"], team["position"])
    )

    return {
        "message": "Respuesta registrada correctamente.",
        "question_id": question.id,
        "active_team": get_team_name(active_team, db),
        "selected_option": selected_option,
        "is_correct": is_correct,
        "correct_option": question.correct_option,
        "explanation": question.explanation,
        "score_changes": score_changes,
        "ranking": ranking,
        "question_number": match.current_question,
        "total_questions": len(questions),
        "status": match.status,
        "finished": finished,
        "winner": ranking[0] if finished and ranking else None
    }


# ==========================================
# CARGAR TODAS LAS PREGUNTAS
# ==========================================

@router.get("/{match_id}/questions")
def get_match_questions(
    match_id: int,
    db: Session = Depends(get_db)
):
    match = get_match_or_404(match_id, db)

    questions = get_questions(match_id, db)

    return {
        "match_id": match.id,
        "total": len(questions),
        "questions": [
            {
                "id": question.id,
                "text": question.text,
                "option_a": question.option_a,
                "option_b": question.option_b,
                "option_c": question.option_c,
                "option_d": question.option_d,
                "image_path": question.image_path
            }
            for question in questions
        ]
    }
