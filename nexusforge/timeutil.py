from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def current_timestamp(timezone_name: str | None = None) -> str:
    tzinfo = None
    if timezone_name:
        try:
            tzinfo = ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError:
            tzinfo = None
    now = datetime.now(tzinfo).astimezone(tzinfo)
    return now.isoformat(timespec="seconds")

