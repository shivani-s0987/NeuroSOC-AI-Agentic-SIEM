#!/usr/bin/env sh
set -eu

base_url=${1:-http://localhost:8000}
suffix=$(date +%s)
username="smoke-${suffix}"
password='SmokePassword123!'

curl -fsS "$base_url/health" >/dev/null
registration=$(curl -fsS -X POST "$base_url/auth/register" \
  -H 'Content-Type: application/json' \
  -d '{"username":"'"$username"'","email":"'"$username"'@example.com","password":"'"$password"'"}')
test -n "$registration"

tokens=$(curl -fsS -X POST "$base_url/auth/login" \
  -H 'Content-Type: application/json' \
  -d '{"username":"'"$username"'","password":"'"$password"'"}')
token=$(printf '%s' "$tokens" | python3 -c 'import json,sys; print(json.load(sys.stdin)["access_token"])')

curl -fsS "$base_url/auth/me" -H "Authorization: Bearer $token" >/dev/null
summary=$(curl -fsS "$base_url/analytics/summary" -H "Authorization: Bearer $token")
printf 'Docker smoke passed: %s\n' "$summary"
