from __future__ import annotations

import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB_DIR = ROOT / "flet_app" / "build" / "web"
APP_DIR = WEB_DIR / "assets" / "app"
REQUIREMENTS = ROOT / "flet_app" / "requirements.txt"


def size_bytes(path: Path) -> int | None:
    return path.stat().st_size if path.exists() else None


def app_package_modules(app_zip: Path) -> list[str]:
    if not app_zip.exists():
        return []
    with zipfile.ZipFile(app_zip) as archive:
        return sorted(
            name
            for name in archive.namelist()
            if name.endswith(".py") and "__pycache__" not in name
        )


def largest_files(root: Path, limit: int = 20) -> list[dict[str, int | str]]:
    if not root.exists():
        return []
    files = [path for path in root.rglob("*") if path.is_file()]
    files.sort(key=lambda path: path.stat().st_size, reverse=True)
    return [
        {
            "path": str(path.relative_to(root)).replace("\\", "/"),
            "bytes": path.stat().st_size,
        }
        for path in files[:limit]
    ]


def main() -> None:
    requirements = (
        [line.strip() for line in REQUIREMENTS.read_text(encoding="utf-8").splitlines() if line.strip()]
        if REQUIREMENTS.exists()
        else []
    )
    app_zip = APP_DIR / "app.zip"
    report = {
        "requirements": requirements,
        "build_web_bytes": sum(path.stat().st_size for path in WEB_DIR.rglob("*") if path.is_file())
        if WEB_DIR.exists()
        else None,
        "app_zip_bytes": size_bytes(app_zip),
        "app_zip_modules": app_package_modules(app_zip),
        "largest_build_files": largest_files(WEB_DIR),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
