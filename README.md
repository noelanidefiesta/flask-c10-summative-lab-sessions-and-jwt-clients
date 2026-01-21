# Productivity App API (Flask)

This repo contains two provided React clients (one using sessions and one using JWT) plus a Flask backend API.

This backend implements:
- Session-based authentication (signup, login, logout, check session)
- A user-owned resource: **Notes**
- Full CRUD for notes
- Pagination for the notes index route
- Access control so users can only access their own notes

## Setup

### 1) Install dependencies

```bash
pipenv install
pipenv shell
```

### 2) Initialize the database

From the repo root:

```bash
cd server
python seed.py
```

This will create `app.db` (SQLite) and seed example users and notes.

### 3) Run the API

From the `server/` folder:

```bash
python app.py
```

The API runs on `http://localhost:5555`.

## Using the provided sessions client

The sessions client makes requests to:
- `POST /signup`
- `POST /login`
- `DELETE /logout`
- `GET /check_session`

To use it in development, you typically run the Flask API on port 5555 and configure your React dev server proxy to point to it (or run them behind the same origin in production).

## API Endpoints

### Auth (Sessions)

- `POST /signup`
  - Body: `{ "username": "...", "password": "...", "password_confirmation": "..." }`
  - Returns: user JSON

- `POST /login`
  - Body: `{ "username": "...", "password": "..." }`
  - Returns: user JSON

- `DELETE /logout`
  - Logs out the current user

- `GET /check_session`
  - Returns the logged-in user if a session exists

### Notes (User-owned resource)

All notes routes require authentication.

- `GET /notes`
  - Query params: `page` (default 1), `per_page` (default 10)
  - Returns: `{ notes: [...], page, per_page, total, pages }`

- `POST /notes`
  - Body: `{ "title": "...", "content": "..." }`
  - Returns: created note JSON

- `GET /notes/<id>`
  - Returns: note JSON

- `PATCH /notes/<id>`
  - Body (any): `{ "title": "..." }`, `{ "content": "..." }`
  - Returns: updated note JSON

- `DELETE /notes/<id>`
  - Deletes a note

## Running tests

This repo includes a small pytest suite for the backend.

From the repo root:

```bash
pipenv run pytest -x
```
