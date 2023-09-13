"""
----------Objectives----------
Use Google Maps Distance API via googlemaps library in order to mutate edges.

----------Resources used----------
https://github.com/googlemaps/google-maps-services-python
"""
import googlemaps

from classes import _Edge


def mutate_edges(edges: set[_Edge], gmaps: googlemaps.client.Client) -> None:
    """
    Takes a set of incomplete edges and returns a new set of edges completed by making calls
    to the given googlemaps client. Any failed calls will result in the edge being discarded.

    Note that normally, there are no failed calls.

    Prints a verbose summary.

    This is a mutating method.

    Preconditions:
        - all(edge.road_distance is None for edge in edges)
        - all(edge.time is None for edge in edges)
    """
    org_len_edges = len(edges)
    failed_edges = set()
    if input(f'you are about to make {len(edges)} calls to the provided client (Y/N): ') == 'Y':
        for edge in edges:
            if not _mutate_edge(edge, gmaps):
                failed_edges.add(edge)

        for edge in failed_edges:
            edges.remove(edge)

        print(f'successfully completed {len(edges)}/{org_len_edges} edges')
    else:
        raise KeyboardInterrupt


def _mutate_edge(edge: _Edge, gmaps: googlemaps.client.Client) -> bool:
    """
    Takes an incomplete edge and completes it by making a call to the given googlemaps client.

    Returns True if successful and mutated, or False if unsuccessful and no mutations made.

    This is a mutating method.

    Preconditions:
        - edge.road_distance is None
        - edge.time is None
    """
    endpoints_iter = iter(edge.endpoints)
    p1 = next(endpoints_iter).coord
    p2 = next(endpoints_iter).coord

    try:
        response = gmaps.directions(p1, p2)
        road_distance = response[0]['legs'][0]['distance']['value'] / 1000
        time = response[0]['legs'][0]['duration']['value']

        assert isinstance(road_distance, float)
        assert isinstance(time, int)

    except Exception:  # TODO: implement better error handling
        return False

    edge.road_distance = road_distance
    edge.time = time

    return True
