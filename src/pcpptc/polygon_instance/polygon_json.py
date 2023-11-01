import json
import typing

from shapely.geometry import Polygon


def polygon_to_json(
    polygon: Polygon, as_string: bool = True
) -> typing.Union[str, dict]:
    """
    Converts a polygon to a json string
    """
    data = {
        "exterior": [(p[0], p[1]) for p in polygon.exterior.coords],
        "interiors": [
            [(p[0], p[1]) for p in hole.coords] for hole in polygon.interiors
        ],
    }
    if as_string:
        return json.dumps(data)
    else:
        return data


def polygon_from_json(
    data_string: typing.Optional[str] = None, data: typing.Optional[dict] = None
) -> Polygon:
    """
    Reads a polygon from a json. Either from a json string or a already parsed data
    object. The numbers should not be strings.
    """
    if data_string:
        data = json.loads(data_string)
    if not data:
        msg = "No data to read."
        raise ValueError(msg)

    def to_points(l: list) -> typing.List[tuple]:
        return [(p[0], p[1]) for p in l]

    exterior = to_points(data["exterior"])
    holes = [to_points(h) for h in data["interiors"]]
    if not holes:
        return Polygon(exterior)
    return Polygon(exterior, holes=holes)
