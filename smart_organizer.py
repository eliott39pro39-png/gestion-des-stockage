"""Planificateur de rangement : aucun déplacement sans validation explicite."""
from pathlib import Path

GROUPS = {
    "Images": {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp"},
    "Vidéos": {".mp4", ".mkv", ".avi", ".mov", ".webm"},
    "Musique": {".mp3", ".wav", ".flac", ".ogg", ".m4a"},
    "Documents": {".pdf", ".doc", ".docx", ".odt", ".txt", ".rtf", ".xls", ".xlsx", ".pptx"},
    "Archives": {".zip", ".tar", ".gz", ".7z", ".rar"},
}

def category(path):
    return next((name for name, extensions in GROUPS.items() if path.suffix.casefold() in extensions), None)

def plan(folder, limit=200):
    root = Path(folder).expanduser()
    if not root.is_dir() or root.is_symlink():
        raise ValueError("Choisis un dossier normal et accessible.")
    moves = []
    for path in sorted(root.iterdir(), key=lambda p: p.name.casefold()):
        if len(moves) >= limit:
            break
        if not path.is_file() or path.is_symlink():
            continue
        group = category(path)
        if not group:
            continue
        target = root / group / path.name
        if target.parent.is_symlink() or target.exists() or target.is_symlink():
            continue
        moves.append((path, target))
    return moves

def execute(moves):
    done = []
    for source, target in moves:
        if source.is_symlink() or not source.is_file() or target.parent.is_symlink() or target.exists() or target.is_symlink():
            continue
        if source.parent != target.parent.parent or target.parent.name not in GROUPS:
            continue
        if category(source) != target.parent.name:
            continue
        target.parent.mkdir(exist_ok=True)
        if target.exists():
            continue
        source.rename(target)
        done.append((source, target))
    return done

def undo(moves):
    restored = []
    for source, target in reversed(moves):
        if target.is_file() and not target.is_symlink() and not source.exists():
            target.rename(source)
            restored.append(source)
    return restored
