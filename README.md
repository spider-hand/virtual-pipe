# Virtual Pipe

## Local setup

Install Node.js 24, pnpm 10.32.1, Python 3.14, uv, GNU Make, Docker with Compose v2, and Lefthook. From the repository root, install the host dependencies and the Git hook.

```sh
pnpm --dir client install --frozen-lockfile
uv sync --project server --locked
lefthook install
```

Run `make up` and open [the Vue dev server](http://localhost:5173). The page is blank. In your browser’s Network panel, reload the page and inspect `GET /api/health/`. The response should be HTTP 200 with `{"status":"ok"}`. Use `make down` to stop both services.

To run without Compose, start Django with `uv run python manage.py runserver` from `server/` and Vite with `pnpm dev` from `client/`.

## Checks

| Task | Client | Server |
| --- | --- | --- |
| Format | `make client:format` | `make server:format` |
| Check formatting | `make client:format:check` | `make server:format:check` |
| Lint | `make client:lint` | `make server:lint` |
| Unit tests | `make client:test` | `make server:test` |

Lefthook runs the format checks, lint, and unit tests before each commit. Run `lefthook run pre-commit --all-files` to check both projects on demand.

## Update the API client

After changing a Django REST endpoint, run the following commands from the root with Docker running.

```sh
make server:schema
make client:api:generate
```

If an API or model was removed or renamed, clear `client/src/services/` before running `make client:api:generate` to remove obsolete files. Review and commit the generated changes with the endpoint change.
