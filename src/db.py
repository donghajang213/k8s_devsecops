 # SQLAlchemy 모델, DB 연결

from sqlalchemy import create_engine, Column, String, Date, UniqueConstraint
from sqlalchemy.orm import declarative_base, sessionmaker

from src.config import (
    POSTGRES_USER,
    POSTGRES_PASSWORD,
    POSTGRES_HOST,
    POSTGRES_PORT,
    POSTGRES_DB,
)

DATABASE_URL = (
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class ProgramTable(Base):
    __tablename__ = "programs"

    id = Column(String, primary_key=True)  # 예: f"{source}:{source_id}" 조합, 또는 별도 UUID
    source = Column(String, nullable=False)
    source_id = Column(String, nullable=False)
    title = Column(String, nullable=False)
    target = Column(String)
    start_date = Column(Date)
    end_date = Column(Date)
    description = Column(String)
    jurisdiction_org = Column(String)
    executing_org = Column(String)
    category = Column(String)
    source_url = Column(String)

    __table_args__ = (UniqueConstraint("source", "source_id"),)
