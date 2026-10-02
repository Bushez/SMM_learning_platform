from collections.abc import Sequence
from datetime import date, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.selectable import Subquery

from app.application.gamification.dto import LeaderboardEntry, LeaderboardPeriod, LeaderboardScope

from ..models import UserDailyActivityModel, UserModel, XPTransactionModel


class SqlAlchemyGamificationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

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
        result = await self._session.execute(
            insert(XPTransactionModel)
            .values(
                user_id=user_id,
                amount=amount,
                source_type=source_type,
                source_id=source_id,
                course_id=course_id,
                occurred_at=occurred_at,
            )
            .on_conflict_do_nothing(constraint="uq_xp_transactions_source")
            .returning(XPTransactionModel.id)
        )
        return result.scalar_one_or_none() is not None

    async def record_daily_activity(self, *, user_id: UUID, local_date: date) -> bool:
        result = await self._session.execute(
            insert(UserDailyActivityModel)
            .values(user_id=user_id, local_date=local_date)
            .on_conflict_do_nothing(index_elements=["user_id", "local_date"])
            .returning(UserDailyActivityModel.user_id)
        )
        return result.scalar_one_or_none() is not None

    async def activity_dates(self, *, user_id: UUID) -> Sequence[date]:
        return list(
            await self._session.scalars(
                select(UserDailyActivityModel.local_date)
                .where(UserDailyActivityModel.user_id == user_id)
                .order_by(UserDailyActivityModel.local_date)
            )
        )

    async def total_xp(self, *, user_id: UUID) -> int:
        total = await self._session.scalar(
            select(func.coalesce(func.sum(XPTransactionModel.amount), 0)).where(
                XPTransactionModel.user_id == user_id
            )
        )
        return int(total or 0)

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
        ranked = self._ranked_query(
            period=period, scope=scope, course_id=course_id, start_at=start_at
        )
        rows = await self._session.execute(
            select(ranked)
            .order_by(ranked.c.rank, ranked.c.display_name)
            .limit(limit)
            .offset(offset)
        )
        return [
            LeaderboardEntry(
                user_id=row.user_id,
                display_name=row.display_name,
                xp=int(row.xp),
                rank=int(row.rank),
            )
            for row in rows
        ]

    async def leaderboard_entry_for_user(
        self,
        *,
        user_id: UUID,
        period: LeaderboardPeriod,
        scope: LeaderboardScope,
        course_id: UUID | None,
        start_at: datetime | None,
    ) -> LeaderboardEntry | None:
        ranked = self._ranked_query(
            period=period, scope=scope, course_id=course_id, start_at=start_at
        )
        row = await self._session.execute(select(ranked).where(ranked.c.user_id == user_id))
        result = row.one_or_none()
        if result is None:
            return None
        return LeaderboardEntry(
            user_id=result.user_id,
            display_name=result.display_name,
            xp=int(result.xp),
            rank=int(result.rank),
        )

    @staticmethod
    def _ranked_query(
        *,
        period: LeaderboardPeriod,
        scope: LeaderboardScope,
        course_id: UUID | None,
        start_at: datetime | None,
    ) -> Subquery:
        query = (
            select(
                XPTransactionModel.user_id.label("user_id"),
                UserModel.display_name.label("display_name"),
                func.sum(XPTransactionModel.amount).label("xp"),
            )
            .join(UserModel, UserModel.id == XPTransactionModel.user_id)
            .group_by(XPTransactionModel.user_id, UserModel.display_name)
        )
        if start_at is not None:
            query = query.where(XPTransactionModel.occurred_at >= start_at)
        if scope is LeaderboardScope.COURSE and course_id is not None:
            query = query.where(XPTransactionModel.course_id == course_id)
        totals = query.subquery("leaderboard_totals")
        return (
            select(
                totals.c.user_id,
                totals.c.display_name,
                totals.c.xp,
                func.dense_rank().over(order_by=totals.c.xp.desc()).label("rank"),
            )
        ).subquery("ranked_leaderboard")
