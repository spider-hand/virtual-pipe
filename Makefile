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
ifneq ($(filter dev down migrate migrate:show client:% server:%,$(MIGRATION_ARGS)),)
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

CLIENT_RUN = docker compose run --rm --no-deps -T client sh -c
SERVER_RUN = docker compose run --rm --no-deps -T server uv run --locked

dev:
	docker compose up

down:
	docker compose down

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
	$(CLIENT_RUN) 'corepack pnpm install --frozen-lockfile && corepack pnpm test:unit --run'

server\:format:
	$(SERVER_RUN) ruff format .

server\:format\:check:
	$(SERVER_RUN) ruff format --check .

server\:lint:
	$(SERVER_RUN) ruff check .

server\:test:
	docker compose run --rm -T server uv run --locked pytest || { status=$$?; test "$$status" -eq 5 || exit "$$status"; }
