from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.application.auth.dto import UserView
from app.application.common.errors import ValidationError
from app.application.gamification import GamificationService
from app.application.gamification.dto import (
    GamificationSummary,
    LeaderboardEntry,
    LeaderboardPeriod,
    LeaderboardScope,
    LeaderboardView,
)
from app.presentation.api.dependencies import (
    get_gamification_service,
    require_authenticated_user,
)

leaderboard_router = APIRouter(prefix="/leaderboards", tags=["Leaderboards"])
profile_router = APIRouter(prefix="/users/me", tags=["Users"])


class GamificationSummaryResponse(BaseModel):
    total_xp: int
    current_streak: int
    longest_streak: int

    @classmethod
    def from_view(cls, summary: GamificationSummary) -> "GamificationSummaryResponse":
        return cls(
            total_xp=summary.total_xp,
            current_streak=summary.current_streak,
            longest_streak=summary.longest_streak,
        )


class LeaderboardEntryResponse(BaseModel):
    user_id: UUID
    display_name: str
    xp: int
    rank: int

    @classmethod
    def from_view(cls, entry: LeaderboardEntry) -> "LeaderboardEntryResponse":
        return cls(
            user_id=entry.user_id, display_name=entry.display_name, xp=entry.xp, rank=entry.rank
        )


class LeaderboardResponse(BaseModel):
    period: LeaderboardPeriod
    scope: LeaderboardScope
    course_id: UUID | None
    entries: list[LeaderboardEntryResponse]
    current_user: LeaderboardEntryResponse | None

    @classmethod
    def from_view(cls, leaderboard: LeaderboardView) -> "LeaderboardResponse":
        return cls(
            period=leaderboard.period,
            scope=leaderboard.scope,
            course_id=leaderboard.course_id,
            entries=[LeaderboardEntryResponse.from_view(entry) for entry in leaderboard.entries],
            current_user=LeaderboardEntryResponse.from_view(leaderboard.current_user)
            if leaderboard.current_user
            else None,
        )


@profile_router.get(
    "/gamification",
    response_model=GamificationSummaryResponse,
    summary="Get current user's XP and streak summary",
    operation_id="getMyGamificationSummary",
)
async def get_my_gamification_summary(
    user: UserView = Depends(require_authenticated_user),
    service: GamificationService = Depends(get_gamification_service),
) -> GamificationSummaryResponse:
    return GamificationSummaryResponse.from_view(
        await service.summary(user_id=user.id, timezone_name=user.timezone)
    )


@leaderboard_router.get(
    "",
    response_model=LeaderboardResponse,
    summary="Get XP leaderboard using UTC period boundaries",
    operation_id="getLeaderboard",
)
async def get_leaderboard(
    period: LeaderboardPeriod = Query(default=LeaderboardPeriod.WEEKLY),
    scope: LeaderboardScope = Query(default=LeaderboardScope.GLOBAL),
    course_id: UUID | None = Query(default=None),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: UserView = Depends(require_authenticated_user),
    service: GamificationService = Depends(get_gamification_service),
) -> LeaderboardResponse:
    if scope is LeaderboardScope.COURSE and course_id is None:
        raise ValidationError("course_id is required for course leaderboard scope")
    if scope is LeaderboardScope.GLOBAL and course_id is not None:
        raise ValidationError("course_id is only valid for course leaderboard scope")
    return LeaderboardResponse.from_view(
        await service.leaderboard(
            current_user_id=user.id,
            period=period,
            scope=scope,
            course_id=course_id,
            limit=limit,
            offset=offset,
        )
    )
