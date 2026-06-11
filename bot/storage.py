import json
from pathlib import Path

FILE = Path("history.json")

def load_history():
    if FILE.exists():
        return json.loads(FILE.read_text())
    return {}

def save_history(data):
    FILE.write_text(json.dumps(data, indent=2))

history = load_history()