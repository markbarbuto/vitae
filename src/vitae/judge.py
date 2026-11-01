import json
from dataclasses import dataclass

from vitae.golden import GoldenItem
from vitae.knowledge import KnowledgeDoc, prefix_text
from vitae.llm import chat
from vitae.prompt import NO_ANSWER

RUBRIC = f"""You grade answers from an assistant that speaks as Mark Barbuto, in first person, on his portfolio site. "I" in an answer means Mark. The assistant could see only the knowledge base below.

Grade in two parts.

1. Faithfulness. Split the answer into atomic factual claims about Mark, his work, his projects, his interests or the assistant itself. Skip greetings, offers to help and pure phrasing. For each claim, quote the shortest knowledge-base text that supports it as evidence, then set supported. A claim is supported only if the knowledge base states it or it follows directly from what is stated. A claim that attaches a real fact to the wrong employer, project, date or number is unsupported. Persuasive wording is fine when the fact under it is supported.

2. Correctness. Compare the answer with the reference answer. The answer is correct if it answers the question asked and its main facts agree with the reference. It may add other supported facts and may leave out minor details of the reference. It is incorrect if it misses the main fact the question asks for, contradicts the reference, or is the refusal {NO_ANSWER}. For a follow-up, the previous question gives the context of the question.

Give a short reason before the correct verdict."""

SCHEMA = {
    "type": "object",
    "properties": {
        "claims": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "claim": {"type": "string"},
                    "evidence": {"type": "string"},
                    "supported": {"type": "boolean"},
                },
                "required": ["claim", "evidence", "supported"],
            },
        },
        "reason": {"type": "string"},
        "correct": {"type": "boolean"},
    },
    "required": ["claims", "reason", "correct"],
}


@dataclass(frozen=True)
class Claim:
    claim: str
    evidence: str
    supported: bool


@dataclass(frozen=True)
class Verdict:
    claims: tuple[Claim, ...]
    reason: str
    correct: bool

    @property
    def faithful(self) -> bool:
        return all(claim.supported for claim in self.claims)


def parse_verdict(raw: dict) -> Verdict:
    return Verdict(
        claims=tuple(Claim(c["claim"], c["evidence"], bool(c["supported"])) for c in raw["claims"]),
        reason=raw["reason"],
        correct=bool(raw["correct"]),
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
    message = chat(
        server,
        judge_messages(docs, item, answer),
        temperature=0,
        max_tokens=4096,
        response_format={"type": "json_schema", "json_schema": {"name": "verdict", "schema": SCHEMA}},
        chat_template_kwargs={"reasoning_effort": "high"},
    )
    return parse_verdict(json.loads(message["content"]))
