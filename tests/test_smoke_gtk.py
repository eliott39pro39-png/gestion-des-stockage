"""Headless GTK4 smoke tests, run with xvfb-run and system Python."""
import pathlib
import tempfile
import time
from gi.repository import GLib
import app

application = app.App()
window = app.Window(application)
with tempfile.TemporaryDirectory() as directory:
    root = pathlib.Path(directory)
    (root / "folder").mkdir()
    (root / "a.txt").write_bytes(b"same content")
    (root / "b.txt").write_bytes(b"same content")
    (root / "different.txt").write_bytes(b"other")
    window.cwd = root
    window.files()
    assert len(window.entries) == 4
    window.toggle_file_view()
    assert window.file_view in ("grid", "list")
    window.toggle_file_view()
    window.duplicates_page()
    window.start_duplicates(str(root))
    deadline = time.monotonic() + 15
    while window._duplicates_busy and time.monotonic() < deadline:
        while GLib.MainContext.default().pending():
            GLib.MainContext.default().iteration(False)
        time.sleep(.02)
    assert not window._duplicates_busy, "Duplicate scan timed out"
    assert len(window.duplicate_groups) == 1
    assert len(window.duplicate_groups[0]) == 2
    assert not any(check.get_active() for check, _ in window.duplicate_checks)
    window.storage_detective()
    window.start_storage_scan(str(root))
    deadline = time.monotonic() + 15
    while window._storage_scanning and time.monotonic() < deadline:
        while GLib.MainContext.default().pending():
            GLib.MainContext.default().iteration(False)
        time.sleep(.02)
    assert not window._storage_scanning, "Storage scan timed out"
print("GUI and duplicate scan smoke tests OK")
