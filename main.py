
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from database.database import Base, engine
from database import models

from backend.api.games import router as games_router
from backend.api.questions import router as questions_router
from backend.api.approved_questions import router as approved_questions_router
from backend.api.matches import router as matches_router


BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"


# ==========================================
# INICIALIZAR BASE DE DATOS
# ==========================================

Base.metadata.create_all(bind=engine)


# ==========================================
# APLICACIÓN FASTAPI
# ==========================================

app = FastAPI(
    title="QUIZMASTER",
    description="Plataforma de juegos educativos por equipos",
    version="1.0.0"
)


# ==========================================
# REGISTRAR RUTAS API
# ==========================================

app.include_router(games_router)
app.include_router(questions_router)
app.include_router(approved_questions_router)
app.include_router(matches_router)


# ==========================================
# ARCHIVOS ESTÁTICOS
# ==========================================

app.mount(
    "/static",
    StaticFiles(directory=FRONTEND_DIR),
    name="static"
)


# ==========================================
# ESTADO DE LA APLICACIÓN
# ==========================================

@app.get("/api/status")
def status():
    return {
        "app": "QUIZMASTER",
        "status": "funcionando",
        "database": "conectada"
    }


# ==========================================
# PORTADA
# ==========================================

@app.get("/")
def home():
    return FileResponse(FRONTEND_DIR / "index.html")


# ==========================================
# PANEL DEL PROFESOR
# ==========================================

@app.get("/teacher")
def teacher_panel():
    return FileResponse(FRONTEND_DIR / "teacher.html")
