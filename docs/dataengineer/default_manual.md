# 데이터 파이프라인 초기 세팅 체크리스트

새 데이터 소스를 API로 연동할 때마다 (환경/프로젝트와 무관하게) 항상 거치는 단계들을,
직접 따라 칠 수 있는 명령어와 함께 정리했다.
(프로젝트 자체를 처음 만드는 단계 — uv, gitignore, git/GitHub — 는 별도 글 참고)

## 1. 외부 API 연동

### 1-1. 패키지 설치

```
uv add requests python-dotenv
```

- `requests`: HTTP 요청(=API 호출)을 보내는 라이브러리
- `python-dotenv`: `.env` 파일에 적어둔 값을 파이썬 코드에서 읽어올 수 있게 해주는 라이브러리

### 1-2. API 키 발급받고 `.env`에 저장

공공데이터포털이나 오픈API를 제공하는 사이트에서 회원가입 → 활용신청을 하면 API 키(인증키)를 이메일 또는 마이페이지로 받는다.

이 키는 **절대 코드에 직접 쓰지 않는다.** 코드에 박아두면 GitHub에 그대로 올라가서 누구나 볼 수 있게 된다. 프로젝트 루트에 `.env` 파일을 만들고 거기에만 저장한다:

```
# .env
BIZINFO_API_KEY=발급받은키값
```

주의: `.env` 문법은 `키=값`이다. `키: 값`(YAML 스타일 콜론)으로 쓰면 안 읽힌다.

그리고 `.gitignore`에 `.env`가 들어있는지 꼭 확인한다 (안 들어있으면 이 키가 GitHub에 그대로 올라간다).

`data.go.kr` 계열 API는 키를 **encoding(인코딩)** / **decoding(디코딩)** 두 형태로 같이 보여주는데, 아래 1-4에서 `requests`가 자동으로 URL 인코딩을 해주는 방식을 쓸 거라 **디코딩(원본) 키**를 저장한다. (인코딩된 키를 저장하면 이중 인코딩이 일어나서 `SERVICE_KEY_IS_NOT_REGISTERED_ERROR` 같은, 원인을 바로 알기 힘든 에러가 난다.)

### 1-3. 파이썬 코드에서 `.env` 값 불러오기

```python
import os
import dotenv

dotenv.load_dotenv()  # .env 파일을 읽어서 환경변수로 등록

BIZINFO_API_KEY = os.getenv("BIZINFO_API_KEY")
```

`os.getenv("이름")`은 `.env`에 적어둔 `이름=값` 중 값을 문자열로 가져온다. 키 이름이 `.env`랑 정확히 똑같아야 한다 (오타 나면 `None`이 조용히 반환되고, 나중에 API가 401/403으로 실패하는 형태로 뒤늦게 드러난다).

### 1-4. 실제 요청 보내보기

```python
import requests

url = "https://www.bizinfo.go.kr/uss/rss/bizinfoApi.do"  # API가 제공하는 엔드포인트 주소
params = {
    "crtfcKey": BIZINFO_API_KEY,
    "dataType": "json",
    "pageUnit": 10,
    "pageIndex": 1,
}

response = requests.get(url, params=params)
print(response.status_code)
print(response.text)
```

- URL 문자열을 `f"...?crtfcKey={key}&..."`처럼 직접 이어붙이지 않는다. `params=` 딕셔너리로 넘기면 `requests`가 알아서 URL 인코딩까지 해준다.
- `response.status_code`가 200이면 성공. 200이 아니면(401, 429, 500 등) **`response.json()`을 바로 부르지 말고 `response.text`를 먼저 찍어서** 서버가 실제로 뭐라고 답했는지 눈으로 봐야 한다. 흔한 원인들:
  - `401` — 인증키가 틀렸거나 (오타, 발급 대기중), 파라미터 이름이 API 문서와 다름
  - `429` — 하루 호출 한도(트래픽 쿼터) 초과. 코드를 고쳐도 안 풀리고, 보통 자정 기준으로 리셋된다
  - `500`/`"Unexpected errors"` — `data.go.kr` 계열은 base URL 뒤에 오퍼레이션(기능) 이름이 한 단계 더 붙어야 하는 경우가 많다 (예: `.../mssBizService_v2/getbizList_v2`). base URL만 호출하면 이 에러가 난다.

### 1-5. 응답 구조 파악하기

같은 방식으로 API를 하나 더 붙일 때, 응답 형식이 서로 다를 수 있다:

- **JSON 응답**이면 `response.json()`으로 바로 파이썬 dict/list가 됨
- **XML 응답**이면 표준 라이브러리 `xml.etree.ElementTree`로 파싱해야 함:
  ```python
  import xml.etree.ElementTree as ET

  root = ET.fromstring(response.text)          # XML 문자열 → 태그 트리 구조로 변환
  items = root.findall(".//item")               # root 아래 어디에 있든 <item> 태그를 전부 찾음
  parsed = [{child.tag: child.text for child in item} for item in items]
  # 각 <item> 태그의 자식 태그들을 {태그이름: 텍스트} 형태의 dict로 변환
  ```

이때 필드 이름(`title`인지 `pblancNm`인지), 날짜 표기 방식, 페이지네이션 파라미터 이름(`pageNo`/`pageIndex` 등)이 API마다 다르다는 걸 미리 메모해둔다 — 다음 단계(통합 스키마)에서 이 차이를 흡수해야 한다.

