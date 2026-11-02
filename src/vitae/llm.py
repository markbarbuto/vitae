import json
import urllib.request


def chat(server: str, messages: list[dict], **params) -> dict:
    body = json.dumps({"messages": messages, **params}).encode("utf-8")
    request = urllib.request.Request(
        f"{server}/v1/chat/completions", data=body, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(request, timeout=600) as response:
        return json.load(response)["choices"][0]["message"]
