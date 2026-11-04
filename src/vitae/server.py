import hashlib
import hmac
import json
import os
import threading
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from vitae import llm
from vitae.config import load_config
from vitae.knowledge import load_knowledge
from vitae.limits import RateLimiter
from vitae.pipeline import SAMPLING, Done, Event, Pipeline
from vitae.prompt import SMALL_TALK_TEXT, refusal_text, system_message
from vitae.retrieval import Retriever, chunk_docs, load_aliases, load_hints, load_topics

QUEUE = 3


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    history: list[str] = Field(default_factory=list, max_length=10)


def sse(event: Event | dict, name: str | None = None) -> str:
    payload = event if isinstance(event, dict) else asdict(event)
    return f"event: {name or type(event).__name__.lower()}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _slot(llm_url: str, action: str, filename: str) -> bool:
    request = urllib.request.Request(
        f"{llm_url}/slots/0?action={action}",
        data=json.dumps({"filename": filename}).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        urllib.request.urlopen(request, timeout=900).close()
        return True
    except urllib.error.URLError:
        return False


def warm(llm_url: str, system: str) -> str:
    """Restore the cached knowledge prefix from disk, or prefill it once and save it.

    The file is keyed by the loaded model as well as the prompt: a slot saved by one model is meaningless to another.
    """
    with urllib.request.urlopen(f"{llm_url}/v1/models", timeout=30) as response:
        model = json.load(response)["data"][0]["id"]
    filename = f"prefix-{hashlib.sha256(f'{model}\n{system}'.encode()).hexdigest()[:16]}.bin"
    if _slot(llm_url, "restore", filename):
        return f"restored {filename}"
    llm.chat(llm_url, [{"role": "system", "content": system}, {"role": "user", "content": "Question: hi"}], **{**SAMPLING, "max_tokens": 1})
    return f"prefilled; saved {filename}" if _slot(llm_url, "save", filename) else "prefilled; slot saving is off"


def build(root: Path, llm_url: str, hints: int) -> Pipeline:
    config = load_config(root / "config" / "assistant.toml")
    docs = load_knowledge(root / "knowledge")
    topic_of = load_topics(root / "knowledge" / "topics.toml")
    sources_of: dict[str, tuple[str, ...]] = {}
    for section, topic in topic_of.items():
        sources_of[topic.name] = (*sources_of.get(topic.name, ()), section)
    return Pipeline(
        retriever=Retriever(chunk_docs(docs, topic_of), config, root / "models"),
        aliases=load_aliases(root / "knowledge" / "aliases.toml"),
        sources_of=sources_of,
        system=system_message(docs),
        generate=lambda messages: llm.stream(llm_url, messages, **SAMPLING),
        refuse_below=config.refuse_below,
        refusal_text=refusal_text(config.contact_email),
        small_talk_text=SMALL_TALK_TEXT,
        hints=hints,
        hint_of=load_hints(root / "knowledge" / "topics.toml"),
    )


@dataclass(frozen=True)
class Access:
    """With an edge secret set, only the Vercel proxy gets in, and only it may name the visitor's IP. The eval secret
    lets the eval runner past the rate limits."""

    edge_secret: str | None = None
    eval_secret: str | None = None

    @classmethod
    def from_env(cls) -> "Access":
        return cls(os.environ.get("VITAE_EDGE_SECRET") or None, os.environ.get("VITAE_EVAL_SECRET") or None)


def _matches(given: str | None, secret: str | None) -> bool:
    return secret is not None and given is not None and hmac.compare_digest(given.encode(), secret.encode())


def create_app(pipeline: Pipeline, llm_url: str, access: Access = Access(), limiter: RateLimiter | None = None) -> FastAPI:
    app = FastAPI()
    limiter = limiter or RateLimiter()
    lock, counter, waiting = threading.Lock(), threading.Lock(), [0]

    @app.on_event("startup")
    def startup() -> None:
        print(warm(llm_url, pipeline.system), flush=True)

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    @app.post("/chat")
    def chat(body: ChatRequest, request: Request) -> StreamingResponse:
        from_edge = _matches(request.headers.get("x-edge-secret"), access.edge_secret)
        if access.edge_secret and not from_edge:
            raise HTTPException(status_code=401)
        ip = request.headers.get("x-client-ip") if from_edge else None
        ip = ip or (request.client.host if request.client else "unknown")
        wait = None if _matches(request.headers.get("x-eval-secret"), access.eval_secret) else limiter.check(ip)

        def events():
            if wait is not None:
                yield sse({"retry_after_s": wait}, "rate_limited")
                return
            with counter:
                full = waiting[0] >= QUEUE
                if not full:
                    waiting[0] += 1
            if full:
                yield sse({"retry_after_s": 30}, "busy")
                return
            try:
                with lock:
                    with counter:
                        waiting[0] -= 1
                    for event in pipeline.answer(body.question, tuple(body.history)):
                        yield sse(event)
            except Exception as error:
                yield sse({"message": type(error).__name__}, "error")
                yield sse(Done())

        return StreamingResponse(events(), media_type="text/event-stream")

    return app


def serve(root: Path, llm_url: str, hints: int, host: str, port: int) -> None:
    import uvicorn

    uvicorn.run(create_app(build(root, llm_url, hints), llm_url, Access.from_env()), host=host, port=port)

