"""Build dist/visitprep-source.zip from the files tracked by git, refusing to write the ZIP when a tracked file looks like it contains a ModelScope API key; known fake values used in tests and prompt logs (see KNOWN_FAKE_VALUES) are exempt from the env-key pattern. Only file names and line numbers are printed, never the matched text."""

import re
import subprocess
import sys
import zipfile
from pathlib import Path

_KEY_RE = re.compile(r"\bms-[A-Za-z0-9-]{20,}")
_ENV_KEY_RE = re.compile(r"MODELSCOPE_API_KEY\s*=\s*['\"]?([A-Za-z0-9-]{8,})")
# Fake values used in tests and prompt logs, not real keys.
KNOWN_FAKE_VALUES = frozenset({"sk-from-env-file", "sk-bom-key", "sk-file-key", "abcd1234efgh"})


def select_files(paths):
    selected = []
    for path in paths:
        if path == ".env":
            continue
        if path.startswith(".env.") and path != ".env.example":
            continue
        if path == "dist" or path.startswith("dist/"):
            continue
        if path.endswith(".pdf"):
            continue
        if "__pycache__" in path.split("/") or ".pytest_cache" in path.split("/"):
            continue
        selected.append(path)
    return selected


def find_secrets(text):
    hits = []
    for number, line in enumerate(text.splitlines(), start=1):
        env_hit = any(
            match.group(1) not in KNOWN_FAKE_VALUES for match in _ENV_KEY_RE.finditer(line)
        )
        if _KEY_RE.search(line) or env_hit:
            hits.append(number)
    return hits


def main():
    tracked = subprocess.run(
        ["git", "ls-files"], capture_output=True, text=True, check=True
    ).stdout.splitlines()
    files = select_files(tracked)
    problems = []
    for path in files:
        try:
            text = Path(path).read_bytes().decode("utf-8")
        except UnicodeDecodeError:
            continue
        for line in find_secrets(text):
            problems.append((path, line))
    if problems:
        for path, line in problems:
            print(f"{path}:{line}")
        sys.exit(1)
    out = Path("dist") / "visitprep-source.zip"
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in files:
            zf.write(path, path)
    for path in files:
        print(path)
    print(f"{len(files)} files")


if __name__ == "__main__":
    main()
