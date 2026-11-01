# Rollback Procedure

1. Declare an incident and stop new deployments.
2. If application writes are unsafe, disable traffic at the load balancer.
3. Deploy the previous known-good API/frontend/worker images.
4. Verify `/health/live`, `/health/ready`, frontend availability, and worker logs.
5. Run smoke tests.
6. If the application release introduced only backward-compatible migrations, do not roll back the database schema.
7. If data was modified or a migration is backward-incompatible, restore only from a verified pre-deployment backup into an isolated database and switch traffic after integrity checks.
8. Record migration/manual recovery actions and preserve audit logs.

Rollback success criteria are live traffic health, database integrity, worker recovery, realtime delivery, and confirmation of the last accepted event processing state.
