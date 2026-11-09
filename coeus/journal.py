from datetime import datetime, timezone
from coeus.store import HOME


def path():
    HOME.mkdir(parents=True, exist_ok=True)
    file = HOME / "journal.md"
    if not file.exists():
        file.write_text("# Coeus journal\n\nPlain text. You can edit this file.\n")
    return file


def add(title, body):
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    with path().open("a") as handle:
        handle.write(f"\n## {stamp} — {title}\n\n{body.strip()}\n")


def read():
    return path().read_text()


def day_pnl():
    total = 0.0
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    current = False
    for line in read().splitlines():
        if line.startswith("## "):
            current = today in line
            continue
        if current and line.startswith("pnl:"):
            try:
                total += float(line.split(":", 1)[1].strip())
            except ValueError:
                pass
    return total
