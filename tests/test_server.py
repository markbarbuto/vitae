from types import SimpleNamespace

from fastapi.testclient import TestClient

from vitae.limits import RateLimiter
from vitae.pipeline import Done, Token
from vitae.server import Access, create_app

ACCESS = Access(edge_secret="edge", eval_secret="eval")


def client(limiter: RateLimiter | None = None) -> TestClient:
    pipeline = SimpleNamespace(system="", answer=lambda question, history: iter([Token("Hi."), Done()]))
    return TestClient(create_app(pipeline, "http://unused", ACCESS, limiter))


def ask(c: TestClient, **headers: str):
    return c.post("/chat", json={"question": "Where do you work?"}, headers=headers)


def test_only_the_edge_proxy_gets_in():
    c = client()

    assert ask(c).status_code == 401
    assert ask(c, **{"x-edge-secret": "wrong"}).status_code == 401
    assert ask(c, **{"x-edge-secret": "edge"}).text == 'event: token\ndata: {"text": "Hi."}\n\nevent: done\ndata: {"timings": {}}\n\n'


def test_the_fifth_question_in_a_minute_from_one_visitor_is_rate_limited():
    limiter = RateLimiter(clock=lambda: 1000.0)
    c = client(limiter)
    visitor = {"x-edge-secret": "edge", "x-client-ip": "1.1.1.1"}
    for _ in range(4):
        ask(c, **visitor)

    assert ask(c, **visitor).text == 'event: rate_limited\ndata: {"retry_after_s": 60.0}\n\n'
    assert ask(c, **{**visitor, "x-client-ip": "2.2.2.2"}).text.startswith("event: token")
    assert ask(c, **{**visitor, "x-eval-secret": "eval"}).text.startswith("event: token")
