from pathlib import Path

import pytest

from vitae.calibration import Label, agreement, parse_sheet, render_sheet, sample
from vitae.golden import load_golden, parse_item
from vitae.judge import parse_verdict

ITEM = parse_item(
    {"id": "followup-01", "category": "followup", "turns": ["Where do you work?", "What did you build?"], "reference": "The KHP app.", "sections": ["a.md#A"]},
    "dev",
)


def test_a_filled_sheet_round_trips_to_labels():
    sheet = render_sheet([(ITEM, "I built the KHP app.")], "tune")
    filled = sheet.replace("- correct: ", "- correct: y").replace("- faithful: ", "- faithful: N").replace("- note: ", "- note: close enough")

    assert "**Previous question:** Where do you work?" in sheet
    assert parse_sheet(filled) == [Label(item_id="followup-01", correct=True, faithful=False, note="close enough")]


def test_an_unlabelled_answer_is_reported_by_id():
    with pytest.raises(ValueError, match="followup-01: correct must be y or n, got ''"):
        parse_sheet(render_sheet([(ITEM, "I built the KHP app.")], "tune"))


def test_agreement_reports_rate_and_chance_corrected_kappa():
    result = agreement(human=[True, True, True, False], judge=[True, True, False, False])

    assert (result.agree, result.n, result.rate, round(result.kappa, 3)) == (3, 4, 0.75, 0.5)


def test_an_answer_is_faithful_only_when_every_claim_is_supported():
    verdict = parse_verdict(
        {
            "claims": [
                {"claim": "I work at Balanced+.", "evidence": "Software Developer at Balanced+", "supported": True},
                {"claim": "I won a Nobel Prize.", "evidence": "", "supported": False},
            ],
            "asks_for": "where I work",
            "answered": True,
            "wrong_on_asked": False,
            "reason": "Invented award.",
        }
    )

    assert (verdict.correct, verdict.faithful) == (True, False)


def test_a_wrong_fact_in_what_was_asked_makes_an_answer_incorrect():
    verdict = parse_verdict(
        {
            "claims": [{"claim": "Celestica gave me the Award of Excellence.", "evidence": "", "supported": False}],
            "asks_for": "which award I got at Celestica",
            "answered": True,
            "wrong_on_asked": True,
            "reason": "Wrong award for Celestica.",
        }
    )

    assert (verdict.correct, verdict.faithful) == (False, False)


def test_holdout_never_reuses_tuning_items():
    items = load_golden(Path("eval/golden"))
    tune = sample(items, "tune")
    holdout = sample(items, "holdout", frozenset(item.id for item in tune))

    assert (len(tune), len(holdout)) == (40, 15)
    assert not {item.id for item in tune} & {item.id for item in holdout}
