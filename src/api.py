from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from src.db import SessionLocal, ProgramTable
from src.models import Program

app = FastAPI()
Instrumentator().instrument(app).expose(app)   # /metrics 엔드포인트 노출 (Prometheus가 스크레이프)


@app.get("/programs", response_model=list[Program])
def list_programs():
    with SessionLocal() as session:
        return session.query(ProgramTable).all()
