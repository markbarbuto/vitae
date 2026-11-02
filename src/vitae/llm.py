import json
import urllib.request
from collections.abc import Iterator


def _post(server: str, body: dict, timeout: float = 600):
    request = urllib.request.Request(
        f"{server}/v1/chat/completions", data=json.dumps(body).encode("utf-8"), headers={"Content-Type": "application/json"}
    )
    return urllib.request.urlopen(request, timeout=timeout)


def chat(server: str, messages: list[dict], **params) -> dict:
    with _post(server, {"messages": messages, **params}) as response:
        return json.load(response)["choices"][0]["message"]


def stream(server: str, messages: list[dict], **params) -> Iterator[str]:
    with _post(server, {"messages": messages, "stream": True, **params}) as response:
        for line in response:
            if not line.startswith(b"data: ") or line.strip() == b"data: [DONE]":
                continue
            delta = json.loads(line[6:])["choices"][0]["delta"].get("content")
            if delta:
                yield delta
