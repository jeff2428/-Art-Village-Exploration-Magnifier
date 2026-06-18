from __future__ import annotations

import os
import hashlib
import shutil
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "flet_app"
APP_PACKAGE = APP_DIR / "build" / "web" / "assets" / "app" / "app.zip"
APP_PACKAGE_CANDIDATES = (
    APP_PACKAGE,
    APP_DIR / "build" / "flutter" / "app" / "app.zip",
    APP_DIR / "build" / "flutter" / "build" / "web" / "assets" / "app" / "app.zip",
)
EXCLUDED_ARCHIVE_NAMES = {"js.py"}


def local_python_modules(app_dir: Path | None = None) -> dict[str, Path]:
    app_dir = app_dir or APP_DIR
    return {
        path.relative_to(app_dir).as_posix(): path
        for path in sorted(app_dir.rglob("*.py"))
        if "build" not in path.relative_to(app_dir).parts
        and "__pycache__" not in path.relative_to(app_dir).parts
        and path.name != "__init__.py"
        and path.name != "js.py"
    }


def extra_assets(root: Path | None = None) -> dict[str, Path]:
    root = root or ROOT
    animals = root / "admin" / "animals.json"
    assets: dict[str, Path] = {}
    if animals.exists():
        assets["admin/animals.json"] = animals
    shared_config = root / "shared" / "config.py"
    if shared_config.exists():
        assets["shared/config.py"] = shared_config
    return assets


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
                if (
                    info.filename in replacements
                    or info.filename in written
                    or info.filename in EXCLUDED_ARCHIVE_NAMES
                ):
                    continue
                target.writestr(info, source.read(info.filename))
                written.add(info.filename)

            for archive_name, source_path in replacements.items():
                target.write(source_path, archive_name)
                written.add(archive_name)

        shutil.move(str(temp_path), app_package)
        app_package.with_name(f"{app_package.name}.hash").write_text(
            hashlib.sha256(app_package.read_bytes()).hexdigest(),
            encoding="utf-8",
        )
    finally:
        if temp_path.exists():
            temp_path.unlink()

    return sorted(replacements)


def rewrite_existing_app_packages() -> dict[str, list[str]]:
    patched: dict[str, list[str]] = {}
    for app_package in APP_PACKAGE_CANDIDATES:
        if app_package.exists():
            patched[str(app_package)] = rewrite_app_package(app_package)
    if not patched:
        raise FileNotFoundError("No Flet app package found. Run `flet build web` or `flet run -w` first.")
    return patched


if __name__ == "__main__":
    patched_packages = rewrite_existing_app_packages()
    for package, patched in patched_packages.items():
        print(f"Patched Flet app package with local modules: {package}")
        for name in patched:
            print(f"  - {name}")
