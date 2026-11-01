import pytest

from vitae.calibration import Label, agreement, parse_sheet, render_sheet
from vitae.golden import parse_item
from vitae.judge import parse_verdict

ITEM = parse_item(
    {"id": "followup-01", "category": "followup", "turns": ["Where do you work?", "What did you build?"], "reference": "The KHP app.", "sections": ["a.md#A"]},
    "dev",
)


def test_a_filled_sheet_round_trips_to_labels():
    sheet = render_sheet([(ITEM, "I built the KHP app.")])
    filled = sheet.replace("- correct: ", "- correct: y").replace("- faithful: ", "- faithful: N").replace("- note: ", "- note: close enough")

    assert "**Previous question:** Where do you work?" in sheet
    assert parse_sheet(filled) == [Label(item_id="followup-01", correct=True, faithful=False, note="close enough")]


def test_an_unlabelled_answer_is_reported_by_id():
    with pytest.raises(ValueError, match="followup-01: correct must be y or n, got ''"):
        parse_sheet(render_sheet([(ITEM, "I built the KHP app.")]))


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
            "reason": "Invented award.",
            "correct": True,
        }
    )

    assert (verdict.correct, verdict.faithful) == (True, False)
