from pathlib import Path
from dotenv import load_dotenv

import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

ROOT_DIR = Path(__file__).resolve().parent

load_dotenv(ROOT_DIR.parent / ".env")
