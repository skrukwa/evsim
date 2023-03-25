from classes import Car, ChargeStation, ChargeNetwork
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


def cluster_graph(charge_network: ChargeNetwork, approx_clusters: int) -> None:
    """Clusters the charge stations in charge_network using
    ...  # maybe gaussian ??
    and then replaces each cluster with a single charge station at the mean location.
    This is a mutating method.
    """
    ...


def find_edges_to_add(charge_network: ChargeNetwork) -> None:
    """
    use googlemaps
    """


def add_edges(a) -> ...:
    """
    tbd
    """


def googlemaps_something_matrix_requester(a) -> ...:
    """
    prefer routes, but may have to do directions matrix
    """


if __name__ == '__main__':
    from visuals import *
    # TEST
    m3 = Car('Apache Automotive',
             'EV Linear Charger',
             250,
             lambda start, end: (100 * end) ** 2 - (100 * start) ** 2)

    network = ChargeNetwork(4, m3)

    load_chargers_to_graph(network, 'cali_subset.csv')

    temp_basic_map(network)

    print(len(network._graph))
    import cluster
    tree = cluster.TreeCluster(1000, network.get_charge_stations())
    tree.create_subclusters()
    my_list = tree.get_list_of_clusters()

    temp_cluster_map(my_list)
    print(len(my_list))

