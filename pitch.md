# Secure Bloom SSE Hackathon Pitch

## 90-Second Pitch
Hi judges, we built **Secure Bloom SSE** to solve a real healthcare problem: teams need fast patient search, but storing searchable medical text in plaintext is a security risk.

Our app lets users register, log in, create patient records, and search records through a simple workflow.

Under the hood, when a patient is saved, we encrypt the full record with **AES-GCM** before it touches the database.

For search, we do not store plaintext terms. We normalize text, split it into trigrams, and convert each trigram into deterministic **HMAC-SHA256 tokens**. Search runs by matching tokens, not raw medical data.

So we get practical partial-text search while keeping sensitive content encrypted at rest.

Technically, this is a full-stack build: **FastAPI + async SQLAlchemy + PostgreSQL** on the backend, and **React + TypeScript + Vite** on the frontend, with session-based authentication and logout revocation.

In short, Secure Bloom SSE shows you can keep search usable and make privacy much stronger at the same time.

## Live Demo Talk Track
1. Register and log in.
2. Create a patient record (name, DOB, diagnosis).
3. Search by a name or diagnosis fragment.
4. Show matching results loading in real time.
5. Close with: "Data is encrypted at rest, and search works through HMAC token matching, not plaintext indexing."

## If Judges Ask "What's Next?"
1. Add ranking/relevance instead of token match-only search.
2. Add key rotation and stronger key management.
3. Harden the prototype for production and compliance-focused audits.
