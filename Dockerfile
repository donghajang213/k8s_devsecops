# -slim: 이미지 크기와 공격 표면을 줄이기 위해. 버전 고정: 재현성과 예기치 않은 변경 방지
FROM python:3.14-slim

WORKDIR /app

# 의존성 파일만 먼저 복사 - 소스코드만 바뀌었을 때 uv sync 레이어를 캐시로 재사용하기 위해
COPY pyproject.toml uv.lock .
RUN pip install uv && uv sync --frozen

# 소스코드는 의존성 설치 이후에 복사
COPY src/ ./src/
COPY alembic.ini .
COPY alembic/ ./alembic/

EXPOSE 8000

# non-root 사용자로 실행 (root 권한 최소화)
RUN useradd --create-home appuser
USER appuser

# exec form(리스트) - 컨테이너의 PID 1로 직접 실행되어 SIGTERM을 앱이 바로 받게 함
# --host 0.0.0.0: 컨테이너 내부에서만 듣는 127.0.0.1이 아니라, 컨테이너 밖에서도 접근 가능하게
CMD ["uv", "run", "uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]

