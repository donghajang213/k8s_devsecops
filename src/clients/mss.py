# 공공데이터포털 API 호출 + mapper

import time

import requests
from src.config import MSS_SERVICE_KEY
from src.models import Program
import xml.etree.ElementTree as ET

### 공공데이터 포털

MSS_URL = "https://apis.data.go.kr/1421000/mssBizService_v2/getbizList_v2"

def fetch_mss_data(pageNo=1, numOfRows=10):
    params = {
        "serviceKey": MSS_SERVICE_KEY,
        "pageNo": pageNo,
        "numOfRows": numOfRows
    }

    response = requests.get(MSS_URL, params=params)

    # ET.fromstring이 XML이 아닌 걸 받으면 바로 ParseError로 죽어서,
    # 실제로 서버가 뭘 돌려줬는지 먼저 눈으로 확인하기 위한 디버그 출력.
    # (정상 동작 확인되면 이 두 줄은 지워도 됨)
    print("pageNo:", pageNo, response.status_code)
    print(repr(response.text))

    root = ET.fromstring(response.text)

    items = []
    for item in root.findall(".//item"):
        items.append({child.tag: child.text for child in item})
    return items

def fetch_mss_all(numOfRows=10):
    first_page_params = {
        "serviceKey": MSS_SERVICE_KEY,
        "pageNo": 1,
        "numOfRows": numOfRows
    }
    first_response = requests.get(MSS_URL, params=first_page_params)
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
        source_id=raw.get("itemId", ""),
        title=raw.get("title", ""),
        target="",
        start_date=raw.get("applicationStartDate") or None,
        end_date=raw.get("applicationEndDate") or None,
        description=raw.get("dataContents", ""),
        jurisdiction_org="중소벤처기업부",
        executing_org=raw.get("writerPosition", ""),
        category="",
        source_url=raw.get("viewUrl", "")
    )
