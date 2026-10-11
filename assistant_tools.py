"""Assistant guidé local : recherches bornées et renommage explicitement confirmé."""
import os
import pathlib

def search_items(folder, query, limit=30, max_entries=12000):
    root = pathlib.Path(folder).expanduser()
    if not root.is_dir() or root.is_symlink():
        raise ValueError("Choisis un dossier accessible, sans lien symbolique.")
    query = query.strip().casefold()
    if not query:
        raise ValueError("Indique un nom de fichier ou de dossier.")
    matches, pending, visited = [], [root], 0
    while pending and visited < max_entries and len(matches) < limit:
        current = pending.pop()
        try:
            with os.scandir(current) as entries:
                for entry in entries:
                    if visited >= max_entries or len(matches) >= limit:
                        break
                    visited += 1
                    try:
                        if entry.is_symlink():
                            continue
                        is_dir = entry.is_dir(follow_symlinks=False)
                        if query in entry.name.casefold():
                            matches.append(pathlib.Path(entry.path))
                        if is_dir:
                            pending.append(pathlib.Path(entry.path))
                    except OSError:
                        continue
        except OSError:
            continue
    return matches, bool(pending) or visited >= max_entries

def preview_rename(path, new_name):
    source = pathlib.Path(path)
    name = new_name.strip()
    if (not name or name in (".", "..") or "/" in name or "\\" in name
            or "\x00" in name or pathlib.Path(name).name != name
            or (os.name == "nt" and (name.endswith(".") or name.endswith(" ")))):
        raise ValueError("Nom de fichier invalide.")
    if source.is_symlink() or not source.exists():
        raise ValueError("Fichier introuvable ou lien symbolique.")
    target = source.with_name(name)
    if target == source or target.exists():
        raise FileExistsError("Le nom existe déjà ou est inchangé.")
    return source, target

def confirm_rename(source, target):
    source, expected = preview_rename(source, pathlib.Path(target).name)
    if expected != pathlib.Path(target):
        raise ValueError("La destination a changé.")
    source.rename(expected)
    return expected
