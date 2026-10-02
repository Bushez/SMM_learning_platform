from collections.abc import Sequence
from datetime import date, datetime
from typing import Protocol
from uuid import UUID

from .dto import LeaderboardEntry, LeaderboardPeriod, LeaderboardScope


class GamificationRepository(Protocol):
    async def award_xp(
        self,
        *,
        user_id: UUID,
        amount: int,
        source_type: str,
        source_id: UUID,
        course_id: UUID,
        occurred_at: datetime,
    ) -> bool: ...

    async def record_daily_activity(self, *, user_id: UUID, local_date: date) -> bool: ...

    async def activity_dates(self, *, user_id: UUID) -> Sequence[date]: ...

    async def total_xp(self, *, user_id: UUID) -> int: ...

    async def leaderboard_entries(
        self,
        *,
        period: LeaderboardPeriod,
        scope: LeaderboardScope,
        course_id: UUID | None,
        start_at: datetime | None,
        limit: int,
        offset: int,
    ) -> Sequence[LeaderboardEntry]: ...

    async def leaderboard_entry_for_user(
        self,
        *,
        user_id: UUID,
        period: LeaderboardPeriod,
        scope: LeaderboardScope,
        course_id: UUID | None,
        start_at: datetime | None,
    ) -> LeaderboardEntry | None: ...
