# Docker 컨테이너화 체크리스트

FastAPI(또는 비슷한 파이썬 앱) 하나를 컨테이너화할 때 항상 고려하는 것들.

## Dockerfile

```dockerfile
# -slim: 이미지 크기와 공격 표면을 줄이기 위해. 버전 고정: 재현성과 예기치 않은 변경 방지
FROM python:3.14-slim

WORKDIR /app

# 의존성 파일만 먼저 복사 - 소스코드만 바뀌었을 때 uv sync 레이어를 캐시로 재사용하기 위해
COPY pyproject.toml uv.lock .
RUN pip install uv && uv sync --frozen

# 소스코드는 의존성 설치 이후에 복사
COPY src/ ./src/

EXPOSE 8000

# non-root 사용자로 실행 (root 권한 최소화)
RUN useradd --create-home appuser
USER appuser

# exec form(리스트) - 컨테이너의 PID 1로 직접 실행되어 SIGTERM을 앱이 바로 받게 함
# --host 0.0.0.0: 컨테이너 내부에서만 듣는 127.0.0.1이 아니라, 컨테이너 밖에서도 접근 가능하게
CMD ["uv", "run", "uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 핵심 포인트

1. **베이스 이미지에 버전을 고정한다** (`python:3.14-slim`, `latest` 금지) — 재현성 + 예기치 않은 변경 방지. `-slim`류의 경량 이미지를 쓰면 이미지 크기와 공격 표면(불필요한 패키지)이 줄어든다.

2. **레이어 캐싱 순서**: 의존성 파일(`pyproject.toml`, `uv.lock`) → 의존성 설치 → 소스코드 복사 순으로 배치한다. Docker는 각 명령을 레이어로 캐싱하는데, 앞선 레이어가 안 바뀌면 캐시를 재사용한다. 소스코드를 먼저 복사하면 코드 한 줄만 고쳐도 그 뒤의 의존성 설치까지 매번 새로 실행되어 빌드가 느려진다.

3. **non-root 사용자로 실행한다**: 컨테이너는 호스트와 커널을 공유하기 때문에, 컨테이너 탈출(escape) 취약점이 터지면 root로 실행 중이던 컨테이너는 호스트에서도 root급 피해를 줄 수 있다. `RUN useradd ...` + `USER appuser`로 최소 권한을 적용한다. 단, 의존성 설치(`RUN uv sync`)는 `USER` 전환 전에 해야 root 권한으로 정상 설치된다 — 순서가 중요하다.

4. **`CMD`는 exec form(리스트)으로 쓴다**: `CMD ["uv", "run", ...]`처럼 리스트로 쓰면 이 프로세스가 컨테이너의 PID 1로 직접 실행된다. 문자열로 쓰면(`CMD uv run ...`) 내부적으로 `/bin/sh -c "..."`로 감싸져서 셸이 PID 1이 되고, K8s가 파드 종료 시 보내는 `SIGTERM`을 셸이 받아버려 앱까지 제대로 전달 안 될 수 있다 (graceful shutdown 실패 → 강제 종료까지 대기).

5. **`EXPOSE`는 문서화일 뿐 실제 포트를 열지 않는다.** 실제로 호스트에서 접근 가능하게 하려면 `docker run -p` 또는 compose의 `ports:`가 따로 필요하다.

6. **Dockerfile 안에서 줄 끝에 `#` 주석을 달면 안 된다** — Docker는 `#`가 줄의 맨 앞에 있을 때만 주석으로 인식한다. 명령어 뒤에 붙이면 그 텍스트가 명령어의 일부로 해석되어 에러가 난다 (특히 `CMD`처럼 JSON 배열 형태인 곳에서 문제가 됨). 설명은 반드시 별도 줄에 쓴다.

## `.dockerignore`

```
.git
.venv
.env
__pycache__
*.pyc
```

`.gitignore`와 개념은 같지만 대상이 다르다 — `docker build` 시 Docker 데몬에 넘기는 파일 목록(build context)에서 제외한다. `COPY . .`처럼 폭넓게 복사하는 줄이 있으면 `.env`가 그대로 이미지 레이어에 박히는데, 이미지를 나중에 지워도 레이어 히스토리엔 남아있어서 `docker history`로 복구 가능하다. 이미지를 레지스트리에 올리는 순간 그 키가 노출된다. 지금 Dockerfile처럼 `COPY`를 필요한 파일만 콕 집어 쓰는 구조라면 당장은 위험하지 않아도, 나중에 `COPY . .`로 편의상 바꿀 실수에 대비한 안전망으로 항상 만들어둔다.

## docker-compose.yml과의 관계

- **Dockerfile**: 이미지 하나를 어떻게 만들지 정의 (빌드 레시피)
- **docker-compose.yml**: 여러 컨테이너를 어떻게 같이 띄우고 연결할지 정의 (오케스트레이션)

이미 만들어진 이미지(postgres, adminer 공식 이미지 등)만 쓸 거면 Dockerfile 없이 compose만으로 충분하다. 직접 만든 이미지를 쓰려면 compose 서비스에 `build: .`로 Dockerfile을 참조시킨다.

```yaml
services:
  api:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    environment:
      # 컨테이너끼리는 localhost가 아니라 서비스 이름으로 통신한다
      POSTGRES_HOST: db
      POSTGRES_PORT: 5432   # db 서비스의 컨테이너 "내부" 포트. 호스트에 매핑한 포트(예: 5433)와 다름
    depends_on:
      - db
```

`env_file`로 `.env`를 통째로 불러오고, `environment`로 일부 값만 오버라이드한다 (compose에서는 `environment`가 `env_file`보다 우선순위가 높다). 특히 DB 접속 정보에서 호스트/포트를 착각하기 쉬운데 — 호스트(내 PC)에서 접근할 땐 `docker-compose.yml`의 `ports:` 왼쪽 값(호스트 포트)을 쓰고, 컨테이너끼리 통신할 땐 오른쪽 값(컨테이너 내부 포트)과 서비스 이름을 쓴다.

## 실행 후 확인

```
docker compose up -d --build
docker ps                                    # 컨테이너들이 다 떠 있는지
docker exec <컨테이너이름> whoami             # non-root로 잘 실행되는지 (appuser가 나와야 정상)
curl http://localhost:8000/programs           # 실제 API 응답 확인
```
