"""
Define generalized calculation functions.
"""
import math
from typing import Callable, Any


def lowest_average_distance(points: set[Any],
                            distance_func: Callable = math.dist,
                            coords_key: Callable = lambda x: (x[0], x[1])) -> Any:
    """
    Returns a point such that the average distance between it and every other point is minimised.

    Takes an optional distance parameter that calculates the distance between two coordinates,
    which defaults to calculating euclidean distances.

    Takes an optional key parameter which must return an indexable coordinate
    containing a latitude, longitude pair. Otherwise, if the points being passed are already
    in that form (ex. tuple), key can be ignored.

    Preconditions:
        - len(points) >= 1
    """
    min_average_distance_so_far, point_so_far = float('inf'), None

    for i in points:
        i_coord = coords_key(i)
        sum_so_far = 0
        for j in points:
            j_coord = coords_key(j)
            sum_so_far += distance_func(i_coord, j_coord)

        average = sum_so_far / len(points)
        if average < min_average_distance_so_far:
            min_average_distance_so_far, point_so_far = average, i

    return point_so_far


def furthest_apart(points: set[Any],
                   distance_func: Callable = math.dist,
                   coords_key: Callable = lambda x: (x[0], x[1])) -> tuple:
    """
    Returns two points such that the distance between them is maximised.

    Takes an optional distance parameter that calculates the distance between two coordinates.
    If no such parameter is provided, euclidean distances are used.

    Takes an optional key parameter which must return an indexable coordinate
    containing a latitude, longitude pair. Otherwise, if the points being passed are already
    in that form (ex. tuple), key can be ignored.

    Preconditions:
        - len(points) >= 1
    """
    max_distance_so_far, points_so_far = 0, None

    for i in points:
        i_coord = coords_key(i)
        for j in points:
            j_coord = coords_key(j)
            distance = distance_func(i_coord, j_coord)

            if distance >= max_distance_so_far:
                max_distance_so_far, points_so_far = distance, (i, j)

    return points_so_far


def great_circle_distance(p1: tuple[float, float], p2: tuple[float, float]) -> float:
    """
    Returns the great circle distance in kilometers between the two given points using the equation below.

    https://en.wikipedia.org/wiki/Great-circle_distance

    Preconditions:
    - -90 <= p1[0] <= 90
    - -180 <= p1[1] <= 180
    - -90 <= p2[0] <= 90
    - -180 <= p2[1] <= 180

    >>> round(great_circle_distance((52.133174, -106.630807), (50.401793, 30.449782)))
    7920
    """
    lat1 = (math.pi / 180) * p1[0]
    lon1 = (math.pi / 180) * p1[1]
    lat2 = (math.pi / 180) * p2[0]
    lon2 = (math.pi / 180) * p2[1]

    lat_diff = abs(lat1 - lat2)
    lon_diff = abs(lon1 - lon2)

    central_angle = 2 * math.asin(
        math.sqrt(
            _hav(lat_diff) + (1 - _hav(lat_diff) - _hav(lat1 + lat2)) * _hav(lon_diff)
        )
    )
    return 6371 * central_angle


def _hav(num: float) -> float:
    """Returns the haversine of the number."""
    return math.sin(num / 2) ** 2
