# Private Notes API

A Flask productivity backend with session authentication and private, user-owned notes. No frontend is included. Passwords are hashed with Flask-Bcrypt; the API validates input, scopes every note query to its owner, and paginates note lists.

## Setup

Use Python 3.12 and Pipenv. Dependencies match the lab's supplied versions.

```bash
pipenv install --dev
export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
pipenv run flask --app app:create_app db upgrade
pipenv run python seed.py
pipenv run flask --app app:create_app run --port 5555
```

Keep the same `SECRET_KEY` between restarts so valid sessions survive refreshes. `.env.example` lists configuration options; the application reads environment variables and does not automatically load `.env`. The default SQLite database is `instance/notes.db`, which is excluded from Git.

The seed script creates `alice` and `bob`, each with 15 notes, with development password `DemoPass123!`. It skips existing usernames and never clears the database. Do not seed demo accounts into a production database.

## Project layout

- `app.py`: application factory, configuration, CORS, and JSON errors.
- `extensions.py`: shared SQLAlchemy, Bcrypt, and Migrate extensions.
- `models.py`: User and Note models and public serialization.
- `security.py`: session authentication, origin checks, and CSRF protection.
- `validation.py`: request schemas and JSON validation.
- `routes/`: authentication and notes endpoints.
- `migrations/`: versioned database schema.
- `seed.py`: repeatable sample data.
- `tests/`: isolated API and security tests.

## Authentication and browser integration

### Implemented endpoints

| Method | Endpoint | Description | Success |
| --- | --- | --- | --- |
| POST | `/signup` | Register a unique username, hash the password, and start a session. | 201 |
| POST | `/login` | Authenticate with username/password and start a new session. | 200 |
| GET | `/check_session` | Return the signed-in user and CSRF token; return 401 when signed out. | 200 |
| DELETE | `/logout` | Clear the authenticated session. Requires CSRF header. | 204 |
| GET | `/notes` | List only your notes, newest ID first. Query: `page=1&per_page=10`. | 200 |

Note lists return `notes`, `page`, `per_page`, `total`, `pages`, `has_next`, and `has_prev`. Page must be positive; per-page size must be 1–100. Invalid pagination returns 400; empty and out-of-range pages return an empty `notes` array. All notes endpoints require authentication (401 when signed out).

`POST /signup` accepts `{"username":"alice","password":"password123"}` and returns `id`, `username`, and `csrf_token`. Usernames must contain 3–32 ASCII letters, digits, or underscores; they are case-sensitive. Passwords must contain 8–72 UTF-8 bytes. Duplicate usernames return 409, invalid fields return 422, malformed/empty JSON returns 400, unsupported content types return 415, and disallowed origins return 403. Unknown fields are rejected.

Use the provided **session** frontend. Send `credentials: "include"` with fetch requests. Set `FRONTEND_ORIGIN` to its exact origin (for example `http://localhost:5173`) to enable credentialed CORS. Use the same hostname for both apps (`localhost` for both, rather than mixing `localhost` and `127.0.0.1`). Default `SameSite=Lax` cookies support local development and same-site hosting; unrelated domains require a separate deployment/cookie configuration review.

All POST, PATCH, and DELETE requests require `Content-Type: application/json`; authenticated writes also require `X-CSRF-Token` using the token returned by authentication/session responses. DELETE may have an empty body but still needs the JSON content type. CSRF tokens rotate on signup/login. Login/signup also enforce allowed browser origins and JSON content types. Cookie session data is signed, not encrypted, and contains only a user ID and CSRF token. A session lasts at most 12 hours.

In HTTPS deployments set `COOKIE_SECURE=1`, use a private strong secret, and run behind a production WSGI server. The Flask development server is for local development. Add deployment-level rate limiting for public authentication endpoints. Flask's signed-cookie logout clears the client's cookie; it does not centrally revoke previously copied cookies.

## Checks

```bash
pipenv run python -m pytest -q
```

Tests use a separate in-memory SQLite database. For later schema changes:

```bash
pipenv run flask --app app:create_app db migrate -m "Describe the schema change"
pipenv run flask --app app:create_app db upgrade
```

## References

Session and CSRF decisions follow the [Flask security guidance](https://flask.palletsprojects.com/en/stable/web-security/). Migrations use [Flask-Migrate](https://flask-migrate.readthedocs.io/).
