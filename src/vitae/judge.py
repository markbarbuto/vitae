import json
from dataclasses import dataclass

from vitae.golden import GoldenItem
from vitae.knowledge import KnowledgeDoc, prefix_text
from vitae.llm import chat
from vitae.prompt import NO_ANSWER

RUBRIC = f"""You grade answers from an assistant that speaks as Mark Barbuto, in first person, on his portfolio site. "I" in an answer means Mark. The assistant could see only the knowledge base below.

Grade in two parts.

1. Faithfulness. Split the answer into atomic factual claims about Mark, his work, his projects, his interests or the assistant itself. Skip greetings, offers to help and pure phrasing. For each claim, quote the shortest knowledge-base text that supports it as evidence, then set supported. A claim is supported only if the knowledge base states it or it follows directly from what is stated. A claim that attaches a real fact to the wrong employer, project, date or number is unsupported. Persuasive wording is fine when the fact under it is supported.

2. Correctness. Answer these separately. Do not let one decide another, and do not repeat faithfulness: a wrong side detail was already graded above.
- asks_for: in a few words, what the question asks for. For a follow-up, the previous question gives the context.
- answered: true if the answer gives the asker what the question asks for. The reference answer is one good answer, not a checklist. Leaving out some of its items or details still counts as answered, and for open questions such as a pitch, a comparison or a timeline any answer that covers the substance counts. False if the answer misses it or is the refusal {NO_ANSWER}.
- wrong_on_asked: true only if the answer states something false or unsupported as part of the very thing asked for, such as the wrong award when asked which award, or a project that does not exist when asked which projects.
Give a short reason last."""

SCHEMA = {
    "type": "object",
    "properties": {
        "claims": {
            "type": "array",
            "maxItems": 15,
            "items": {
                "type": "object",
                "properties": {
                    "claim": {"type": "string", "maxLength": 300},
                    "evidence": {"type": "string", "maxLength": 300},
                    "supported": {"type": "boolean"},
                },
                "required": ["claim", "evidence", "supported"],
            },
        },
        "asks_for": {"type": "string", "maxLength": 200},
        "answered": {"type": "boolean"},
        "wrong_on_asked": {"type": "boolean"},
        "reason": {"type": "string", "maxLength": 600},
    },
    "required": ["claims", "asks_for", "answered", "wrong_on_asked", "reason"],
}


@dataclass(frozen=True)
class Claim:
    claim: str
    evidence: str
    supported: bool


@dataclass(frozen=True)
class Verdict:
    claims: tuple[Claim, ...]
    asks_for: str
    answered: bool
    wrong_on_asked: bool
    reason: str

    @property
    def faithful(self) -> bool:
        return all(claim.supported for claim in self.claims)

    @property
    def correct(self) -> bool:
        return self.answered and not self.wrong_on_asked


def parse_verdict(raw: dict) -> Verdict:
    return Verdict(
        claims=tuple(Claim(c["claim"], c["evidence"], bool(c["supported"])) for c in raw["claims"]),
        asks_for=raw["asks_for"],
        answered=bool(raw["answered"]),
        wrong_on_asked=bool(raw["wrong_on_asked"]),
        reason=raw["reason"],
    )


def judge_messages(docs: list[KnowledgeDoc], item: GoldenItem, answer: str) -> list[dict]:
    context = f"Previous question: {item.turns[-2]}\n" if len(item.turns) > 1 else ""
    return [
        {"role": "system", "content": f"{RUBRIC}\n\n<knowledge>\n{prefix_text(docs)}\n</knowledge>"},
        {
            "role": "user",
            "content": f"{context}Question: {item.question}\n\nReference answer: {item.reference}\n\nAnswer to grade: {answer}",
        },
    ]


def judge(server: str, docs: list[KnowledgeDoc], item: GoldenItem, answer: str) -> Verdict:
    for temperature in (0.0, 0.3):
        message = chat(
            server,
            judge_messages(docs, item, answer),
            temperature=temperature,
            max_tokens=8192,
            response_format={"type": "json_schema", "json_schema": {"name": "verdict", "schema": SCHEMA}},
            chat_template_kwargs={"reasoning_effort": "medium"},
        )
        if message.get("content"):
            return parse_verdict(json.loads(message["content"]))
    raise ValueError(f"{item.id}: judge returned no verdict twice; its reasoning used up max_tokens")
