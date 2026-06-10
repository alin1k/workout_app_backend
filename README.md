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

## Smoke test

```bash
curl localhost:5000/health

curl -X POST localhost:5000/api/exercise-types \
  -H 'Content-Type: application/json' \
  -d '{"name":"Bench Press","muscle_group":"chest"}'

curl -X POST localhost:5000/api/workouts \
  -H 'Content-Type: application/json' \
  -d '{"name":"Push day"}'

curl -X POST localhost:5000/api/workouts/1/exercises \
  -H 'Content-Type: application/json' \
  -d '{"exercise_type_id":1}'

curl -X POST localhost:5000/api/exercises/1/sets \
  -H 'Content-Type: application/json' \
  -d '{"reps":10,"weight":60}'

curl localhost:5000/api/workouts/1   # full nested tree
```

## Logs

```bash
docker compose logs -f web    # follow Flask logs
docker compose logs -f db     # follow Postgres logs
docker compose logs -f        # both, interleaved
```
