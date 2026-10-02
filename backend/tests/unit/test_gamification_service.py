from collections.abc import Sequence
from datetime import date, datetime
from uuid import UUID, uuid4

from app.application.gamification import GamificationService
from app.application.gamification.dto import LeaderboardEntry, LeaderboardPeriod, LeaderboardScope


class FakeGamificationRepository:
    def __init__(self) -> None:
        self._awarded_sources: set[tuple[UUID, str, UUID]] = set()
        self.activity: set[tuple[UUID, date]] = set()
        self.total = 0

    async def award_xp(
        self,
        *,
        user_id: UUID,
        amount: int,
        source_type: str,
        source_id: UUID,
        course_id: UUID,
        occurred_at: datetime,
    ) -> bool:
        del course_id, occurred_at
        source = (user_id, source_type, source_id)
        if source in self._awarded_sources:
            return False
        self._awarded_sources.add(source)
        self.total += amount
        return True

    async def record_daily_activity(self, *, user_id: UUID, local_date: date) -> bool:
        activity = (user_id, local_date)
        if activity in self.activity:
            return False
        self.activity.add(activity)
        return True

    async def activity_dates(self, *, user_id: UUID) -> Sequence[date]:
        return sorted(
            activity_date
            for activity_user, activity_date in self.activity
            if activity_user == user_id
        )

    async def total_xp(self, *, user_id: UUID) -> int:
        del user_id
        return self.total

    async def leaderboard_entries(
        self,
        *,
        period: LeaderboardPeriod,
        scope: LeaderboardScope,
        course_id: UUID | None,
        start_at: datetime | None,
        limit: int,
        offset: int,
    ) -> Sequence[LeaderboardEntry]:
        del period, scope, course_id, start_at, limit, offset
        return []

    async def leaderboard_entry_for_user(
        self,
        *,
        user_id: UUID,
        period: LeaderboardPeriod,
        scope: LeaderboardScope,
        course_id: UUID | None,
        start_at: datetime | None,
    ) -> LeaderboardEntry | None:
        del user_id, period, scope, course_id, start_at
        return None


async def test_xp_award_is_idempotent_and_daily_activity_requires_lesson_completion() -> None:
    repository = FakeGamificationRepository()
    service = GamificationService(gamification=repository, task_completion_xp=10)
    user_id, course_id, task_id = uuid4(), uuid4(), uuid4()

    first = await service.on_first_task_completion(
        user_id=user_id,
        task_id=task_id,
        course_id=course_id,
        timezone_name="UTC",
        lesson_completed=False,
    )
    second = await service.on_first_task_completion(
        user_id=user_id,
        task_id=task_id,
        course_id=course_id,
        timezone_name="UTC",
        lesson_completed=True,
    )

    assert first.xp_awarded == 10
    assert second.xp_awarded == 0
    assert len(repository.activity) == 1
    assert await repository.total_xp(user_id=user_id) == 10