### 1-6. 전체 데이터 가져오기 (페이지네이션)

한 번의 요청으로는 보통 몇십 건만 온다. 응답 안에 전체 건수(`totalCount`, `totCnt` 등)가 같이 오는데, 이 값으로 몇 페이지를 더 돌아야 하는지 계산한다:

```python
import math
import time

total_pages = math.ceil(total_count / page_size)
for page in range(2, total_pages + 1):
    # 페이지별로 요청 반복
    ...
    time.sleep(0.2)  # 요청 사이에 짧게 쉬어서 서버 부담/차단을 피함
```

**주의**: 개발계정은 보통 하루 호출 한도가 있다. 페이지네이션 코드를 디버깅하면서 전체 데이터를 계속 다시 긁으면 순식간에 한도를 다 쓴다. 개발 중엔 응답 1~2페이지를 로컬 파일로 저장해두고, 그 파일로 파싱 로직만 반복 테스트하는 걸 추천한다.

## 2. 여러 소스를 하나의 스키마로 통합

API를 2개 이상 붙이면, 소스마다 필드 이름이 다 다르다는 문제를 만난다. 이걸 해결하는 순서:

1. **공통 스키마 정의** — `pydantic`의 `BaseModel`로, "우리 서비스에서 쓸" 필드 이름을 새로 정한다 (소스 원본 필드명 그대로 쓰지 않음):
   ```python
   from pydantic import BaseModel
   from datetime import date
   from typing import Literal, Optional

   class Program(BaseModel):
       source: Literal["source_a", "source_b"]
       source_id: str                    # 원본 API가 준 고유 ID. 나중에 중복/갱신 판단에 필요
       title: str
       start_date: Optional[date] = None
       end_date: Optional[date] = None
       ...
   ```
2. **필드 선택 기준**: 모든 소스에 실제로 존재하는 정보만 넣는다. 한 소스에만 있는 정보를 억지로 다른 소스에도 채우려 하지 말고, 그 필드를 `Optional`로 두고 없는 소스는 빈 값으로 둔다.
3. **소스별 변환(mapper) 함수**를 따로 만든다 — 원본 dict를 받아서 `Program` 객체로 바꿔주는 함수를 소스마다 하나씩:
   ```python
   def source_a_to_program(raw: dict) -> Program:
       return Program(
           source="source_a",
           source_id=raw.get("원본ID필드", ""),
           title=raw.get("원본제목필드", ""),
           ...
       )
   ```
4. **날짜/기간처럼 표현이 들쭉날쭉한 필드는 방어적으로 파싱한다.** 실제 공공데이터엔 `"2026-07-21 ~ 2026-08-04"`처럼 깔끔한 것도 있지만 `"상시 접수마감시까지"`, `"2026년 4월 ~ 예산 소진시까지"`처럼 날짜가 아닌 값도 섞여 있다. `split`이나 `datetime.strptime`이 실패하면 예외로 프로그램 전체가 죽게 두지 말고, 그 필드만 `None`으로 넣고 넘어가도록 `try/except`로 감싼다:
   ```python
   from datetime import datetime

   def parse_date_or_none(value: str) -> str | None:
       try:
           return datetime.strptime(value.strip(), "%Y-%m-%d").date().isoformat()
       except ValueError:
           return None
   ```

## 3. DB에 저장하기

### 3-1. 로컬 DB 띄우기

`docker-compose.yml`에 PostgreSQL을 정의하고 띄운다:

```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: mydb
    ports:
      - "5433:5432"   # 이미 다른 프로젝트가 5432를 쓰고 있을 수 있으니 docker ps로 먼저 확인
```

```
docker compose up -d
docker ps    # 정상적으로 떠있는지, 포트 충돌은 없는지 확인
```

### 3-2. 테이블 정의 + 마이그레이션

```
uv add sqlalchemy alembic psycopg2-binary
uv run alembic init alembic
```

`src/db.py` 같은 파일에 SQLAlchemy로 테이블을 정의하고 (`Program` 모델과 필드는 비슷하되 DB 문법으로), `alembic/env.py`에서 `target_metadata = Base.metadata`로 연결한다. 그다음:

```
uv run alembic revision --autogenerate -m "설명"
uv run alembic upgrade head
```

첫 번째 명령이 마이그레이션 파일(up/down)을 자동 생성하고, 두 번째 명령이 실제로 테이블을 만든다.

### 3-3. 저장은 upsert로

같은 API를 반복 수집하면, 전에 저장한 레코드가 다시 나오거나(중복) 내용만 바뀌어서(예: 마감일 연장) 다시 오는 경우가 있다. 그냥 `INSERT`만 하면 중복 에러가 나거나 중복 행이 쌓인다. `(source, source_id)`처럼 "이게 같으면 같은 레코드"라고 볼 기준을 유니크 제약으로 잡고, PostgreSQL의 `on_conflict_do_update`로 "있으면 갱신, 없으면 새로 삽입"을 한 번에 처리한다:

```python
from sqlalchemy.dialects.postgresql import insert

stmt = insert(ProgramTable).values(**data)
stmt = stmt.on_conflict_do_update(
    index_elements=["source", "source_id"],
    set_={col: stmt.excluded[col] for col in UPDATE_COLUMNS},
)
session.execute(stmt)
```
