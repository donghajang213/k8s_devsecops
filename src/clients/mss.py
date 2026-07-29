# 공공데이터포털 API 호출 + mapper

import time

import requests
from src.config import MSS_SERVICE_KEY
from src.models import Program
from src.date_utils import parse_date_or_none
from defusedxml import ElementTree as ET   # 외부(신뢰 불가) XML 파싱이라 표준 라이브러리 대신 defusedxml 사용

### 공공데이터 포털

MSS_URL = "https://apis.data.go.kr/1421000/mssBizService_v2/getbizList_v2"

def fetch_mss_data(pageNo=1, numOfRows=100):
    params = {
        "serviceKey": MSS_SERVICE_KEY,
        "pageNo": pageNo,
        "numOfRows": numOfRows
    }

    response = requests.get(MSS_URL, params=params, timeout=10)
    root = ET.fromstring(response.text)

    items = []
    for item in root.findall(".//item"):
        items.append({child.tag: child.text for child in item})
    return items

def fetch_mss_all(numOfRows=100):
    first_page_params = {
        "serviceKey": MSS_SERVICE_KEY,
        "pageNo": 1,
        "numOfRows": numOfRows
    }
    first_response = requests.get(MSS_URL, params=first_page_params, timeout=10)
    root = ET.fromstring(first_response.text)
    total_count = int(root.findtext(".//totalCount", default="0"))
    all_items = [
    {child.tag: child.text for child in item}
    for item in root.findall(".//item")
    ]   


    total_pages = (total_count + numOfRows - 1) // numOfRows
    for page in range(2, total_pages + 1):
        all_items += fetch_mss_data(pageNo=page, numOfRows=numOfRows)
        time.sleep(0.2)  # 연속 요청 사이 잠깐 대기 - 서버 부담/rate limit 방지

    return all_items


def mss_to_program(raw: dict) -> Program:
    return Program(
        source="mss",
        source_id=raw.get("itemId") or "",
        title=raw.get("title") or "",
        target="",
        start_date=parse_date_or_none(raw.get("applicationStartDate") or ""),
        end_date=parse_date_or_none(raw.get("applicationEndDate") or ""),
        description=raw.get("dataContents") or "",
        jurisdiction_org="중소벤처기업부",
        executing_org=raw.get("writerPosition") or "",
        category="",
        source_url=raw.get("viewUrl") or ""
    )
