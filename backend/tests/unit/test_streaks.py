from datetime import UTC, date, datetime

from app.domain.gamification import calculate_streaks, local_activity_date


def test_local_activity_date_uses_the_users_iana_timezone() -> None:
    occurred_at = datetime(2026, 1, 1, 21, tzinfo=UTC)

    assert local_activity_date(occurred_at=occurred_at, timezone_name="Europe/Moscow") == date(
        2026, 1, 2
    )


def test_streak_calculation_keeps_yesterdays_streak_and_tracks_longest_run() -> None:
    activity_dates = [date(2026, 9, 27), date(2026, 9, 28), date(2026, 9, 30)]

    current, longest = calculate_streaks(activity_dates=activity_dates, today=date(2026, 10, 1))

    assert current == 1
    assert longest == 2


def test_streak_resets_when_the_last_activity_is_older_than_yesterday() -> None:
    current, longest = calculate_streaks(
        activity_dates=[date(2026, 9, 27), date(2026, 9, 28)],
        today=date(2026, 10, 1),
    )

    assert current == 0
    assert longest == 2
