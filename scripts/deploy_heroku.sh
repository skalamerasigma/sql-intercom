#!/usr/bin/env bash
set -euo pipefail

# Simple Heroku deploy helper for this app.
# Usage:
#   scripts/deploy_heroku.sh <heroku-app-name>
# Example:
#   scripts/deploy_heroku.sh sql-intercom

APP_NAME="${1:-}"
if [[ -z "${APP_NAME}" ]]; then
	echo "Usage: scripts/deploy_heroku.sh <heroku-app-name>"
	exit 1
fi

if ! command -v heroku >/dev/null 2>&1; then
	echo "Heroku CLI not found. Install: https://devcenter.heroku.com/articles/heroku-cli"
	exit 1
fi

# Check auth
if ! heroku auth:whoami >/dev/null 2>&1; then
	echo "You're not logged in to Heroku. Run: heroku login -i"
	exit 1
fi

# Create or connect remote
if ! heroku apps:info -a "${APP_NAME}" >/dev/null 2>&1; then
	echo "Creating Heroku app: ${APP_NAME}"
	heroku create "${APP_NAME}"
fi

if ! git remote get-url heroku >/dev/null 2>&1; then
	heroku git:remote -a "${APP_NAME}"
fi

# Ensure Python buildpack (idempotent)
if ! heroku buildpacks -a "${APP_NAME}" | grep -q "heroku/python"; then
	heroku buildpacks:add heroku/python -a "${APP_NAME}" >/dev/null
fi

# Load local .env if present for convenience (do not commit secrets)
if [[ -f ".env" ]]; then
	set -a
	# shellcheck disable=SC1091
	source .env
	set +a
fi

# Defaults for optional vars
INTERCOM_TEAM_ID="${INTERCOM_TEAM_ID:-5480079}"
SLA_FIRST_RESPONSE_MINUTES="${SLA_FIRST_RESPONSE_MINUTES:-15}"
REFRESH_INTERVAL_SECONDS="${REFRESH_INTERVAL_SECONDS:-30}"
PER_PAGE="${PER_PAGE:-150}"

if [[ -z "${INTERCOM_BEARER_TOKEN:-}" ]]; then
	echo "Missing INTERCOM_BEARER_TOKEN. Export it or put it in .env before running."
	exit 1
fi

echo "Setting Heroku config vars..."
heroku config:set -a "${APP_NAME}" \
	INTERCOM_BEARER_TOKEN="${INTERCOM_BEARER_TOKEN}" \
	INTERCOM_TEAM_ID="${INTERCOM_TEAM_ID}" \
	SLA_FIRST_RESPONSE_MINUTES="${SLA_FIRST_RESPONSE_MINUTES}" \
	REFRESH_INTERVAL_SECONDS="${REFRESH_INTERVAL_SECONDS}" \
	PER_PAGE="${PER_PAGE}"

echo "Pushing to Heroku..."
if ! git push heroku HEAD:main; then
	git push heroku HEAD:master
fi

# Ensure a web dyno is up
heroku ps:scale web=1 -a "${APP_NAME}" >/dev/null

echo "Opening app..."
heroku open -a "${APP_NAME}"

echo "Done."


