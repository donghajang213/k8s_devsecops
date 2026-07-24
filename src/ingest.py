from sqlalchemy.dialects.postgresql import insert

from src.db import SessionLocal, ProgramTable
from src.models import Program
from src.clients.bizinfo import fetch_bizinfo_all, bizinfo_to_program
from src.clients.mss import fetch_mss_all, mss_to_program

# insert 시도했다가 이미 있는 (source, source_id)면 이 컬럼들만 덮어쓴다.
# 그대로 두면 안 바뀌는 값(예: source, source_id 자체)은 넣지 않는다.
UPDATE_COLUMNS = [
    "title",
    "target",
    "start_date",
    "end_date",
    "description",
    "jurisdiction_org",
    "executing_org",
    "category",
    "source_url",
]


def upsert_program(session, program: Program) -> None:
    data = program.model_dump()
    # ProgramTable.id는 PK인데 Program 모델엔 없는 필드라 여기서 직접 만들어준다.
    data["id"] = f"{program.source}:{program.source_id}"

    stmt = insert(ProgramTable).values(**data)
    stmt = stmt.on_conflict_do_update(
        index_elements=["source", "source_id"],
        set_={col: stmt.excluded[col] for col in UPDATE_COLUMNS},
    )
    session.execute(stmt)


def ingest():
    programs: list[Program] = []
    programs += [bizinfo_to_program(raw) for raw in fetch_bizinfo_all()]
    programs += [mss_to_program(raw) for raw in fetch_mss_all()]

    with SessionLocal() as session:
        for program in programs:
            upsert_program(session, program)
        session.commit()

    print(f"{len(programs)}건 적재 완료")


if __name__ == "__main__":
    ingest()
