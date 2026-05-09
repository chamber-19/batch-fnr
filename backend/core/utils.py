from pathlib import Path


def find_dwg_files(folder: str) -> list[str]:
    base = Path(folder)
    if not base.exists() or not base.is_dir():
        raise FileNotFoundError(f"Folder does not exist: {folder}")

    matches: list[str] = []
    for path in base.rglob("*"):
        if path.is_file() and path.suffix.lower() == ".dwg":
            matches.append(str(path.resolve()))

    return sorted(matches)
