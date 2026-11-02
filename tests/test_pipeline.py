from vitae.output import OutputGuard
from vitae.pipeline import Done, Meta, Pipeline, Reason, Refusal, Token, normalize
from vitae.retrieval import Hit, Retrieval


class FakeRetriever:
    def __init__(self, relevance: float) -> None:
        self.relevance = relevance

    def search(self, query: str, refuse_below: float) -> Retrieval:
        return Retrieval(self.relevance, (Hit("Work experience: Balanced+", 5.0), Hit("Skills", 1.0)))


def make(relevance: float = 0.7, reply: tuple[str, ...] = ("I work ", "at Balanced+."), hints: int = 3):
    sent = []

    def generate(messages):
        sent.append(messages)
        yield from reply

    pipeline = Pipeline(
        retriever=FakeRetriever(relevance),
        aliases={},
        sources_of={"Work experience: Balanced+": ("resume.md#Balanced+",), "Skills": ("site/skills.md#Backend",)},
        system="rules",
        generate=generate,
        refuse_below=0.61,
        refusal_text="Ask me by email.",
        small_talk_text="Hi, I'm Mark.",
        hints=hints,
    )
    return pipeline, sent


def kinds(events):
    return [type(event).__name__ for event in events]


def test_guard_holds_back_the_tail_until_the_stream_ends():
    guard = OutputGuard()
    sent = [guard.feed(delta) for delta in ["  I work at Balanced+ ", "in Mississauga."]]

    assert sent == ["I wo", "rk at Balanced+"]
    assert guard.finish() == " in Mississauga."


def test_guard_blocks_a_phone_number_split_across_tokens_before_any_digit_is_sent():
    guard = OutputGuard()
    sent = "".join(guard.feed(delta) for delta in ["Call me at (905) ", "555-", "0199."])

    assert (sent, guard.blocked, guard.finish()) == ("Call ", True, "")


def test_guard_strips_think_tags():
    guard = OutputGuard()
    text = guard.feed("<think></think>Hello there") + guard.finish()

    assert text == "Hello there"


def test_small_talk_gets_the_canned_reply_without_retrieval_or_generation():
    pipeline, sent = make()
    events = list(pipeline.answer("hi!"))

    assert (kinds(events), events[1], sent) == (["Meta", "Token", "Done"], Token("Hi, I'm Mark."), [])


def test_gate_refuses_low_relevance_without_calling_the_model():
    pipeline, sent = make(relevance=0.5)
    events = list(pipeline.answer("Give me a lasagna recipe"))

    assert (kinds(events), events[1], sent) == (["Meta", "Refusal", "Done"], Refusal(Reason.NO_EVIDENCE, "Ask me by email."), [])


def test_answer_streams_tokens_and_sends_hints_and_the_previous_question():
    pipeline, sent = make()
    events = list(pipeline.answer("What do you do there?", ("Where do you work?",)))

    assert events[0] == Meta(("Work experience: Balanced+", "Skills"), ("resume.md#Balanced+", "site/skills.md#Backend"))
    assert "".join(e.text for e in events if isinstance(e, Token)) == "I work at Balanced+."
    assert isinstance(events[-1], Done)
    assert sent[0][1]["content"] == (
        "Relevant sections: Work experience: Balanced+; Skills\nPrevious question: Where do you work?\nQuestion: What do you do there?"
    )


def test_zero_hints_leaves_the_relevant_sections_line_out():
    pipeline, sent = make(hints=0)
    list(pipeline.answer("Where do you work?"))

    assert sent[0][1]["content"] == "Question: Where do you work?"


def test_an_empty_answer_means_the_model_stopped_on_the_refusal_sentinel():
    pipeline, _ = make(reply=())
    events = list(pipeline.answer("What is your salary?"))

    assert (kinds(events), events[1]) == (["Meta", "Refusal", "Done"], Refusal(Reason.NO_ANSWER, "Ask me by email."))


def test_a_reply_that_declines_in_its_own_words_becomes_a_typed_refusal_before_anything_is_sent():
    pipeline, _ = make(reply=("I don't have ", "my salary listed, ", "but email me."))
    events = list(pipeline.answer("What is your salary?"))

    assert (kinds(events), events[1]) == (["Meta", "Refusal", "Done"], Refusal(Reason.NO_ANSWER, "Ask me by email."))


def test_normalize_removes_invisible_characters_and_caps_length():
    assert normalize("Where​ do  you⁠ work?") == "Where do you work?"
    assert len(normalize("a" * 900)) == 500
