import json
from pathlib import Path

HISTORY_PATH = Path.home() / '.local/share/gestion-stockage-final/assistant-history.json'

def load_history():
    try:
        return json.loads(HISTORY_PATH.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return []

def save_history(messages):
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_PATH.write_text(json.dumps(messages[-500:], ensure_ascii=False), encoding='utf-8')

def clear_history():
    HISTORY_PATH.unlink(missing_ok=True)
