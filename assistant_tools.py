"""Assistant guidé local : recherches bornées et renommage explicitement confirmé."""
import os
import pathlib
import unicodedata

def normalize_name(value):
    """Accent-insensitive case-folding for matching filenames."""
    value = unicodedata.normalize("NFKD", str(value).casefold())
    return "".join(c for c in value if not unicodedata.combining(c))


def normalize_query(query):
    """Convert common French requests into searchable filename terms."""
    import re
    q = normalize_name(query)
    q = re.sub(r"[^\w. -]", " ", q)
    words = q.split()
    stop = {"trouve", "trouver", "cherche", "chercher", "recherche", "rechercher",
            "retrouve", "retrouver", "montre", "affiche", "moi", "mes", "mon",
            "ma", "les", "des", "du", "de", "le", "la", "un", "une", "fichier",
            "fichiers", "dossier", "dossiers", "tous", "toutes", "dans", "sur",
            "ordinateur", "disque", "stp", "svp", "je", "veux", "ou", "sont"}
    aliases = {"photos": "image", "photo": "image", "images": "image",
               "pdfs": "pdf", "documents": "document", "videos": "video"}
    terms = [aliases.get(w, w) for w in words if w not in stop]
    return terms or words


def search_items(folder, query, limit=30, max_entries=12000,
                 progress=None, cancel=None):
    """Bounded, cancellable traversal; progress callback receives scanned count."""
    root = pathlib.Path(folder).expanduser()
    if not root.is_dir() or root.is_symlink():
        raise ValueError("Choisis un dossier accessible, sans lien symbolique.")
    terms = normalize_query(query)
    if not terms:
        raise ValueError("Indique un nom de fichier ou de dossier.")
    extensions = {"image": {".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic"},
                  "video": {".mp4", ".mov", ".avi", ".mkv"},
                  "document": {".pdf", ".doc", ".docx", ".odt", ".txt"},
                  "pdf": {".pdf"}}
    matches, pending, visited = [], [root], 0
    truncated = False
    while pending and visited < max_entries and len(matches) < limit:
        if cancel is not None and cancel.is_set():
            return matches, True
        current = pending.pop()
        try:
            with os.scandir(current) as entries:
                for entry in entries:
                    if cancel is not None and cancel.is_set():
                        return matches, True
                    if visited >= max_entries or len(matches) >= limit:
                        truncated = True
                        break
                    visited += 1
                    if progress is not None and visited % 150 == 0:
                        progress(visited, str(current))
                    try:
                        if entry.is_symlink():
                            continue
                        is_dir = entry.is_dir(follow_symlinks=False)
                        name = normalize_name(entry.name)
                        def matches_term(term):
                            return (name.find(term) >= 0 or
                                    (not is_dir and term in extensions and
                                     pathlib.Path(name).suffix in extensions[term]))
                        if all(matches_term(t) for t in terms):
                            matches.append(pathlib.Path(entry.path))
                        if is_dir:
                            pending.append(pathlib.Path(entry.path))
                    except OSError:
                        continue
        except OSError:
            continue
    if progress is not None:
        progress(visited, str(root))
    return matches, truncated or bool(pending)

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
    if not source.is_file() or source.is_symlink():
        raise ValueError("Le renommage guidé accepte uniquement les fichiers ordinaires.")
    # Exclusive hard-link creation prevents overwriting a newly created target.
    os.link(source, expected, follow_symlinks=False)
    try:
        source.unlink()
    except OSError:
        expected.unlink()
        raise
    return expected
