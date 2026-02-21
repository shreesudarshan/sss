# Secure Bloom SSE

Secure Bloom SSE is a full-stack application for encrypted patient-record storage with authenticated search.

Users can:
- register and sign in
- create patient records
- store those records in encrypted form
- search only their own records by protected search tokens

## Core Concept: Encrypted Searchable Strings
The central goal of this project is to support search without storing plaintext medical data in the database.

The implementation uses an SSE-style blind-index approach:
1. Patient payloads are encrypted with AES-GCM before persistence.
2. Searchable text fields are normalized and split into trigrams (3-character windows).
3. Each trigram is converted into a deterministic HMAC-SHA256 token.
4. Only tokens are indexed for search; plaintext search terms are never stored.
5. Query input follows the same normalization and tokenization process, then matches indexed tokens.

This enables partial-text matching while keeping record contents encrypted at rest.

## Security Model
- Confidentiality at rest: patient payloads are stored as AES-GCM ciphertext.
- Search privacy improvement: indexed values are HMAC tokens, not plaintext.
- User isolation: each query is scoped to the authenticated user account.
- Session security: login sessions are persisted using hashed session tokens.

This is an application-level security design for practical use. It is not positioned as a formally verified cryptographic protocol.

## Technology Stack
- Backend: FastAPI, SQLAlchemy (async), PostgreSQL
- Frontend: React, Vite, TypeScript
- Security primitives: AES-GCM, HMAC-SHA256, bcrypt

## Repository Structure
- `app`: backend source code
- `sss frontend`: frontend source code
- `setup.md`: complete installation and troubleshooting guide
- `.env.example`: environment variable template

## Getting Started
Use the setup guide first:
- `setup.md`

It includes:
- Python and Node.js installation
- virtual environment creation
- PostgreSQL setup
- backend and frontend startup commands
