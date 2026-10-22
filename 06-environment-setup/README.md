# Video 6 – Environment Setup Like a Pro

Set up once, use for the whole playlist: **Python + virtual environment + VS Code + Git**.

## 1. Install Python (3.10 or newer – latest stable recommended)
| OS | How |
|----|-----|
| Windows | Download from **python.org** → run installer → ✅ tick **"Add python.exe to PATH"** |
| macOS | Download from **python.org** (or `brew install python`) |
| Linux (Ubuntu) | `sudo apt install python3 python3-venv python3-pip` |

Check: `python --version` (on Mac/Linux you may need `python3`).

## 2. Create the project and a virtual environment
```bash
mkdir course-hub
cd course-hub
python -m venv .venv
```
Activate it:
| OS | Command |
|----|---------|
| Windows (PowerShell / CMD) | `.venv\Scripts\activate` |
| macOS / Linux | `source .venv/bin/activate` |

You'll see `(.venv)` at the start of your terminal line. Deactivate with `deactivate`.

> **PowerShell error "running scripts is disabled"?** Run once:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

## 3. Install FastAPI and save your dependencies
```bash
pip install "fastapi[standard]"
pip freeze > requirements.txt          # save exact versions
pip install -r requirements.txt        # recreate on another machine
```
Optional faster tool: **uv** (`pip install uv`, then `uv venv` and `uv pip install "fastapi[standard]"`).

## 4. VS Code
1. Install from **code.visualstudio.com**
2. Extensions: **Python** (Microsoft) – includes **Pylance**
3. `Ctrl+Shift+P` → **Python: Select Interpreter** → choose the one inside `.venv`

## 5. Git
```bash
git --version
git config --global user.name "Your Name"
git config --global user.email "you@example.com"

git init
git add .
git commit -m "First commit"
```
Copy this folder's `.gitignore` into your project – **never commit `.venv` or `.env`**.

Get the course code: `git clone https://github.com/nileshborate/fastapi.git`

## 6. Check everything
```bash
python check_setup.py
fastapi dev main.py        # open http://127.0.0.1:8000 and /docs
```

## Interview questions
1. **Why use a virtual environment?** Each project gets its own isolated packages and versions, so projects don't conflict and setups are reproducible.
2. **What is `requirements.txt` for?** It lists the project's dependencies (often with exact versions via `pip freeze`) so anyone can install the same set with `pip install -r requirements.txt`.
3. **Why don't we commit `.venv` to Git?** It's large, OS-specific and can be recreated from `requirements.txt`; add it to `.gitignore` (along with secrets like `.env`).

## Homework
1. Create a `course-hub` folder with a `.venv`, install FastAPI, and save `requirements.txt`.
2. Run `python check_setup.py` until every line says **[OK]**.
3. Add a `.gitignore`, make your first commit, and push it to a new repo on your GitHub.
Answer (all commands) at the start of Video 7.
