# Workout App Backend

Flask backend for a workout-tracking app. Both the Flask service and Postgres run as containers managed by Docker Compose. 

## Stack

- Flask 3 + Flask-SQLAlchemy + Flask-Migrate (Alembic)
- PostgreSQL 16
- Everything runs in containers; the host only needs Docker

## Setup

```bash
cp .env.example .env
```

You need Docker Desktop (or a compatible Docker engine + Compose v2) on PATH. No Python venv is required to *run* the app — only to develop with IDE autocomplete.

## Running

```bash
docker compose up        # foreground — Ctrl+C stops everything
docker compose up -d     # background
docker compose down      # stop + remove containers (keeps DB volume)
docker compose down -v   # also wipe the DB volume
```

What happens on `up`:
1. Postgres starts; healthcheck waits until it accepts connections.
2. The `web` container starts (only after Postgres is healthy).
3. `web` runs `flask db upgrade` to apply any pending migrations.
4. `web` starts the Flask dev server on `http://localhost:5000` with `--debug` (auto-reload).

Source code is bind-mounted (`./app`, `./migrations`) so edits trigger an immediate Flask reload — no rebuild needed.

## Dev seed data

On a dev `docker compose up`, `scripts/seed_dev.py` runs right after the migrations and makes sure the database has something to look at:

| Login | Password | Role |
|---|---|---|
| `admin` | `admin` | admin |
| `demo` | `demo` | normal user |

It also creates a small movement catalogue and a few weeks of workouts for each user. It is idempotent: users and movements are created only if missing, and workouts are added only to a seed user who has none, so your own data survives restarts. The two passwords and admin flags are put back to the values above on every start.

```bash
docker exec workout_app_web python -m scripts.seed_dev           # run it by hand
docker exec workout_app_web python -m scripts.seed_dev --reset   # wipe the seed users' workouts and re-create them
```

This never runs in production: only `docker-compose.override.yml` calls it, `scripts/` is excluded from the image by `.dockerignore`, and the script exits unless `FLASK_ENV=development`.

## Accounts

There is no self-registration. An administrator creates accounts from the app (**Account → Admin → Users → New account**), which calls `POST /api/v1/admin/users`. Accounts created this way are always normal users; the new user can change the password they were given from **Account → Reset password**.

The first administrator has to come from somewhere else. In dev the seed script above provides `admin`. Anywhere else — a fresh production database, or whenever you need another admin — use the CLI, which prompts for the password:

```bash
docker compose exec web flask --app app create-admin <username>
```

## Compose file layout

- `docker-compose.yml` — base definition shared by every environment.
- `docker-compose.override.yml` — dev-only extras (host DB port, source bind mounts, `--debug` Flask server). Compose loads this **automatically** on a bare `docker compose up`.
- `docker-compose.prod.yml` — prod-only extras (gunicorn, `restart: unless-stopped`, external `web` network). Loaded only when passed explicitly with `-f`.

Passing `-f` disables auto-loading of the override file, so the prod command never picks up dev settings.

## Running in prod

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

## Ports

- `5000` — Flask
- `5433` — Postgres (mapped from container's 5432; configurable via `POSTGRES_HOST_PORT` in `.env`)

## Generating migrations

Models live in `app/models/`. After changing them, generate a migration *inside* the running container:

```bash
docker compose exec web flask --app app db migrate -m "describe your change"
docker compose exec web flask --app app db upgrade   # or just restart compose
```

Other useful Alembic commands:

| Command | What it does |
|---|---|
| `docker compose exec web flask --app app db current` | Show current revision |
| `docker compose exec web flask --app app db history` | Show all revisions |
| `docker compose exec web flask --app app db downgrade <rev>` | Roll back |
| `docker compose exec web flask --app app db downgrade base` | Roll back everything |

## Rebuilding the image

After changing `requirements.txt` or `Dockerfile`:

```bash
docker compose build web
docker compose up
```

## Connecting from the host

If you want to poke at the database directly (psql, IDE plugin, etc.) it's reachable on the host at `localhost:5433`. The `DATABASE_URL` in `.env` points there for that purpose — the container uses a different URL (host `db`, port `5432`) injected by `docker-compose.yml`.

## Logs

```bash
docker compose logs -f web    # follow Flask logs
docker compose logs -f db     # follow Postgres logs
docker compose logs -f        # both, interleaved
```
