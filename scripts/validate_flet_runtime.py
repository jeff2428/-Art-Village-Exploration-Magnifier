from __future__ import annotations

import argparse
import sys
from pathlib import Path

from verify_pages_deploy import has_valid_renderer_build

DEFAULT_BOOTSTRAP = Path("flet_app/build/web/flutter_bootstrap.js")


def validate_bootstrap(path: Path, renderer: str) -> list[str]:
    failures: list[str] = []
    if not path.exists():
        return [f"Missing Flutter bootstrap file: {path}"]
    bootstrap = path.read_text(encoding="utf-8", errors="replace")
    if not has_valid_renderer_build(bootstrap, renderer):
        failures.append(
            f"Flet runtime metadata is missing a valid {renderer} build in {path}. "
            "The deployed HTML would force that renderer and fail during startup."
        )
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Flet web runtime metadata before deployment.")
    parser.add_argument("--bootstrap", type=Path, default=DEFAULT_BOOTSTRAP)
    parser.add_argument("--renderer", default="skwasm")
    args = parser.parse_args()

    failures = validate_bootstrap(args.bootstrap, args.renderer)
    if failures:
        print("Flet runtime validation failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print(f"Flet runtime validation passed: {args.renderer} build metadata found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
