"""Run an archived GTK application without colliding with the installed instance."""
import pathlib
import re
import runpy
import sys
import traceback

APP_ID = re.compile(r"(application_id\s*=\s*['\"])[^'\"]+(['\"])")

def prepare_source(source, version):
    suffix = "V" + re.sub(r"[^0-9A-Za-z]", "_", version)
    identifier = "io.github.gestionstockage.Archive" + suffix
    result, count = APP_ID.subn(lambda match: match.group(1) + identifier + match.group(2), source, count=1)
    if count != 1:
        raise ValueError("Impossible d'isoler l'identifiant GTK de cette ancienne version.")
    return result

def main():
    if len(sys.argv) != 3:
        raise SystemExit("Usage: archive_launcher.py SCRIPT VERSION")
    script = pathlib.Path(sys.argv[1]).resolve()
    version = sys.argv[2]
    if not re.fullmatch(r"[0-9]+(?:\.[0-9]+)*", version):
        raise ValueError("Version invalide")
    if script.name != "app.py" or script.parent.name != version or script.parent.parent != pathlib.Path(__file__).resolve().parent / "versions":
        raise ValueError("Archive invalide")
    source = script.read_text(encoding="utf-8")
    patched = prepare_source(source, version)
    sys.path.insert(0, str(script.parent))
    sys.argv = [str(script)]
    namespace = {"__name__": "__main__", "__file__": str(script), "__package__": None}
    exec(compile(patched, str(script), "exec"), namespace)

if __name__ == "__main__":
    try:
        main()
    except BaseException:
        traceback.print_exc()
        raise
