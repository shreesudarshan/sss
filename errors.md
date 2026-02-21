# Clean Rebuild Commands (Windows PowerShell)

Run this full sequence to recreate virtual environment and install everything from scratch:

```powershell
cd F:\SSS

# 1) Remove old virtual environment (if it exists)
if (Test-Path .\venv) { Remove-Item -Recurse -Force .\venv }

# 2) Create fresh virtual environment
python -m venv venv

# 3) Activate it
.\venv\Scripts\Activate.ps1

# 4) Upgrade pip and install all project dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

# 5) Verify auth-related packages
python -m pip show passlib bcrypt

# 6) Start backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Expected versions after install:
- `passlib` = `1.7.4`
- `bcrypt` = `4.0.1`

If `bcrypt` is not `4.0.1`, run:

```powershell
pip uninstall -y bcrypt
pip install bcrypt==4.0.1
```
