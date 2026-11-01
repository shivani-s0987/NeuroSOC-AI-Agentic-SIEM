# Release Process

## Versioning

Use Semantic Versioning: `MAJOR.MINOR.PATCH`. Start release branches from an updated `main`, add notes to `CHANGELOG.md`, and tag the release commit as `vX.Y.Z`.

```bash
git tag -a vX.Y.Z -m "NeuroSOC vX.Y.Z"
git push origin vX.Y.Z
```

## Pre-release

1. Confirm CI backend, frontend, migration, container, and security jobs passed.
2. Review `CHANGELOG.md` and migration notes.
3. Back up production.
4. Execute migrations in staging with production-shaped data.
5. Run smoke tests and security review.

## Deployment

Production deployment requires environment protection and a human approval in the deployment platform. No workflow in this repository deploys a live environment automatically.

## Rollback

Stop application writes, restore traffic to the previous application image, and restore the database only when the migration is backward-incompatible. Follow [ROLLBACK_PROCEDURE.md](./ROLLBACK_PROCEDURE.md).
