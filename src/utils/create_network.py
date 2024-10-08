"""
Create networks.

See also:
https://afdc.energy.gov/fuels/electricity_locations.html#/analyze?fuel=ELEC
"""
import csv
import datetime

import googlemaps
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon

from classes.charge_network import ChargeNetwork
from classes.charge_station import ChargeStation
from classes.leg import Leg
from cluster import ClusterTree
from visuals import graph_network, graph_clusters


def make_network(input_filepath: str,
                 min_chargers: int,
                 ev_range: int,
                 cluster_diameter: int,
                 output_filepath: str) -> None:
    """
    Creates a complete network from a data file of charge stations
    and visualizes the progress intermittently as outlined below.

    Outputs a JSON file of the final network for later use without having to remake the network.

    1. make a network using the data in the given data file and visualize it
    2. cluster that data and visualize it
    3. make a new graph of just the centroids of the clustered data and visualize it
    4. add all the legs to the new graph using googlemaps api and visualize it
    5. output the JSON file

    The attributes of this function are as follows.
        - input_filepath: the file path of the charge station dataset
        - min_chargers: the min number of DC fast chargers at each charge station when creating this network
        - ev_range: the max road distance in kilometers of each leg when creating this network
        - cluster_diameter: the max diameter in kilometers of cluster created when clustering this network
        - output_filepath: the file path the JSON file will be saved as (ending in .json)

    Preconditions:
        - input_filepath leads to a csv in the default format downloaded from
          https://afdc.energy.gov/fuels/electricity_locations.html#/analyze?fuel=ELEC
    """
    # STEP 1. INITIALIZE GRAPH WITH DATA

    full_network = ChargeNetwork(min_chargers, ev_range)
    load_charge_stations_from_csv(full_network, input_filepath)

    graph_network(full_network, display_result=True)
    print(f'number of charge stations in full network: {len(full_network.charge_stations())}')

    # STEP 2. MAKE A CLUSTER TREE BASED OF THE FIRST GRAPH

    cluster_tree = ClusterTree(full_network.charge_stations(), cluster_diameter)

    cluster_list = cluster_tree.get_list_of_clusters()
    graph_clusters(cluster_list, display_result=True)
    print(f'number of charge stations in clustered network: {len(cluster_list)}')

    # STEP 3. MAKE A NEW GRAPH WITH THE CLUSTERED DATA

    centroids = cluster_tree.get_list_of_final_centroids()
    simplified_network = ChargeNetwork(min_chargers, ev_range)
    for cs in centroids:
        simplified_network.add_charge_station(cs)

    graph_network(simplified_network, display_result=True)

    # STEP 4. ADD LEGS TO THE NEW GRAPH USING GOOGLEMAPS API

    legs = simplified_network.get_possible_legs()
    gmaps = googlemaps.Client(key=input('what is your google maps api key: '))
    mutate_legs(legs, gmaps)
    simplified_network.safe_load_legs(legs)

    graph_network(simplified_network, display_result=True)

    # STEP 5. OUTPUT THE JSON FILE

    simplified_network.export_to_json(output_filepath)


def load_charge_stations_from_csv(charge_network: ChargeNetwork, filepath: str) -> None:
    """
    Takes an empty ChargeNetwork object and adds each row of the csv at filepath as a charge station as long as
        - it has at least charge_network.min_chargers_at_station DC fast chargers and
        - it is located in mainland North America.

    This is a mutating method.

    Preconditions:
        - charge_network is empty
        - filepath leads to a csv in the default format downloaded from the
          energy.gov Alternative Fuels Data Center
    """
    with open(filepath) as f:
        reader = csv.reader(f)
        next(reader)  # skip the header

        for row in reader:
            dc_fast_count = int(row[19]) if row[19] else 0

            lat = float(row[24])
            lng = float(row[25])
            name = row[1] if row[1] else None
            addr = row[2] if row[2] else None
            phone = row[8] if row[8] else None
            hours = row[12] if row[12] else None
            date = datetime.datetime.strptime(row[32], '%Y-%m-%d').date() if row[32] else None

            if dc_fast_count >= charge_network.min_chargers_at_station and _in_mainland(lat, lng):
                new_cs = ChargeStation(name, addr, hours, phone, lat, lng, date)
                charge_network.add_charge_station(new_cs)


def _in_mainland(lat: float, lng: float) -> bool:
    """Returns if the given coordinate is in mainland North America.
    >>> _in_mainland(40.7128,-74.0060)  # new york
    True
    >>> _in_mainland(49.2827,-123.1207)  # vancouver
    True
    >>> _in_mainland(51.5074,-0.1278)  # london
    False
    """
    point = Point(lat, lng)
    north_america_polygon = Polygon([(52, -170), (71, -166), (46, -48), (24, -80), (24, -120)])
    return north_america_polygon.contains(point)


def mutate_legs(legs: set[Leg], gmaps: googlemaps.client.Client) -> None:
    """
    Takes a set of incomplete legs and mutates their driving_distance and driving_time by making calls
    to the given googlemaps client. Any failed calls will result in the leg being discarded.

    Note that normally, there are no failed calls.

    Prints a verbose summary.

    This is a mutating method.

    Preconditions:
        - all(leg.driving_distance is None for leg in legs)
        - all(leg.driving_time is None for leg in legs)
    """
    init_leg_count = len(legs)
    failed_legs = set()
    if input(f'you are about to make {len(legs)} calls to the provided client (Y/N): ') == 'Y':
        for leg in legs:
            if not _mutate_leg(leg, gmaps):
                failed_legs.add(leg)

        for leg in failed_legs:
            legs.remove(leg)

        print(f'successfully completed {len(legs)}/{init_leg_count} legs')
    else:
        raise KeyboardInterrupt


def _mutate_leg(leg: Leg, gmaps: googlemaps.client.Client) -> bool:
    """
    Takes an incomplete leg and completes it by making a call to the given googlemaps client.

    Returns True if successful and mutated, or False if unsuccessful and no mutations made.

    This is a mutating method.

    Preconditions:
        - leg.driving_distance is None
        - leg.driving_time is None
    """
    endpoints_iter = iter(leg.endpoints)
    cs1 = next(endpoints_iter).coord
    cs2 = next(endpoints_iter).coord

    try:
        response = gmaps.directions(cs1, cs2)
        driving_distance = response[0]['legs'][0]['distance']['value']
        driving_time = response[0]['legs'][0]['duration']['value']

    except Exception:  # todo implement better error handling
        return False

    leg.driving_distance = driving_distance
    leg.driving_time = driving_time

    return True


if __name__ == '__main__':
    make_network(input_filepath='created_network/dataset.csv',
                 min_chargers=4,
                 ev_range=700,
                 cluster_diameter=60,
                 output_filepath='../created_network/network.json')
