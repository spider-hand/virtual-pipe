.DEFAULT_GOAL := dev

# Make treats positional migration arguments as goals; consume only those goals.
ifneq ($(filter migrate,$(MAKECMDGOALS)),)
ifneq ($(firstword $(MAKECMDGOALS)),migrate)
$(error migrate must be the first and only command)
endif
MIGRATION_ARGS := $(wordlist 2,3,$(MAKECMDGOALS))
ifneq ($(word 4,$(MAKECMDGOALS)),)
$(error Usage: make migrate [app [migration]])
endif
ifneq ($(filter dev down migrate migrate:show client:% server:% db:%,$(MIGRATION_ARGS)),)
$(error Do not combine migration arguments with other commands)
endif
.PHONY: $(MIGRATION_ARGS)
$(MIGRATION_ARGS):
	@:
endif

ifneq ($(filter migrate:show,$(MAKECMDGOALS)),)
ifneq ($(MAKECMDGOALS),migrate:show)
$(error migrate:show must be used alone)
endif
endif

quote = '$(subst ','"'"',$(1))'

.PHONY: dev down migrate migrate\:show
.PHONY: client\:format client\:format\:check client\:lint client\:test
.PHONY: server\:format server\:format\:check server\:lint server\:test
.PHONY: server\:schema client\:api\:generate
.PHONY: osm\:download osm\:import
.PHONY: db\:clean db\:functions

CLIENT_RUN = docker compose run --rm --no-deps -T client sh -c
SERVER_RUN = docker compose run --rm --no-deps -T server uv run --locked

dev:
	docker compose up

down:
	docker compose down

db\:clean:
	docker compose exec -T db psql -U virtual_pipe -d virtual_pipe -v ON_ERROR_STOP=1 -c 'TRUNCATE TABLE pipesets_pipe, pipesets_pipeset RESTART IDENTITY;'

db\:functions:
	docker compose exec -T db psql -U virtual_pipe -d virtual_pipe -v ON_ERROR_STOP=1 < db/functions/pipes_data.sql
	docker compose exec -T db psql -U virtual_pipe -d virtual_pipe -v ON_ERROR_STOP=1 < db/functions/pipes_mvt.sql

osm\:download:
	docker compose run --rm --no-deps osm sh -ec 'file=kanto-latest.osm.pbf; if [ ! -f "$$file" ]; then curl --fail --location --retry 3 --output "$$file.part" "https://download.geofabrik.de/asia/japan/$$file"; mv "$$file.part" "$$file"; fi'

osm\:import:
	docker compose build osm
	docker compose run --rm --no-deps osm osmium tags-filter /data/kanto-latest.osm.pbf w/highway --overwrite --output /data/kanto-roads.osm.pbf
	docker compose run --rm osm osm2pgsql --create --slim --drop --cache 512 --number-processes 2 --output flex --style /config/roads.lua /data/kanto-roads.osm.pbf

migrate:
	docker compose run --rm server uv run --locked python manage.py migrate $(foreach arg,$(MIGRATION_ARGS),$(call quote,$(arg)))

migrate\:show:
	docker compose run --rm server uv run --locked python manage.py showmigrations

client\:format:
	$(CLIENT_RUN) 'corepack pnpm install --frozen-lockfile && corepack pnpm format'

client\:format\:check:
	$(CLIENT_RUN) 'corepack pnpm install --frozen-lockfile && corepack pnpm format:check'

client\:lint:
	$(CLIENT_RUN) 'corepack pnpm install --frozen-lockfile && corepack pnpm lint'

client\:test:
	$(CLIENT_RUN) 'export PLAYWRIGHT_BROWSERS_PATH=/app/node_modules/.cache/ms-playwright && corepack pnpm install --frozen-lockfile && corepack pnpm exec playwright install --with-deps --only-shell chromium && corepack pnpm test:unit --run'

server\:format:
	$(SERVER_RUN) ruff format .

server\:format\:check:
	$(SERVER_RUN) ruff format --check .

server\:lint:
	$(SERVER_RUN) ruff check .

server\:test:
	docker compose run --rm -T server uv run --locked pytest || { status=$$?; test "$$status" -eq 5 || exit "$$status"; }

server\:schema:
	$(SERVER_RUN) python manage.py spectacular --file schema.yaml --validate --fail-on-warn

client\:api\:generate:
	$(MAKE) server:schema
	docker run --rm -v "$(CURDIR):/local" openapitools/openapi-generator-cli:v7.26.0 generate -i /local/server/schema.yaml -g typescript-fetch -o /local/client/src/services --global-property apis,models,apiDocs=false,modelDocs=false,apiTests=false,modelTests=false,supportingFiles=runtime.ts:index.ts --additional-properties=hideGenerationTimestamp=true
