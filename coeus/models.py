import json
import urllib.request

SPACEXAI_URL = "https://api.x.ai/v1"
SPACEXAI_MODEL = "grok-4.7"


def _openai(prompt, base_url, api_key, model, responses=False):
    from openai import OpenAI
    client = OpenAI(api_key=api_key or "local", base_url=base_url)
    if responses:
        result = client.responses.create(model=model, input=prompt)
        return result.output_text
    result = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    return result.choices[0].message.content


def _claude(prompt, api_key, model):
    if not model:
        raise ValueError("Set the Claude model id from your Anthropic account.")
    body = json.dumps({
        "model": model,
        "max_tokens": 800,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as res:
        data = json.loads(res.read().decode())
    parts = data.get("content") or []
    return "".join(part.get("text", "") for part in parts if part.get("type") == "text")


def complete(prompt, provider, model, base_url, api_key):
    provider = (provider or "").lower()
    if provider in ("", "none"):
        raise ValueError("No model is set.")
    if provider == "spacexai":
        if not api_key:
            raise ValueError("Set XAI_API_KEY for SpaceXAI.")
        return _openai(prompt, SPACEXAI_URL, api_key, model or SPACEXAI_MODEL, responses=True)
    if provider == "ollama":
        return _openai(prompt, base_url or "http://127.0.0.1:11434/v1", api_key or "ollama", model)
    if provider == "claude":
        if not api_key:
            raise ValueError("Set ANTHROPIC_API_KEY.")
        return _claude(prompt, api_key, model)
    if provider == "own":
        if not base_url or not model:
            raise ValueError("Your model needs a base URL and a model name.")
        if not api_key:
            raise ValueError("Set COEUS_MODEL_KEY, or save a key in the app.")
        return _openai(prompt, base_url, api_key, model)
    raise ValueError(f"Unknown model provider: {provider}")


def allow(text, provider, model, base_url, api_key):
    prompt = (
        "You are the second check for Coeus, a local trading assistant. "
        "Answer with JSON only: {\"allow\": true or false, \"reason\": \"short\"}. "
        "Allow only if the plan is specific and does not ask to ignore risk limits. "
        "Do not invent a price.\n\nPlan:\n" + text
    )
    raw = complete(prompt, provider, model, base_url, api_key)
    start = raw.find("{")
    end = raw.rfind("}")
    if start < 0 or end < start:
        return False, "The second model did not return a clear yes or no."
    data = json.loads(raw[start:end + 1])
    return bool(data.get("allow")), str(data.get("reason") or "")
