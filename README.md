# Virtual Pipe

## Local setup

Install GNU Make and Docker with Compose v2.

Run `make up` from the repository root. Once the services start, visit `http://localhost:5173`. Run `make down` to stop the services. PostgreSQL data and downloaded OSM extracts persist in Docker volumes.

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

Install Node.js 24, pnpm 10.32.1, Python 3.14, uv, and Lefthook for the host-side checks and Git hook.

```sh
pnpm --dir client install --frozen-lockfile
uv sync --project server --locked
lefthook install
```

| Task | Client | Server |
| --- | --- | --- |
| Format | `make client:format` | `make server:format` |
| Check formatting | `make client:format:check` | `make server:format:check` |
| Lint | `make client:lint` | `make server:lint` |
| Unit tests | `make client:test` | `make server:test` |

Lefthook runs the format checks, lint, and unit tests before each commit. Run `lefthook run pre-commit --all-files` to check both projects on demand.

Server tests run in Docker Compose with GeoDjango's libraries installed. Keep Docker running for the Git hook. The test command starts the Compose database if needed, and the default database user can create Django's test database.

## Update the API client

After changing a Django REST endpoint, run the following commands from the root with Docker running.

```sh
make server:schema
make client:api:generate
```

If an API or model was removed or renamed, clear `client/src/services/` before running `make client:api:generate` to remove obsolete files. Review and commit the generated changes with the endpoint change.

## District search setup

Copy `N03-20260101.shp`, `N03-20260101.shx`, `N03-20260101.dbf`, `N03-20260101.prj`, and `N03-20260101.cpg` from the nationwide [MLIT download](https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-N03-2026.html) into the root `data/` directory. Run `make up`. The server prepares the local search catalog on first startup.

## Credits

District search uses [国土数値情報（行政区域データ）, 2026 edition](https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-N03-2026.html), from Japan’s Ministry of Land, Infrastructure, Transport and Tourism, under CC BY 4.0.
