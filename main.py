"""The main.py module of the ev-trip-sim project.
https://github.com/skrukwa/ev-trip-sim

Description
===========

This module can be used to interact and test the other modules of this project.
Notable, this file can be used make a new network, and get shortest paths from a preexisting network.

Copyright and Usage Information
===============================

This file is distributed under the ev-trip-sim project which is
bounded by the terms of Apache License Version 2.0. For more
information, please follow the github link above.

This file is Copyright (c) Evan Skrukwa and Nadim Mottu.
"""
import datetime
import pickle
import random
from typing import Optional

import googlemaps

import calcs
import cluster
import graph_initializer
import maps_api
import visuals
from classes import ChargeNetwork, ChargeStation


def make_network(data_file: str, min_chargers: int, cluster_diameter: int, car_range: int) -> None:
    """Goes through the process of making a complete network from a data file of
    charge stations and visualizes the progress intermittently as outlined below.

    Outputs a pickle file of the final network for later use without having to
    remake the network.

    1. make a network using all the data in the given data file and visualize it
    2. cluster that data and visualize it
    3. make a new graph of just the centroids of the clustered data and visualize it
    4. add all the edges to the new graph using googlemaps api and visualize it

    The attributes of this function are as follows.
        - data_file: the file path the charge station dataset
        - min_chargers: the minimum number of chargers at each charge station when creating a graph
        - cluster_diameter: the maximum diameter in kilometers of cluster created when clustering the graph
        - car_range: the maximum road distance in kilometers of edges when creating a graph

    Preconditions:
        - data_file leads to a csv in the default format downloaded from the
          energy.gov Alternative Fuels Data Center
    """
    # STEP 1. INITIALIZE GRAPH WITH DATA

    full_network = ChargeNetwork(min_chargers, car_range)
    graph_initializer.load_chargers_to_graph(full_network, data_file)

    visuals.graph_network(full_network)
    print(f'number of charge stations in full network: {len(full_network.charge_stations())}')

    # STEP 2. MAKE A CLUSTER TREE BASED OF THE FIRST GRAPH

    cluster_tree = cluster.ClusterTree(full_network.charge_stations(), cluster_diameter)

    cluster_list = cluster_tree.get_list_of_clusters()
    visuals.graph_clusters(cluster_list)
    print(f'number of charge stations in clustered network: {len(cluster_list)}')

    # STEP 3. MAKE A NEW GRAPH WITH THE CLUSTERED DATA

    centroids = cluster_tree.get_list_of_final_centroids()
    simplified_network = ChargeNetwork(min_chargers, car_range)
    for charger in centroids:
        simplified_network.add_charge_station(charger, set())

    visuals.graph_network(simplified_network)

    # STEP 4. ADD EDGES TO THE NEW GRAPH USING GOOGLEMAPS API

    possible_edges = simplified_network.get_list_of_possible_edges()
    gmaps = googlemaps.Client(key=input('what is your google maps api key: '))
    out_file = input('what should the name of the output file be (for example: output.pickle): ')
    finished_edges = maps_api.mutate_edges(possible_edges, gmaps)
    simplified_network.load_edges(finished_edges)

    with open(out_file, 'wb') as file:
        pickle.dump(simplified_network, file)

    visuals.graph_network(simplified_network)


def get_path(network_pickle_file: str,
             coord1: Optional[tuple[float, float]] = None,
             coord2: Optional[tuple[float, float]] = None) -> None:
    """Finds the closest charge stations to coord1 and coord2 in the given network and
    then calculates and visualizes the shortest path.

    If the coord arguments are not provided, calculates and visualizes the shortest path
    between two random charge stations.

    Preconditions:
        - network_file leads to a pickle file containing a completed ChargeNetwork object
        - (coord1 is None and coord2 is None) or (coord1 is not None and coord2 is not None)
    """
    with open(network_pickle_file, 'rb') as file:
        net = pickle.load(file)
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

    result = net.get_shortest_path(c1, c2)
    print(' ')
    print(f'start coord: {c1.coord}')
    print(f'start name: {c1.name}')
    print(f'start address: {c1.address}')
    print(f'start hours: {c1.hours}')
    print(f'start open date: {c1.open_date}')
    print(' ')
    print(f'end coord: {c2.coord}')
    print(f'end name: {c2.name}')
    print(f'end address: {c2.address}')
    print(f'end hours: {c2.hours}')
    print(f'end open date: {c2.open_date}')
    print(' ')
    print(f'total path length: {sum(e.road_distance for e in result)} km')
    print(f'total path duration: {datetime.timedelta(seconds=sum(e.time for e in result))}')

    # VISUALIZE THE PATH

    temp_graph = ChargeNetwork(-1, -1)
    temp_graph.add_charge_station(ChargeStation('', '', '', 0, 0, datetime.date(2000, 1, 1)), set(result))

    all_chargers = set()
    for edge in result:
        endpoints_iter = iter(edge.endpoints)
        p1 = next(endpoints_iter)
        if p1 not in all_chargers:
            all_chargers.add(p1)
        p2 = next(endpoints_iter)
        if p2 not in all_chargers:
            all_chargers.add(p2)

    for charger in all_chargers:
        temp_graph.add_charge_station(charger, set())

    visuals.graph_network(temp_graph)


if __name__ == '__main__':
    # import doctest
    # doctest.testmod()
    #
    # import python_ta
    # python_ta.check_all(config={
    #     'max-line-length': 120,
    #     'disable': ['forbidden-import', 'forbidden-IO-function', 'possibly-undefined', 'too-many-locals']
    # })

    print('options:')
    print('1. make your own smaller network')
    print('2. visualize the full network we made')
    print('3. use the full network to get a path from florida to bc')
    print('4. use the full network to get a random path')
    print('5. use the full network to get a specified path by snapping given coords to charge stations')
    choice = input('please input your choice (1/2/3/4/5): ')

    if choice == '1':
        # make your own smaller network
        make_network(data_file='illinois_subset.csv',
                     min_chargers=4,
                     cluster_diameter=65,
                     car_range=500)

    elif choice == '2':
        # visualize the full network we made
        with open('full_network.pickle', 'rb') as pickle_file:
            network = pickle.load(pickle_file)
        visuals.graph_network(network)

    elif choice == '3':
        # use the full network to get a path from florida to bc
        get_path('full_network.pickle',
                 (24.553241, -81.754997),
                 (54.858385, -126.860451))

    elif choice == '4':
        # use the full network to get a random path
        get_path('full_network.pickle')

    elif choice == '5':
        # use the full network to get a specified path
        # snap the given coordinates to the closest charge stations in the network
        input_c1 = (float(input('coord 1 lat: ')), float(input('coord 1 lon: ')))
        input_c2 = (float(input('coord 2 lat: ')), float(input('coord 2 lon: ')))
        get_path('full_network.pickle', input_c1, input_c2)

    else:
        raise TypeError
