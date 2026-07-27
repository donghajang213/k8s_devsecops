from fastapi import FastAPI

from src.db import SessionLocal, ProgramTable
from src.models import Program

app = FastAPI()


@app.get("/programs", response_model=list[Program])
def list_programs():
    with SessionLocal() as session:
        return session.query(ProgramTable).all()
