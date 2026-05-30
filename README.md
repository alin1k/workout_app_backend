# Workout App Backend

Flask backend for a workout-tracking app. See `~/.claude/plans/i-want-to-build-snappy-dongarra.md` for the phased build plan.

## Phase 1 — In-memory controllers

No database, no auth. State lives in module-level dicts and is wiped on restart.

### Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### Run

```bash
python run.py
# or
flask --app app run --debug
```

The API is served at `http://localhost:5000`.

### Smoke test

```bash
# Health check
curl localhost:5000/health

# Create an exercise type
curl -X POST localhost:5000/api/exercise-types \
  -H 'Content-Type: application/json' \
  -d '{"name": "Bench Press", "muscle_group": "chest"}'

# Create a workout
curl -X POST localhost:5000/api/workouts \
  -H 'Content-Type: application/json' \
  -d '{"name": "Push day", "notes": "Felt strong"}'

# Add an exercise to the workout (replace IDs)
curl -X POST localhost:5000/api/workouts/1/exercises \
  -H 'Content-Type: application/json' \
  -d '{"exercise_type_id": 1}'

# Add sets to the exercise
curl -X POST localhost:5000/api/exercises/1/sets \
  -H 'Content-Type: application/json' \
  -d '{"reps": 10, "weight": 60}'

# Read the full nested workout
curl localhost:5000/api/workouts/1
```
