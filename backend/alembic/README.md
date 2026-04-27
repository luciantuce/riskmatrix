# Database Migrations (Alembic)

All schema changes go through Alembic — never `Base.metadata.create_all`.

## Create a new migration after changing models

```bash
cd backend
alembic revision --autogenerate -m "describe the change"
```

Review the generated file in `alembic/versions/` before committing.
Autogenerate is a starting point, not the final word — always check it.

## Apply migrations

```bash
alembic upgrade head
```

## Roll back one step

```bash
alembic downgrade -1
```

## Inspect current version

```bash
alembic current
alembic history
```

## Railway

The backend's `start.sh` runs `alembic upgrade head` automatically on boot,
so every deploy picks up pending migrations.
