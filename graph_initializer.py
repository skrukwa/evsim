"""TODO"""
from classes import Car, ChargeNetwork
import csv
import datetime


def load_chargers_to_graph(charge_network: ChargeNetwork, filepath: str) -> None:
    """Takes an empty ChargeNetwork object and adds each row of the csv
    at filepath as a charge station as long as it has a sum of at least
    charge_network.min_chargers_at_station type 2 and type DC chargers.

    This is a mutating method.

    Preconditions:
        - graph.is_empty()
        - filepath leads to a csv in the default format downloaded from the
          energy.gov Alternative Fuels Data Center
    """
    with open(filepath) as f:
        reader = csv.reader(f)
        next(reader)  # skip the header
        for row in reader:

            try:
                type_2_count = int(row[18]) if row[18] else 0
                type_dc_count = int(row[19]) if row[19] else 0

                if type_2_count + type_dc_count >= charge_network.min_chargers_at_station:
                    new_charger = ChargeStation(
                        name=str(row[1]),
                        address=str(row[2]),
                        hours=str(row[12]),
                        latitude=float(row[24]),
                        longitude=float(row[25]),
                        open_date=datetime.datetime.strptime(row[32], '%Y-%m-%d').date())

                    charge_network.add_charge_station(new_charger, None)
            except Exception:
                print('skipped this row due to a parsing error')







if __name__ == '__main__':
    from visuals import *
    import cluster

    m3 = Car('Apache Automotive',
             'EV Linear Charger',
             250,
             lambda start, end: (100 * end) ** 2 - (100 * start) ** 2)

    network = ChargeNetwork(4, m3)
    load_chargers_to_graph(network, 'cali_subset.csv')

    graph_network(network)
    print(len(network.charge_stations()))

    tree = cluster.ClusterTree(network.charge_stations(), 20)

    cluster_list = tree.get_list_of_clusters()

    graph_clusters(cluster_list)
    print(len(cluster_list))

    centroids = tree.get_list_of_final_centroids()
    simple_network = ChargeNetwork(4, m3)
    for charger in centroids:
        simple_network.add_charge_station(charger, None)

    graph_network(simple_network)
