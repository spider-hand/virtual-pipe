# Virtual Pipe

## Local setup

Install Node.js 24, pnpm 10.32.1, Python 3.14, uv, GNU Make, Docker with Compose v2, and Lefthook. From the repository root, install the host dependencies and the Git hook.

```sh
pnpm --dir client install --frozen-lockfile
uv sync --project server --locked
lefthook install
```

Run `make up` to start PostgreSQL with PostGIS, Django, and Vite. Open [the Vue dev server](http://localhost:5173). The page is blank. In your browser’s Network panel, reload the page and inspect `GET /api/health/`. The response should be HTTP 200 with `{"status":"ok"}`. Use `make down` to stop the services. PostgreSQL data and downloaded OSM extracts persist in Docker volumes.

To run Django and Vite on the host, start the database with `docker compose up --build --detach --wait db`. Run `uv run --locked python manage.py migrate` and `uv run --locked python manage.py runserver` from `server/`, then `pnpm dev` from `client/`. Django connects to PostgreSQL at `127.0.0.1:5432` by default. The local database, user, and password all default to `virtual_pipe`. Set `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD` in both environments if you use different credentials. For a separate host database, Django also accepts `POSTGRES_HOST` and `POSTGRES_PORT`.

## Import Japan roads

Start with Shikoku, the smallest Geofabrik region.

```sh
make osm:download REGION=shikoku
make osm:import REGION=shikoku
```

Both commands require a region. Choose `chubu`, `chugoku`, `hokkaido`, `kansai`, `kanto`, `kyushu`, `shikoku`, or `tohoku`. For nationwide coverage, use `REGION=japan` in both commands. The nationwide PBF alone is about 2.4 GB. Allow additional Docker disk space for import staging and the database. [Geofabrik Japan extracts](https://download.geofabrik.de/asia/japan.html)

The download updates the cached extract for that region. The import starts PostgreSQL if needed and uses the cached extract. A successful import replaces `osm.roads` with the selected extract's road centerlines. If the import fails, the previous roads remain available.

Road data is © OpenStreetMap contributors, available under the Open Database License. [OpenStreetMap copyright and license](https://www.openstreetmap.org/copyright)

## Checks

| Task | Client | Server |
| --- | --- | --- |
| Format | `make client:format` | `make server:format` |
| Check formatting | `make client:format:check` | `make server:format:check` |
| Lint | `make client:lint` | `make server:lint` |
| Unit tests | `make client:test` | `make server:test` |

Lefthook runs the format checks, lint, and unit tests before each commit. Run `lefthook run pre-commit --all-files` to check both projects on demand.

Server tests that access the database require a reachable PostgreSQL instance. The default local Compose user can create Django's test database.

## Update the API client

After changing a Django REST endpoint, run the following commands from the root with Docker running.

```sh
make server:schema
make client:api:generate
```

If an API or model was removed or renamed, clear `client/src/services/` before running `make client:api:generate` to remove obsolete files. Review and commit the generated changes with the endpoint change.
