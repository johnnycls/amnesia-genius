# Memory (memory.md)

This is your always-visible working memory, injected every turn.
You lose all conversation memory after this turn.
Put what the next turn needs to know here, and put things you only
need occasionally in separate files, linked from here.

A compact operational snapshot, not a diary. A filled-in template looks like:

# Goals
- finish the API migration; next milestone is updating the deployment script

# Current state
- tests pass locally; production deployment has not been attempted
- the migration script is in skills/migrate-api.py

# Decisions and constraints
- use the existing provider configuration; do not commit credentials

# User preferences
- prefer small, verified changes and concise summaries

# Next steps
- inspect the deployment workflow, then run the migration in staging

# Files
- skills/migrate-api.py - API migration program
- notes/api-migration.md - endpoint mapping and staging results

Replace this example with your real state. Keep it lean: prune completed
goals, stale facts, and finished steps; move large or occasional material
into dedicated files and link to them here.