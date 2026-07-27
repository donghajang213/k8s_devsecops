from datetime import datetime


def parse_date_or_none(value: str) -> str | None:
    """'2026-3-11', '2026-07-21' 같은 문자열만 날짜로 인정하고, 아니면 None.
    (예: '2026년 4월', '예산 소진시까지' 같은 날짜가 아닌 텍스트가 섞여 있는 경우 대비)"""
    try:
        return datetime.strptime(value.strip(), "%Y-%m-%d").date().isoformat()
    except ValueError:
        return None
