from collections.abc import Collection
from datetime import date, datetime
from itertools import pairwise
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def local_activity_date(*, occurred_at: datetime, timezone_name: str) -> date:
    try:
        return occurred_at.astimezone(ZoneInfo(timezone_name)).date()
    except ZoneInfoNotFoundError as error:
        raise ValueError("Invalid IANA timezone") from error


def calculate_streaks(*, activity_dates: Collection[date], today: date) -> tuple[int, int]:
    unique_dates = sorted(set(activity_dates))
    if not unique_dates:
        return 0, 0
    longest = 1
    run = 1
    for previous, current in pairwise(unique_dates):
        if (current - previous).days == 1:
            run += 1
        else:
            run = 1
        longest = max(longest, run)
    allowed_end = today
    if unique_dates[-1] < today:
        allowed_end = today.fromordinal(today.toordinal() - 1)
    current_streak = 0
    cursor = allowed_end
    activity_set = set(unique_dates)
    while cursor in activity_set:
        current_streak += 1
        cursor = cursor.fromordinal(cursor.toordinal() - 1)
    return current_streak, longest
