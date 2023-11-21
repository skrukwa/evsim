"""
----------Objectives----------
Create networks.
"""
import googlemaps

import cluster
import complete_edges
import graph_initializer
import visuals
from classes import ChargeNetwork


def make_network(input_filepath: str,
                 min_chargers: int,
                 ev_range: int,
                 cluster_diameter: int,
                 output_filepath: str) -> None:
    """
    Goes through the process of making a complete network from a data file of
    charge stations and visualizes the progress intermittently as outlined below.

    Outputs a JSON file of the final network for later use without having to
    remake the network.

    1. make a network using all the data in the given data file and visualize it
    2. cluster that data and visualize it
    3. make a new graph of just the centroids of the clustered data and visualize it
    4. add all the edges to the new graph using googlemaps api and visualize it
    5. output the JSON file

    The attributes of this function are as follows.
        - input_filepath: the file path of the charge station dataset
        - min_chargers: the minimum number of DC fast chargers at each charge station when creating this network
        - ev_range: the maximum road distance in kilometers of edges when creating this network
        - cluster_diameter: the maximum diameter in kilometers of cluster created when clustering this network
        - output_filepath: the file path the JSON file will be saved as

    Preconditions:
        - input_filepath leads to a csv in the default format downloaded from
          https://afdc.energy.gov/fuels/electricity_locations.html#/analyze?fuel=ELEC
    """
    # STEP 1. INITIALIZE GRAPH WITH DATA

    full_network = ChargeNetwork(min_chargers, ev_range)
    graph_initializer.load_chargers_to_graph(full_network, input_filepath)

    visuals.graph_network(full_network, display_result=True)
    print(f'number of charge stations in full network: {len(full_network.charge_stations())}')

    # STEP 2. MAKE A CLUSTER TREE BASED OF THE FIRST GRAPH

    cluster_tree = cluster.ClusterTree(full_network.charge_stations(), cluster_diameter)

    cluster_list = cluster_tree.get_list_of_clusters()
    visuals.graph_clusters(cluster_list, display_result=True)
    print(f'number of charge stations in clustered network: {len(cluster_list)}')

    # STEP 3. MAKE A NEW GRAPH WITH THE CLUSTERED DATA

    centroids = cluster_tree.get_list_of_final_centroids()
    simplified_network = ChargeNetwork(min_chargers, ev_range)
    for charger in centroids:
        simplified_network.add_charge_station(charger, set())

    visuals.graph_network(simplified_network, display_result=True)

    # STEP 4. ADD EDGES TO THE NEW GRAPH USING GOOGLEMAPS API

    edges = simplified_network.get_possible_edges()
    gmaps = googlemaps.Client(key=input('what is your google maps api key: '))
    complete_edges.mutate_edges(edges, gmaps)
    simplified_network.load_edges(edges)

    visuals.graph_network(simplified_network, display_result=True)

    # STEP 5. OUTPUT THE JSON FILE

    simplified_network.export_to_json(output_filepath)


if __name__ == '__main__':
    make_network(input_filepath='created_network/dataset.csv',
                 min_chargers=4,
                 ev_range=700,
                 cluster_diameter=60,
                 output_filepath='network.json')
