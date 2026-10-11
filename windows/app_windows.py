#!/usr/bin/env python3
"""Windows adapter for the GTK4 storage manager.

Keep the Linux application unchanged. Windows-specific operations are replaced
with Windows-safe equivalents; deletion always requires confirmation.
"""
import os
import sys
import pathlib
import subprocess
import tempfile
import shutil
import importlib.util

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location("gestion_stockage_linux_core", ROOT / "app.py")
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)

from gi.repository import Gtk, Gio
from send2trash import send2trash

core.APP = "Gestion de stockage Windows"
core.CONFIG = pathlib.Path(os.environ.get("APPDATA", pathlib.Path.home())) / "GestionStockageWindows" / "settings.json"

def win_trash(self, *_):
    p = self.selected()
    if p:
        self.dialog("Mettre à la corbeille Windows ?", str(p),
                    lambda: self.perform(lambda: send2trash(str(p)), "Élément placé dans la corbeille"))

def win_trash_page(self, *_):
    self.clear()
    self.mark_page("Corbeille")
    self.heading("🗑️ Corbeille Windows")
    self.info("La restauration des fichiers se fait dans la corbeille de Windows.")
    def launch(*_):
        try:
            os.startfile("shell:RecycleBinFolder")
        except OSError as exc:
            self.dialog("Impossible d’ouvrir la corbeille", str(exc))
    self.btn(self.content, "Ouvrir la corbeille Windows", launch)

def win_games(self, *_):
    self.clear()
    self.mark_page("Jeux & applis")
    self.heading("JEUX & APPLICATIONS  ◇")
    self.info("Raccourcis vers les emplacements Windows détectés. Aucun programme n’est modifié.")
    paths = [
        ("Programmes", pathlib.Path(os.environ.get("ProgramFiles", "C:/Program Files"))),
        ("Programmes x86", pathlib.Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)"))),
        ("Applications utilisateur", pathlib.Path(os.environ.get("LOCALAPPDATA", str(pathlib.Path.home())))),
        ("Steam", pathlib.Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)")) / "Steam"),
        ("Jeux", pathlib.Path.home() / "Games"),
    ]
    for name, p in paths:
        if p.is_dir():
            self.btn(self.content, "📂 " + name + " — " + str(p), lambda _b, p=p: self.open_dir(p))

def win_cache_paths():
    local = pathlib.Path(os.environ.get("LOCALAPPDATA", str(pathlib.Path.home())))
    return [("Cache des miniatures Windows", local / "Microsoft" / "Windows" / "Explorer"),
            ("Cache Python pip", local / "pip" / "Cache")]

def win_cleanup(self, *_):
    self.clear()
    self.mark_page("Fichiers inutiles")
    self.heading("FICHIERS INUTILES  ◎")
    self.info("Inspection uniquement : aucun cache Windows n’est supprimé par cette page.")
    for title, path in win_cache_paths():
        if path.is_dir() and not path.is_symlink():
            self.info(title + " : " + str(path))
            self.btn(self.content, "Ouvrir " + title, lambda _b, p=path: self.open_dir(p))

def win_clean(self, *_):
    self.clear()
    self.mark_page("Nettoyage")
    self.heading("NETTOYAGE SÉCURISÉ  ✦")
    self.info("Consulte les caches et l’espace disque. Aucune suppression massive automatique.")
    cache = pathlib.Path(os.environ.get("TEMP", tempfile.gettempdir()))
    if cache.is_dir():
        self.btn(self.content, "📂 Inspecter le dossier temporaire", lambda *_: self.open_dir(cache))
    self.info("Pour le nettoyage du système, utilise les paramètres de stockage de Windows.")

core.Window.trash = win_trash
core.Window.trash_page = win_trash_page
core.Window.games = win_games
core.Window.cleanup_page = win_cleanup
core.Window.clean = win_clean

if __name__ == "__main__":
    sys.exit(core.App().run(sys.argv))
