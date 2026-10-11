"""Generate launchable old-version snapshots from Git history during packaging."""
import pathlib
import re
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "versions"
VERSION_PATTERN = re.compile(r"^VERSION=['\"]([0-9]+(?:\.[0-9]+){1,2})['\"]", re.M)
MODULES = ("app.py", "assistant_tools.py", "assistant_history.py", "smart_organizer.py", "mountain-bg.png")

def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=True).stdout

def main():
    current = VERSION_PATTERN.search((ROOT / "app.py").read_text(encoding="utf-8"))
    if not current:
        raise SystemExit("No current version")
    seen = {current.group(1)}
    try:
        commits = git("log", "--format=%H", "--", "app.py").decode().splitlines()
    except (OSError, subprocess.CalledProcessError):
        print("Git history unavailable: keeping bundled archives")
        return
    for commit in commits:
        try:
            source = git("show", f"{commit}:app.py")
        except subprocess.CalledProcessError:
            continue
        match = VERSION_PATTERN.search(source.decode("utf-8", errors="replace"))
        if not match:
            continue
        version = match.group(1)
        if version in seen:
            continue
        seen.add(version)
        destination = ARCHIVE / version
        if (destination / "app.py").exists():
            continue
        destination.mkdir(parents=True, exist_ok=True)
        for name in MODULES:
            try:
                data = git("show", f"{commit}:{name}")
            except subprocess.CalledProcessError:
                continue
            (destination / name).write_bytes(data)
        print("Archived", version)

if __name__ == "__main__":
    main()
