from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class LeaderboardPeriod(StrEnum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    ALL_TIME = "ALL_TIME"


class LeaderboardScope(StrEnum):
    GLOBAL = "GLOBAL"
    COURSE = "COURSE"


@dataclass(frozen=True, slots=True)
class GamificationSummary:
    total_xp: int
    current_streak: int
    longest_streak: int


@dataclass(frozen=True, slots=True)
class GamificationOutcome:
    xp_awarded: int
    current_streak: int | None
    longest_streak: int | None


@dataclass(frozen=True, slots=True)
class LeaderboardEntry:
    user_id: UUID
    display_name: str
    xp: int
    rank: int


@dataclass(frozen=True, slots=True)
class LeaderboardView:
    period: LeaderboardPeriod
    scope: LeaderboardScope
    course_id: UUID | None
    entries: tuple[LeaderboardEntry, ...]
    current_user: LeaderboardEntry | None
