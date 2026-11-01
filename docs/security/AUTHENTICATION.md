# Authentication

## Passwords

Passwords are hashed with Argon2id. Passwords must contain 12 to 128 characters in API schemas. Existing 64-character hexadecimal SHA-256 hashes are verified only for login migration; successful verification transparently replaces the stored hash with Argon2id.

## Tokens

Access tokens are short-lived JWTs. Refresh tokens are longer-lived JWTs stored only as SHA-256 lookup hashes in `refresh_token_sessions`. Refresh rotation creates a new session in the same family, revokes the prior session, and revokes the entire family if an already-used token is presented.

Production JWT issuer/audience validation is optional but configured through `JWT_ISSUER` and `JWT_AUDIENCE`.

## Password reset

Reset tokens are random, hashed at rest, single-use, and expire after a configurable interval. A successful reset invalidates remaining reset tokens and all active refresh families. Development responses may include a token; production responses never do.

## Sessions

The frontend keeps an access token only in memory. Refresh cookies are not implemented in this revision. Deployments should terminate TLS and use a shared rate-limit store for multiple workers; the development in-memory limiter is explicitly process-local.

## Environment

See `.env.example` for required variables, including separate access and refresh signing secrets, issuer/audience, reset expiry, and authentication limits.
