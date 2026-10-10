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
ifneq ($(filter dev down migrate migrate:show,$(MIGRATION_ARGS)),)
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

dev:
	docker compose up

down:
	docker compose down

migrate:
	docker compose run --rm server uv run --locked python manage.py migrate $(foreach arg,$(MIGRATION_ARGS),$(call quote,$(arg)))

migrate\:show:
	docker compose run --rm server uv run --locked python manage.py showmigrations
