# Setup Guide

## What Changed And Why

1. Hardcoded API responses were removed.
Why: The old backend returned fake patient data. Now it saves and reads real data.

2. Persistent PostgreSQL support was added.
Why: Data must stay after restart. In-memory and demo storage are not reliable.

3. Basic login and logout were added.
Why: The app now has real users and sessions, so data can be tied to the logged-in user.

4. User and auth tables were added.
Why: We need `users` and `sessions` tables for account and session management.

5. Patient logic was fixed to use real encrypted storage.
Why: Patient records are now encrypted before saving and decrypted when reading.

6. Search logic was fixed.
Why: Search now uses safe query logic and does not use risky string-built SQL.

7. Frontend was rebuilt from the default template.
Why: The app now has working pages for register, login, logout, create patient, and search patient.

8. Config moved to environment variables.
Why: Secrets and database settings should not be hardcoded in code.

9. Duplicate and temporary docs/files were removed.
Why: One main setup document is easier for new developers.

## File By File Purpose
This section explains what each important file does.

### Root
- `README.md`: quick project overview.
- `setup.md`: full setup and troubleshooting guide.
- `requirements.txt`: backend Python dependencies.
- `.env.example`: sample environment variables.
- `.gitignore`: files that should not be committed.

### Backend (`app`)
- `app/__init__.py`: loads env and configures shared logger.
- `app/settings.py`: reads environment settings and validates required values.
- `app/database.py`: database models, engine, session factory, and table initialization.
- `app/auth.py`: helper logic for password hashing and session token handling.
- `app/auth_routes.py`: API routes for register, login, logout, and current user.
- `app/encryption.py`: encrypt/decrypt service and token generation.
- `app/utils.py`: text normalization and trigram generation utilities.
- `app/routes.py`: patient create/search/get API routes.
- `app/main.py`: FastAPI app entrypoint and router registration.

### Frontend (`sss frontend`)
- `sss frontend/src/main.tsx`: React app entrypoint.
- `sss frontend/src/App.tsx`: main UI and API calls.
- `sss frontend/src/index.css`: global baseline styles.
- `sss frontend/src/App.css`: page and component styles.
- `sss frontend/vite.config.ts`: Vite build/dev config.
- `sss frontend/eslint.config.js`: lint rules for frontend code.
- `sss frontend/package.json`: frontend dependencies and scripts.
- `sss frontend/tsconfig.json`: TypeScript root configuration.
- `sss frontend/tsconfig.app.json`: TypeScript settings for browser app code.
- `sss frontend/tsconfig.node.json`: TypeScript settings for Node/Vite config.

## Setup
This section is written for a beginner who wants exact, copy-paste steps.

### 1. Install Python (Windows)
1. Download Python 3.11 or newer from:
- `https://www.python.org/downloads/windows/`
2. Run the installer and enable:
- `Add python.exe to PATH`
3. Open Command Prompt (`cmd`) and verify:

```cmd
python --version
pip --version
```

If `python` is not recognized, try:

```cmd
py --version
```

### 2. Install Node.js (Frontend + TypeScript Tooling)
1. Download Node.js 20 or newer from:
- `https://nodejs.org/`
2. Install with default settings.
3. Verify in `cmd`:

```cmd
node -v
npm -v
```

Important note:
- You do not need a global TypeScript install for this project.
- TypeScript is installed locally from `sss frontend/package.json` when you run `npm install`.

Optional version check after installing frontend dependencies:

```cmd
cd F:\SSS\sss frontend
npx tsc -v
```

### 3. Install PostgreSQL
Install PostgreSQL 16 or newer.

If you do not want to install PostgreSQL directly, use Docker instead.

### 4. Get The Project
Open Command Prompt (`cmd`) and run:

```cmd
cd F:\
git clone <your-repo-url> SSS
cd F:\SSS
```

If the folder is already there, just run:

```cmd
cd F:\SSS
```

### 5. Create PostgreSQL Database
Use one option below.

Option A: Native PostgreSQL
1. Open `SQL Shell (psql)` from Start Menu.
2. Run:

```sql
CREATE USER sss_user WITH PASSWORD 'sss_pass';
CREATE DATABASE sss_db OWNER sss_user;
GRANT ALL PRIVILEGES ON DATABASE sss_db TO sss_user;
```

### 6. Create Environment File
Create a file named `.env` in `F:\SSS` with this content:

```env
DATABASE_URL=postgresql+asyncpg://sss_user:sss_pass@localhost:5432/sss_db
AES_KEY=replace-with-a-strong-random-string
HMAC_KEY=replace-with-a-strong-random-string
APP_SECRET=replace-with-a-strong-random-string
SESSION_TTL_HOURS=168
CORS_ORIGINS=http://localhost:5173
BLOOM_FILTER_SIZE=50000
BLOOM_FILTER_HASH_COUNT=7
```

### 7. Create Virtual Environment And Start Backend
From `F:\SSS` run:

```cmd
python -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Backend should be available at:
- `http://localhost:8000`
- API docs: `http://localhost:8000/docs`

### 8. Start Frontend
Open a new Command Prompt (`cmd`) terminal and run:

```cmd
cd F:\SSS\sss frontend
npm install
set VITE_API_BASE_URL=http://localhost:8000
npm run dev
```

Frontend should be available at:
- `http://localhost:5173`

### 9. Use The App
1. Open `http://localhost:5173`.
2. Register a new account.
3. Login.
4. Create a patient record.
5. Search for the patient by name or diagnosis.
6. Logout.

### 10. Check Persistence
1. Stop backend server.
2. Start backend again.
3. Login again and search for the same patient.
4. If the record is still there, persistent database setup is correct.

## Troubleshooting
1. `connection refused`:
PostgreSQL is not running or wrong host/port in `DATABASE_URL`.

2. `password authentication failed`:
Username/password in `DATABASE_URL` does not match DB user.

3. CORS or login cookie issues:
Check `CORS_ORIGINS` and confirm frontend is running on `http://localhost:5173`.

4. Python module errors:
Make sure virtual environment is activated before running backend commands.
