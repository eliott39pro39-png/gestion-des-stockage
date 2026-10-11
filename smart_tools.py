"""Local, opt-in storage tools. Never delete source files or follow symlinks."""
import os
import pathlib
import shutil
from collections import defaultdict

CATEGORIES = {
    "Images": {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp"},
    "Documents": {".pdf", ".doc", ".docx", ".odt", ".txt", ".md", ".csv", ".xls", ".xlsx"},
    "Vidéos": {".mp4", ".mov", ".mkv", ".avi", ".webm"},
    "Musique": {".mp3", ".wav", ".flac", ".ogg", ".m4a"},
    "Archives": {".zip", ".tar", ".gz", ".7z", ".rar"},
}

def _safe_file(path):
    return path.is_file() and not path.is_symlink()

def plan_organization(folder, limit=1000):
    """Preview direct-child file moves; existing targets are never overwritten."""
    folder = pathlib.Path(folder).resolve(strict=True)
    if not folder.is_dir():
        raise ValueError("Dossier invalide")
    planned = []
    for entry in folder.iterdir():
        if len(planned) >= limit:
            break
        if not _safe_file(entry):
            continue
        category = next((name for name, suffixes in CATEGORIES.items() if entry.suffix.lower() in suffixes), None)
        if category:
            destination = folder / category / entry.name
            if entry != destination and not destination.exists():
                planned.append((entry, destination))
    return planned

def apply_organization(plan):
    """Only apply reviewed plan; recheck paths and never overwrite."""
    moved = []
    for source, target in plan:
        if not _safe_file(source) or target.exists() or source.parent != target.parent.parent:
            continue
        target.parent.mkdir(exist_ok=True)
        if target.exists():
            continue
        shutil.move(str(source), str(target))
        moved.append((source, target))
    return moved


def undo_organization(moved):
    """Undo only moves whose source slot is free; never overwrite user files.

    The caller must pass the exact list returned by apply_organization.
    """
    restored = []
    skipped = []
    for source, target in reversed(list(moved)):
        source, target = pathlib.Path(source), pathlib.Path(target)
        if (not _safe_file(target) or source.exists() or source.is_symlink()
                or target.parent != source.parent / target.parent.name
                or target.parent.name not in CATEGORIES):
            skipped.append((source, target))
            continue
        try:
            target.rename(source)
            restored.append((source, target))
        except OSError:
            skipped.append((source, target))
    return restored, skipped

def disk_map(folder, limit=20000):
    """Read-only directory sizes, capped to avoid unbounded scans."""
    folder = pathlib.Path(folder).resolve(strict=True)
    if not folder.is_dir():
        raise ValueError("Dossier invalide")
    sizes = defaultdict(int)
    pending = [folder]
    scanned = 0
    while pending and scanned < limit:
        current = pending.pop()
        try:
            with os.scandir(current) as entries:
                for item in entries:
                    if scanned >= limit:
                        break
                    try:
                        if item.is_symlink():
                            continue
                        if item.is_dir(follow_symlinks=False):
                            pending.append(pathlib.Path(item.path))
                        elif item.is_file(follow_symlinks=False):
                            relative = pathlib.Path(item.path).relative_to(folder)
                            key = relative.parts[0] if len(relative.parts) > 1 else "(fichiers du dossier)"
                            sizes[key] += item.stat(follow_symlinks=False).st_size
                            scanned += 1
                    except OSError:
                        pass
        except OSError:
            pass
    return sorted(sizes.items(), key=lambda item: item[1], reverse=True), scanned, bool(pending)

def plan_backup(source, destination, limit=20000):
    """Preview only missing/changed files; no deletion or restoration implied."""
    source = pathlib.Path(source).resolve(strict=True)
    destination = pathlib.Path(destination).resolve()
    if not source.is_dir() or source == destination or source in destination.parents or destination in source.parents:
        raise ValueError("Choisis deux dossiers séparés, sans imbrication.")
    plan = []
    pending = [source]
    scanned = 0
    while pending and scanned < limit:
        folder = pending.pop()
        with os.scandir(folder) as entries:
            for entry in entries:
                if scanned >= limit:
                    break
                if entry.is_symlink():
                    continue
                if entry.is_dir(follow_symlinks=False):
                    pending.append(pathlib.Path(entry.path))
                elif entry.is_file(follow_symlinks=False):
                    scanned += 1
                    original = pathlib.Path(entry.path)
                    target = destination / original.relative_to(source)
                    st = original.stat()
                    try:
                        dt = target.stat()
                        changed = st.st_size != dt.st_size or st.st_mtime_ns != dt.st_mtime_ns
                    except FileNotFoundError:
                        changed = True
                    if changed:
                        plan.append((original, target))
    return plan, scanned, bool(pending)

def apply_backup(plan):
    """Copy only new files; never overwrite an existing backup."""
    copied = []
    for source, target in plan:
        if not _safe_file(source) or target.exists():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            continue
        with source.open("rb") as inp, target.open("xb") as out:
            shutil.copyfileobj(inp, out)
        shutil.copystat(source, target)
        copied.append(target)
    return copied
