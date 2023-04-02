"""TODO


EXAMPLE CODE FOR LOADING A PICKLE
=================================

import pickle
with open('file.pickle', 'rb') as file:
    obj = pickle.load(file)

"""
import graph_initializer
import visuals
import cluster
import googlemaps
import maps_api
import pickle
from classes import ChargeNetwork

CAR_RANGE = 500             # TODO
MIN_CHARGERS = 4            # TODO
MIN_CLUSTER_DIAMETER = 65   # TODO
DATA_FILE = 'all_data.csv'  # TODO

# STEP 1. INITIALIZE GRAPH WITH DATA

network = ChargeNetwork(MIN_CHARGERS, CAR_RANGE)
graph_initializer.load_chargers_to_graph(network, DATA_FILE)

visuals.graph_network(network)
print(len(network.charge_stations()))

# STEP 2. MAKE A CLUSTER TREE BASED OF THE FIRST GRAPH

tree = cluster.ClusterTree(network.charge_stations(), MIN_CLUSTER_DIAMETER)
cluster_list = tree.get_list_of_clusters()

visuals.graph_clusters(cluster_list)
print(len(cluster_list))

# STEP 3. MAKE A NEW GRAPH WITH THE CLUSTERED DATA

centroids = tree.get_list_of_final_centroids()

simplified_network = ChargeNetwork(MIN_CHARGERS, CAR_RANGE)
for charger in centroids:
    simplified_network.add_charge_station(charger, set())
visuals.graph_network(simplified_network)

# STEP 4. ADD EDGES TO THE GRAPH

possible_edges = simplified_network.get_list_of_possible_edges()
gmaps = googlemaps.Client(key=input('what is your google maps api key'))
out_file = input('what should the name of the output file be (ex. out.pickle)')
finished_edges = maps_api.mutate_edges(possible_edges, gmaps)
simplified_network.load_edges(finished_edges)

with open(out_file, 'wb') as file:
    pickle.dump(simplified_network, file)

visuals.graph_network(simplified_network)
