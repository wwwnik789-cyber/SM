#!/usr/bin/env python3
"""Extract Russia as GeoJSON from world-atlas countries-50m TopoJSON.

Source dataset: Natural Earth via world-atlas (https://github.com/topojson/world-atlas).
Natural Earth map data is in the public domain.
"""

import json
import sys
from pathlib import Path


def decode_topology(topology, country_id="643"):
    scale = topology["transform"]["scale"]
    translate = topology["transform"]["translate"]
    decoded = []
    for arc in topology["arcs"]:
        x = y = 0
        points = []
        for dx, dy in arc:
            x += dx
            y += dy
            points.append([
                x * scale[0] + translate[0],
                y * scale[1] + translate[1],
            ])
        decoded.append(points)

    def get_arc(index):
        if index >= 0:
            return decoded[index]
        return list(reversed(decoded[~index]))

    def stitch(indices):
        ring = []
        for index in indices:
            arc = get_arc(index)
            ring.extend(arc if not ring else arc[1:])
        return ring

    countries = topology["objects"]["countries"]["geometries"]
    geometry = next(g for g in countries if str(g.get("id")) == country_id)
    if geometry["type"] == "Polygon":
        coordinates = [[stitch(ring) for ring in geometry["arcs"]]]
    else:
        coordinates = [
            [stitch(ring) for ring in polygon]
            for polygon in geometry["arcs"]
        ]
    return {
        "type": "Feature",
        "properties": {
            "name": "Russia",
            "source": "Natural Earth / world-atlas countries-50m",
        },
        "geometry": {"type": "MultiPolygon", "coordinates": coordinates},
    }


def main():
    if len(sys.argv) != 3:
        raise SystemExit("Usage: extract_russia_geojson.py countries-50m.json output.geojson")
    source, output = map(Path, sys.argv[1:])
    feature = decode_topology(json.loads(source.read_text()))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(feature, ensure_ascii=False, separators=(",", ":")))
    print(output)


if __name__ == "__main__":
    main()
