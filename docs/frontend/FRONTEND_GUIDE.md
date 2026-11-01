# Frontend Guide

## Development

```bash
cd frontend
npm install
npm run dev
```

Set `VITE_API_URL` to the backend origin when it differs from `http://localhost:8000`.

## Validation

```bash
cd frontend
npm test -- --run
npm run build
```

Backend RBAC is authoritative. Viewer, analyst, and administrator navigation is derived from `/auth/me`, but every mutation still receives backend authorization.
