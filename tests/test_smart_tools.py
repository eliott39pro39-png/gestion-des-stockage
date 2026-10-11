"""Safety regression tests for proposed organization and backup tools."""
import pathlib
import tempfile
import smart_tools

with tempfile.TemporaryDirectory() as temp:
    root = pathlib.Path(temp)
    incoming = root / "incoming"
    incoming.mkdir()
    (incoming / "photo.jpg").write_bytes(b"image")
    (incoming / "report.pdf").write_bytes(b"pdf")
    (incoming / "unknown.foo").write_bytes(b"other")
    (incoming / "Documents").mkdir()
    (incoming / "Documents" / "report.pdf").write_bytes(b"KEEP")
    plan = smart_tools.plan_organization(incoming)
    assert [source.name for source, _ in plan] == ["photo.jpg"]
    smart_tools.apply_organization(plan)
    assert (incoming / "Images" / "photo.jpg").read_bytes() == b"image"
    assert (incoming / "Documents" / "report.pdf").read_bytes() == b"KEEP"
    assert (incoming / "report.pdf").exists()
    data, scanned, _ = smart_tools.disk_map(incoming)
    assert scanned >= 3 and data
    backup = root / "backup"
    backup.mkdir()
    (backup / "report.pdf").write_bytes(b"PREVIOUS BACKUP")
    planned, _, _ = smart_tools.plan_backup(incoming, backup)
    smart_tools.apply_backup(planned)
    assert (backup / "report.pdf").read_bytes() == b"PREVIOUS BACKUP"
    assert (backup / "Images" / "photo.jpg").read_bytes() == b"image"
    try:
        smart_tools.plan_backup(incoming, incoming / "inside")
        raise AssertionError("nested destination must be refused")
    except ValueError:
        pass
print("Safe storage tools tests passed")

# Undo must restore only safe files and preserve any new file at the original path.
with tempfile.TemporaryDirectory() as temp:
    root = pathlib.Path(temp)
    incoming = root / "incoming"
    incoming.mkdir()
    (incoming / "picture.png").write_bytes(b"original")
    plan = smart_tools.plan_organization(incoming)
    moved = smart_tools.apply_organization(plan)
    assert len(moved) == 1
    (incoming / "picture.png").write_bytes(b"new")
    restored, skipped = smart_tools.undo_organization(moved)
    assert not restored and len(skipped) == 1
    assert (incoming / "picture.png").read_bytes() == b"new"
    (incoming / "picture.png").unlink()
    restored, skipped = smart_tools.undo_organization(moved)
    assert len(restored) == 1 and not skipped
    assert (incoming / "picture.png").read_bytes() == b"original"
