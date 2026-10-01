from collections.abc import Collection


def is_lesson_unlocked(*, prior_lesson_completion: Collection[bool]) -> bool:
    return all(prior_lesson_completion)
