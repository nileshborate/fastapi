# Video 6 - Environment Setup Like a Pro
# Nilesh Technology - FastAPI Mastery: Zero to Production
#
# Checks that your machine is ready for the playlist.
# Run (inside your activated virtual environment):   python check_setup.py

import shutil
import subprocess
import sys


def ok(msg: str) -> None:
    print(f"  [OK]   {msg}")


def bad(msg: str) -> None:
    print(f"  [FIX]  {msg}")


print("Checking your FastAPI setup...\n")

# 1. Python version
v = sys.version_info
if v >= (3, 10):
    ok(f"Python {v.major}.{v.minor}.{v.micro}")
else:
    bad(f"Python {v.major}.{v.minor} found - please install Python 3.10 or newer")

# 2. Virtual environment
if sys.prefix != sys.base_prefix:
    ok(f"Virtual environment active: {sys.prefix}")
else:
    bad("No virtual environment active - run: python -m venv .venv  and activate it")

# 3. FastAPI installed
try:
    import fastapi
    ok(f"FastAPI {fastapi.__version__} installed")
except ImportError:
    bad('FastAPI not installed - run: pip install "fastapi[standard]"')

# 4. Git available
if shutil.which("git"):
    out = subprocess.run(["git", "--version"], capture_output=True, text=True).stdout.strip()
    ok(out)
else:
    bad("Git not found - install it from git-scm.com")

print("\nAll [OK]? You're ready for Video 7!")
