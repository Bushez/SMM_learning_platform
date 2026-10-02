from datetime import UTC, date, datetime, timedelta
from uuid import UUID

from app.domain.gamification import calculate_streaks, local_activity_date

from .dto import (
    GamificationOutcome,
    GamificationSummary,
    LeaderboardPeriod,
    LeaderboardScope,
    LeaderboardView,
)
from .ports import GamificationRepository


class GamificationService:
    def __init__(self, *, gamification: GamificationRepository, task_completion_xp: int) -> None:
        self._gamification = gamification
        self._task_completion_xp = task_completion_xp

    async def on_first_task_completion(
        self,
        *,
        user_id: UUID,
        task_id: UUID,
        course_id: UUID,
        timezone_name: str,
        lesson_completed: bool,
    ) -> GamificationOutcome:
        occurred_at = datetime.now(UTC)
        awarded = await self._gamification.award_xp(
            user_id=user_id,
            amount=self._task_completion_xp,
            source_type="TASK_COMPLETION",
            source_id=task_id,
            course_id=course_id,
            occurred_at=occurred_at,
        )
        if not lesson_completed:
            return GamificationOutcome(
                xp_awarded=self._task_completion_xp if awarded else 0,
                current_streak=None,
                longest_streak=None,
            )
        local_date = local_activity_date(occurred_at=occurred_at, timezone_name=timezone_name)
        await self._gamification.record_daily_activity(user_id=user_id, local_date=local_date)
        current, longest = await self._streaks(user_id=user_id, today=local_date)
        return GamificationOutcome(
            xp_awarded=self._task_completion_xp if awarded else 0,
            current_streak=current,
            longest_streak=longest,
        )

    async def summary(self, *, user_id: UUID, timezone_name: str) -> GamificationSummary:
        now = datetime.now(UTC)
        today = local_activity_date(occurred_at=now, timezone_name=timezone_name)
        current, longest = await self._streaks(user_id=user_id, today=today)
        return GamificationSummary(
            total_xp=await self._gamification.total_xp(user_id=user_id),
            current_streak=current,
            longest_streak=longest,
        )

    async def leaderboard(
        self,
        *,
        current_user_id: UUID,
        period: LeaderboardPeriod,
        scope: LeaderboardScope,
        course_id: UUID | None,
        limit: int,
        offset: int,
    ) -> LeaderboardView:
        start_at = _period_start(period, datetime.now(UTC))
        entries = await self._gamification.leaderboard_entries(
            period=period,
            scope=scope,
            course_id=course_id,
            start_at=start_at,
            limit=limit,
            offset=offset,
        )
        current_user = await self._gamification.leaderboard_entry_for_user(
            user_id=current_user_id,
            period=period,
            scope=scope,
            course_id=course_id,
            start_at=start_at,
        )
        return LeaderboardView(
            period=period,
            scope=scope,
            course_id=course_id,
            entries=tuple(entries),
            current_user=current_user,
        )

    async def _streaks(self, *, user_id: UUID, today: date) -> tuple[int, int]:
        return calculate_streaks(
            activity_dates=await self._gamification.activity_dates(user_id=user_id), today=today
        )


def _period_start(period: LeaderboardPeriod, now: datetime) -> datetime | None:
    if period is LeaderboardPeriod.ALL_TIME:
        return None
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    if period is LeaderboardPeriod.DAILY:
        return day_start
    if period is LeaderboardPeriod.WEEKLY:
        return day_start - timedelta(days=day_start.weekday())
    return day_start.replace(day=1)
