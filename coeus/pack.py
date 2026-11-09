import json
from pathlib import Path

SYSTEM = """You are Coeus, a local assistant for Hyperliquid perpetual trades.

The person describes a plan in plain English. You may read the market and propose a trade. You do not place the trade. The Coeus app checks the guardrails in code and sends the order only after the person approves it.

Rules:
- Markets you may talk about: BTC, ETH, SOL, HYPE.
- Say when a condition is not met. Do not invent a price, a size, or a fill.
- Stops and take-profits stay on the person's computer. Do not tell them to put the tight stop on the public order book.
- Open positions on Hyperliquid are public. The plan and the hidden stops are not.
- Never ask for the main wallet private key or seed phrase.
- Leveraged trades can lose money. This is not financial advice.
- The product name is Coeus. The token ticker is $COEUS. There is no claim about the token's price.

When a plan is unclear, ask one question. Do not guess the missing stop or size.
"""

TOOLS = {
    "name": "Coeus",
    "ticker": "$COEUS",
    "tools": [
        {
            "name": "read_market",
            "description": "Read mark price, funding, and open interest for BTC, ETH, SOL, or HYPE.",
            "parameters": {"coin": "BTC | ETH | SOL | HYPE"},
        },
        {
            "name": "propose_trade",
            "description": "Turn a plain-English plan into a trade for the person to approve. Does not send an order.",
            "parameters": {"text": "the plan"},
        },
    ],
}


def export(folder):
    dest = Path(folder).expanduser().resolve()
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "SYSTEM.md").write_text(SYSTEM)
    (dest / "tools.json").write_text(json.dumps(TOOLS, indent=2) + "\n")
    (dest / "README.md").write_text(
        "Import Coeus into a model you already use.\n\n"
        "SpaceXAI, Claude, an OpenAI-compatible server, or Ollama: paste SYSTEM.md as the system prompt "
        "and give the model the two tools in tools.json. Those tools should call the Coeus app on this computer. "
        "The app still enforces the guardrails and still asks before it sends an order.\n\n"
        "Or point Coeus at your model instead: in the app, choose Your model, Ollama, Claude, or SpaceXAI, "
        "and enter the base URL and model name. The key stays in ~/.coeus/secrets.json or in an environment variable.\n"
    )
    return dest
