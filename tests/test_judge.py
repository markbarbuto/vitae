from vitae.judge import Claim, Verdict, second_opinion


def verdict(supported: bool) -> Verdict:
    claim = Claim(claim="I loved the pizza.", evidence="the best sandwiches and pizza", supported=supported)
    return Verdict(claims=(claim,), asks_for="what stood out", answered=True, wrong_on_asked=False, reason="")


def test_an_answer_is_unfaithful_only_when_both_judges_say_so():
    strict = {"id": "followup-10", "correct": True, "faithful": False}

    assert second_opinion(strict, verdict(True))["faithful"] is True
    assert second_opinion(strict, verdict(False))["faithful"] is False


def test_the_second_opinion_never_changes_correctness_and_is_kept():
    row = second_opinion({"id": "resume-30", "correct": False, "faithful": False}, verdict(True))

    assert row["correct"] is False
    assert row["second"] == {"claims": [{"claim": "I loved the pizza.", "evidence": "the best sandwiches and pizza", "supported": True}], "faithful": True}
