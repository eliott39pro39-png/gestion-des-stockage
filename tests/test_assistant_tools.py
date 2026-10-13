"""Local assistant regression tests: no overwrite, bounded search, symlinks skipped."""
import pathlib
import tempfile
import assistant_tools as a

with tempfile.TemporaryDirectory() as temp:
    root=pathlib.Path(temp)
    (root/"Steam").mkdir()
    (root/"Steam"/"steam.txt").write_text("original")
    (root/"notes.txt").write_text("notes")
    assert any(p.name=="Steam" for p in a.search_items(root,"steam")[0])
    assert any(p.name=="steam.txt" for p in a.search_items(root,"steam")[0])
    assert not a.search_items(root,"missing")[0]
    source,target=a.preview_rename(root/"notes.txt","renamed.txt")
    assert a.confirm_rename(source,target)==target
    assert target.read_text()=="notes"
    assert not source.exists()
    (root/"occupied.txt").write_text("keep")
    try:
        a.preview_rename(target,"occupied.txt")
        raise AssertionError("existing target accepted")
    except FileExistsError:
        pass
    try:
        a.preview_rename(target,"../bad")
        raise AssertionError("path traversal accepted")
    except ValueError:
        pass
    try:
        (root/"shortcut").symlink_to(root/"Steam",target_is_directory=True)
        assert all(p.name!="shortcut" for p in a.search_items(root,"shortcut")[0])
    except (OSError,NotImplementedError):
        pass

    # Search understands common French requests and file types.
    (root/"photo-vacances.jpg").write_bytes(b"image")
    (root/"rapport.pdf").write_bytes(b"pdf")
    (root/"résumé-été.txt").write_text("accents")
    assert any(p.name=="résumé-été.txt" for p in a.search_items(root,"resume ete")[0])
    assert a.normalize_query("Trouve mes photos") == ["image"]
    assert a.normalize_query("Cherche le fichier rapport.pdf") == ["rapport.pdf"]
    assert any(p.name=="photo-vacances.jpg" for p in a.search_items(root,"trouve mes photos")[0])
    assert any(p.name=="rapport.pdf" for p in a.search_items(root,"cherche mes pdfs")[0])
    import threading
    stop=threading.Event()
    stop.set()
    assert a.search_items(root,"rapport",cancel=stop)[1]
    progress=[]
    a.search_items(root,"missing",progress=lambda count,path:progress.append(count))
    assert progress and progress[-1]>0

print("Assistant guided tests passed")
