# Frontend Architecture

The application uses React 18, strict TypeScript, React Router, Axios, Tailwind CSS, and Vitest.

The current implementation adapts the existing single-module application into cohesive page functions. Shared behavior is centralized in API and auth modules, with reusable shell, page header, state, severity, and investigation components.

Authentication uses the backend bearer token contract. The token is held in memory backed by local storage for page refresh. Requests must receive a 401 from protected endpoints; authorization failures remain server enforced and navigation hiding is only UX.
