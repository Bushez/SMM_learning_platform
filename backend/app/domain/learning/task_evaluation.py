import re
import unicodedata
from collections.abc import Collection
from uuid import UUID


def evaluate_choice(
    *, selected_option_ids: Collection[UUID], correct_option_ids: Collection[UUID]
) -> bool:
    return set(selected_option_ids) == set(correct_option_ids)


def normalize_text_answer(value: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", value).strip()).casefold()


def evaluate_text_answer(*, answer: str, accepted_answers: Collection[str]) -> bool:
    return normalize_text_answer(answer) in {
        normalize_text_answer(value) for value in accepted_answers
    }
