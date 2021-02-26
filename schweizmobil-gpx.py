#! /usr/bin/env nix-shell
#! nix-shell -i python3 -p python3 python3Packages.gpxpy python3Packages.requests
import gpxpy.gpx
import requests
import sys

ROUTE_TYPES = {
    "national": "WanderlandRoutenNational",
    "regional": "WanderlandRoutenRegional",
    "local": "WanderlandRoutenLokal",
    "snowshoe-local": "SnowshoeRoutenLokal",
}


def lv03_to_wgs84(y, x):
    y_aux = (y - 600000) / 1000000
    x_aux = (x - 200000) / 1000000
    lng = (
        (
            2.6779094
            + 4.728982 * y_aux
            + 0.791484 * y_aux * x_aux
            + 0.1306 * y_aux * x_aux ** 2
            - 0.0436 * y_aux ** 3
        )
        * 100
        / 36
    )
    lat = (
        (
            16.9023892
            + 3.238272 * x_aux
            - 0.270978 * y_aux ** 2
            - 0.002528 * x_aux ** 2
            - 0.0447 * y_aux ** 2 * x_aux
            - 0.0140 * x_aux ** 3
        )
        * 100
        / 36
    )
    return lat, lng


def schweizmobil_url(route_type, route_nr):
    qs = f"{ROUTE_TYPES[route_type]}={route_nr}"
    return f"https://map.schweizmobil.ch/api/4/query/featuresmultilayers?{qs}"


def fetch_schweizmobil_points(route_type, route_nr):
    feature = requests.get(schweizmobil_url(route_type, route_nr)).json()
    return feature["features"][0]["geometry"]["coordinates"][0]


def gpx_from_points(wgs84_points):
    segment = gpxpy.gpx.GPXTrackSegment()
    for (lat, lon) in wgs84_points:
        segment.points.append(gpxpy.gpx.GPXTrackPoint(lat, lon))

    track = gpxpy.gpx.GPXTrack()
    track.segments.append(segment)
    gpx = gpxpy.gpx.GPX()
    gpx.tracks.append(track)
    return gpx


if __name__ == "__main__":
    types = "|".join(ROUTE_TYPES)
    if len(sys.argv) not in (3, 4):
        print(f"usage: {sys.argv[0]} <{types}> <route_nr> [out.gpx]", file=sys.stderr)
        sys.exit(1)

    route_type = sys.argv[1]
    if route_type not in ROUTE_TYPES:
        print(f"error: {route_type} is not {types}", file=sys.stderr)
        sys.exit(1)

    try:
        route_nr = sys.argv[2]
    except ValueError:
        print(f"error: invalid route number {route_nr}", file=sys.stderr)
        sys.exit(1)

    lv03_points = fetch_schweizmobil_points(route_type, route_nr)
    wgs84_points = [lv03_to_wgs84(y, x) for (y, x) in lv03_points]
    gpx = gpx_from_points(wgs84_points)

    filename = sys.argv[3] if len(sys.argv) == 4 else "out.gpx"
    open(filename, "wb").write(gpx.to_xml().encode("utf-8"))
