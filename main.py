import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "flet_app"))


if __name__ == "__main__":
    exec(Path("flet_app/main.py").read_bytes())
