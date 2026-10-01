from app.domain.learning import is_lesson_unlocked


def test_first_lesson_is_unlocked_and_next_requires_every_prior_lesson() -> None:
    assert is_lesson_unlocked(prior_lesson_completion=[])
    assert is_lesson_unlocked(prior_lesson_completion=[True, True])
    assert not is_lesson_unlocked(prior_lesson_completion=[True, False])
