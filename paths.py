import os, sys
from pathlib import Path

if getattr(sys, "frozen", False):
    DATA_DIR = str(Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "BharatOS")
else:
    DATA_DIR = str(Path(__file__).resolve().parent.parent)
Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
