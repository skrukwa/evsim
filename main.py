"""
----------Objectives----------
Use created network to find path and output results.
"""
from typing import Optional, Callable

import googlemaps

import calcs
import creds
import path_sim
import visuals
from classes import ChargeNetwork


def generic_charge_curve(charge: float):
    """
    Returns the driving time in seconds to charge from 0.00 to charge using to following model.

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


def do_request(input_filepath: str,
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
    then finds the shortest path. Makes a call to the given googlemaps client to find the
    polyline, bounds, and up-to-date driving_distance and driving_time.
    Returns a JSON compatible dict summary.

    Raises PathNotFound or PathNotNeeded.

    Preconditions:
        - input_filepath leads to a JSON file exported from a previous ChargeNetwork object
        - 0 <= min_battery <= max_battery <= 1
        - min_leg_length <= (max_battery - min_battery) * ev_range <= _ev_range of the network at input_filepath
    """
    request_data = {
        'start_coord': coord1,
        'end_coord': coord2,
        'min_leg_length': min_leg_length,
        'ev_range': ev_range,
        'min_battery': min_battery,
        'max_battery': max_battery,
        'start_battery': start_battery
    }

    net = ChargeNetwork.from_json(input_filepath)

    all_charge_stations = list(net.charge_stations())
    cs1 = min(all_charge_stations, key=lambda c: calcs.great_circle_distance(coord1, c.coord))
    cs2 = min(all_charge_stations, key=lambda c: calcs.great_circle_distance(coord2, c.coord))

    path = net.get_shortest_path(cs1, cs2, min_leg_length, (max_battery - min_battery) * ev_range)
    # could raise PathNotFound or PathNotNeeded

    gmaps = googlemaps.Client(key=creds.get_key())

    info, polyline, bounds = path_sim.get_path_info(path, cs1, gmaps)
    dest_start_battery = path_sim.simulate_path_charging(ev_range, min_battery, start_battery, charge_curve, info)
    json_dict = path_sim.prepare_json_dict(path, cs1, info, polyline, bounds, dest_start_battery, request_data)
    return json_dict


if __name__ == '__main__':
    # visualize network
    network = ChargeNetwork.from_json('created_network/network.json')
    visuals.graph_network(network, display_result=True)
