"""
----------Objectives----------
Use created network to find path and output results.
"""
from typing import Optional, Callable

import googlemaps

import calcs
import creds
import polylines
import visuals
from classes import ChargeNetwork


def generic_charge_curve(charge: float):
    """
    Returns the time in seconds to charge from 0.00 to charge using to following model.

    https://www.desmos.com/calculator/fusfey6wwn

    Preconditions:
        - 0 <= charge <= 1
    """
    x = charge
    f = 3618.27
    g = -17215.3
    h = 55352.6
    i = -71588.6
    j = 33607.2
    return f * x ** 1 + g * x ** 2 + h * x ** 3 + i * x ** 4 + j * x ** 5


def find_path_and_get_json_ready(input_filepath: str,
                                 min_leg_length: float,
                                 ev_range: float,
                                 min_battery: float,
                                 max_battery: float,
                                 start_battery: float,
                                 charge_curve: Callable,
                                 coord1: Optional[tuple[float, float]],
                                 coord2: Optional[tuple[float, float]]) -> dict:
    """
    Finds the closest charge stations to coord1 and coord2 in the given network and
    then finds the shortest path, makes a Google Maps API call to find the polyline,
    simulates charging on that polyline, and returns a JSON ready dict summary.

    Raises PathNotFound or PathNotNeeded.

    Preconditions:
        - input_filepath leads to a JSON file exported from a previous ChargeNetwork object
        - 0 <= min_battery <= max_battery <= 1
        - min_leg_length <= (max_battery - min_battery) * ev_range <= _ev_range of the network at input_filepath
    """
    net = ChargeNetwork.from_json(input_filepath)

    set_of_chargers = net.charge_stations()
    list_of_chargers = list(set_of_chargers)
    c1 = min(list_of_chargers, key=lambda c: calcs.great_circle_distance(coord1, c.coord))
    c2 = min(list_of_chargers, key=lambda c: calcs.great_circle_distance(coord2, c.coord))

    path = net.get_shortest_path(c1, c2, min_leg_length, (max_battery - min_battery) * ev_range)
    # could raise PathNotFound or PathNotNeeded

    gmaps = googlemaps.Client(key=creds.get_key())
    polyline = polylines.get_polyline_legs(path, c1, gmaps)
    # could raise googlemaps.exceptions.ApiError

    polyline_with_charging = polylines.get_polyline_with_charging(
        polyline=polyline,
        ev_range=ev_range,
        min_battery=min_battery,
        start_battery=start_battery,
        charge_curve=charge_curve
    )

    return polylines.get_json_ready(path, c1, polyline_with_charging)


if __name__ == '__main__':
    # visualize network
    network = ChargeNetwork.from_json('created_network/network.json')
    visuals.graph_network(network, display_result=True)
