from __future__ import annotations

import os
import shutil
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "flet_app"
APP_PACKAGE = APP_DIR / "build" / "web" / "assets" / "app" / "app.zip"


def local_python_modules(app_dir: Path | None = None) -> dict[str, Path]:
    app_dir = app_dir or APP_DIR
    return {
        path.name: path
        for path in sorted(app_dir.glob("*.py"))
        if path.name != "__init__.py"
    }


def extra_assets(root: Path | None = None) -> dict[str, Path]:
    root = root or ROOT
    animals = root / "admin" / "animals.json"
    return {"admin/animals.json": animals} if animals.exists() else {}


def rewrite_app_package(app_package: Path = APP_PACKAGE) -> list[str]:
    if not app_package.exists():
        raise FileNotFoundError(f"Flet app package not found: {app_package}")

    replacements = {**local_python_modules(), **extra_assets()}
    if "main.py" not in replacements:
        raise FileNotFoundError("Expected flet_app/main.py to exist")

    fd, temp_name = tempfile.mkstemp(suffix=".zip", prefix="flet-app-")
    os.close(fd)
    temp_path = Path(temp_name)
    written: set[str] = set()

    try:
        with zipfile.ZipFile(app_package, "r") as source, zipfile.ZipFile(
            temp_path,
            "w",
            compression=zipfile.ZIP_DEFLATED,
        ) as target:
            for info in source.infolist():
                if info.filename in replacements or info.filename in written:
                    continue
                target.writestr(info, source.read(info.filename))
                written.add(info.filename)

            for archive_name, source_path in replacements.items():
                target.write(source_path, archive_name)
                written.add(archive_name)

        shutil.move(str(temp_path), app_package)
    finally:
        if temp_path.exists():
            temp_path.unlink()

    return sorted(replacements)


if __name__ == "__main__":
    patched = rewrite_app_package()
    print("Patched Flet app package with local modules:")
    for name in patched:
        print(f"  - {name}")
