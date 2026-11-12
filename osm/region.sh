case "${REGION:-}" in
    japan) extract=asia/japan ;;
    chubu|chugoku|hokkaido|kansai|kanto|kyushu|shikoku|tohoku) extract=asia/japan/$REGION ;;
    *)
        printf '%s\n' 'Set REGION to one of: japan chubu chugoku hokkaido kansai kanto kyushu shikoku tohoku' >&2
        exit 1
        ;;
esac

pbf="/downloads/$REGION.osm.pbf"
