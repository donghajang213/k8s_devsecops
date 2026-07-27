# 기업마당 API 호출 + mapper
import requests
from src.models import Program
from src.date_utils import parse_date_or_none

from src.config import BIZINFO_API_KEY
### 기업마당

BIZINFO_URL = "https://www.bizinfo.go.kr/uss/rss/bizinfoApi.do"

def fetch_bizinfo_data(dataType="json", pageUnit=100, pageIndex=1):
    params = {
        "crtfcKey": BIZINFO_API_KEY,
        "dataType": dataType,
        "pageUnit": pageUnit,
        "pageIndex": pageIndex
    }

    response = requests.get(BIZINFO_URL, params=params)
    return response.json()["jsonArray"]

import math
import time

def fetch_bizinfo_all(dataType="json", pageUnit=100):
    first_page_params = {
        "crtfcKey": BIZINFO_API_KEY,
        "dataType": dataType,
        "pageUnit": pageUnit,
        "pageIndex": 1,
    }
    first_response = requests.get(BIZINFO_URL, params=first_page_params).json()
    all_items = first_response["jsonArray"]
    # totCnt는 최상위가 아니라 jsonArray 안 각 항목마다 들어있는 필드라 이렇게 꺼낸다.
    # (건수가 0이면 all_items가 비어있어 total도 0으로 처리)
    total = int(all_items[0]["totCnt"]) if all_items else 0

    total_pages = math.ceil(total / pageUnit)
    for page in range(2, total_pages + 1):
        all_items += fetch_bizinfo_data(dataType=dataType, pageUnit=pageUnit, pageIndex=page)
        time.sleep(0.2)  # 연속 요청 사이 잠깐 대기 - 서버 부담/rate limit 방지

    return all_items


def bizinfo_to_program(raw: dict) -> Program:

    raw_period = raw.get("reqstBeginEndDe", "")
    if raw_period.count("~") == 1:
        start_raw, end_raw = raw_period.split("~")
        start_date, end_date = parse_date_or_none(start_raw), parse_date_or_none(end_raw)
    else:
        # "상시 접수마감시까지" 같은 날짜 범위가 아닌 값 - 날짜 정보 없이 저장
        start_date, end_date = None, None

    return Program(
        source="bizinfo",
        source_id=raw.get("pblancId", ""),
        title=raw.get("pblancNm", ""),
        target=raw.get("trgetNm", ""),
        start_date=start_date,
        end_date=end_date,
        description=raw.get("bsnsSumryCn", ""),
        jurisdiction_org=raw.get("jrsdInsttNm", ""),
        executing_org=raw.get("excInsttNm", ""),
        category=raw.get("pldirSportRealmLclasCodeNm", ""),
        source_url=raw.get("pblancUrl", "")
    )

