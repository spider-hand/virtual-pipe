set -eu

. ./region.sh

temporary=$(mktemp "${pbf}.XXXXXX")
trap 'rm -f "$temporary"' EXIT
trap 'exit 1' HUP INT TERM

printf 'Downloading the Geofabrik extract for %s.\n' "$REGION"
url=$(curl --fail --silent --show-error --location --output "$temporary" \
    --write-out '%{url_effective}' "https://download.geofabrik.de/$extract-latest.osm.pbf")
checksum=$(curl --fail --silent --show-error --location "$url.md5")
printf '%s  %s\n' "${checksum%% *}" "$temporary" | md5sum --check

mv -f "$temporary" "$pbf"
printf 'Downloaded %s to the OSM cache.\n' "$REGION"
