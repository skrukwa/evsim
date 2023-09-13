"""
----------Objectives----------
Use created networks.
"""
import datetime
import random
from typing import Optional

import calcs
import visuals
from classes import ChargeNetwork, ChargeStation


def get_path(input_filepath: str,
             min_leg_length: float,
             max_leg_length: float,
             coord1: Optional[tuple[float, float]] = None,
             coord2: Optional[tuple[float, float]] = None) -> None:
    """
    Finds the closest charge stations to coord1 and coord2 in the given network and
    then calculates and visualizes the shortest path.

    If the coord arguments are not provided, calculates and visualizes the shortest path
    between two random charge stations.

    Preconditions:
        - input_filepath leads to a JSON file exported from a previous ChargeNetwork object
        - (coord1 is None and coord2 is None) or (coord1 is not None and coord2 is not None)
    """
    net = ChargeNetwork.from_json(input_filepath)
    set_of_chargers = net.charge_stations()
    list_of_chargers = list(set_of_chargers)

    if coord1 is None and coord2 is None:
        # RANDOMLY PICK 2 CHARGE POINTS
        c1, c2 = random.sample(list_of_chargers, 2)

    elif coord1 is not None and coord2 is not None:
        # FIND CHARGE STATIONS CLOSEST TO GIVEN COORDS
        c1 = min(list_of_chargers, key=lambda c: calcs.great_circle_distance(coord1, c.coord))
        c2 = min(list_of_chargers, key=lambda c: calcs.great_circle_distance(coord2, c.coord))

    else:
        raise TypeError

    # FIND SHORTEST PATH

    result = net.get_shortest_path(c1, c2, min_leg_length, max_leg_length)
    print()
    print(f'start coord: {c1.coord}')
    print(f'start name: {c1.name}')
    print(f'start address: {c1.address}')
    print(f'start hours: {c1.hours}')
    print(f'start phone: {c1.phone}')
    print(f'start open date: {c1.open_date}')
    print()
    print(f'end coord: {c2.coord}')
    print(f'end name: {c2.name}')
    print(f'end address: {c2.address}')
    print(f'end hours: {c2.hours}')
    print(f'end phone: {c2.phone}')
    print(f'end open date: {c2.open_date}')
    print()
    if not result:
        if isinstance(result, list):
            print('no path needed')
        else:  # isinstance(result, NoneType)
            print('no path found')
        return

    print(f'total path length: {sum(e.road_distance for e in result)} km')
    print(f'total path duration: {datetime.timedelta(seconds=sum(e.time for e in result))}')

    # VISUALIZE THE PATH

    temp_graph = ChargeNetwork(-1, -1)
    temp_graph.add_charge_station(ChargeStation('', '', '', '', 0, 0, datetime.date(2000, 1, 1)), set(result))

    all_chargers = set.union(*(edge.endpoints for edge in result))
    for charger in all_chargers:
        temp_graph.add_charge_station(charger, set())

    visuals.graph_network(temp_graph)


if __name__ == '__main__':
    print('1. visualize the network')
    print('2. use the full network to get a random path')
    print('3. use the full network to get a specified path by snapping given coords to charge stations')
    choice = input('please input your choice (1/2/3): ')

    if choice == '1':
        # visualize network
        network = ChargeNetwork.from_json('created_network/network.json')
        visuals.graph_network(network)

    elif choice == '2':
        # use network to get a random path
        for _ in range(5):
            get_path('created_network/network.json', 250, 450)

    elif choice == '3':
        # use network to get a specified path by
        # snapping the given coordinates to the closest charge stations in the network
        input_c1 = (float(input('coord 1 lat: ')), float(input('coord 1 lon: ')))
        input_c2 = (float(input('coord 2 lat: ')), float(input('coord 2 lon: ')))
        get_path('created_network/network.json',
                 250,
                 450,
                 input_c1,
                 input_c2)

    else:
        raise TypeError
