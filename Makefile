.DEFAULT_GOAL := up

.PHONY: up down osm\:download osm\:import client\:format client\:format\:check client\:lint client\:test client\:api\:generate server\:format server\:format\:check server\:lint server\:test server\:schema

export REGION

up:
	docker compose up --build --detach

down:
	docker compose down

osm\:download:
	@sh osm/region.sh
	docker compose run --build --rm --no-deps -e REGION osm sh download.sh

osm\:import:
	@sh osm/region.sh
	docker compose run --build --rm -e REGION osm sh import.sh

client\:format:
	pnpm --dir client format

client\:format\:check:
	pnpm --dir client format:check

client\:lint:
	pnpm --dir client lint

client\:test:
	pnpm --dir client test:unit

client\:api\:generate:
	pnpm --dir client generate:api

server\:format:
	cd server && uv run --locked ruff format

server\:format\:check:
	cd server && uv run --locked ruff format --check

server\:lint:
	cd server && uv run --locked ruff check

server\:test:
	docker compose run --build --rm -T server uv run --locked pytest

server\:schema:
	docker compose run --build --rm -T server uv run --locked python manage.py spectacular --file openapi.yaml --validate --fail-on-warn
