from uuid import uuid4

from app.domain.learning import evaluate_choice, evaluate_text_answer, normalize_text_answer


def test_multiple_choice_requires_an_exact_set_of_correct_options() -> None:
    first, second, extra = uuid4(), uuid4(), uuid4()

    assert evaluate_choice(selected_option_ids=[first, second], correct_option_ids=[second, first])
    assert not evaluate_choice(selected_option_ids=[first], correct_option_ids=[first, second])
    assert not evaluate_choice(
        selected_option_ids=[first, second, extra], correct_option_ids=[first, second]
    )


def test_text_evaluation_uses_unicode_normalization_casefold_and_whitespace() -> None:
    assert normalize_text_answer("  Café\u00a0Sans   ") == "café sans"
    assert evaluate_text_answer(answer="  CAFÉ\u00a0sans ", accepted_answers=["Café Sans"])
    assert not evaluate_text_answer(answer="Serif", accepted_answers=["Sans Serif"])
