from classes import Car, ChargeStation, ChargeNetwork
import csv
import datetime


def load_chargers_to_graph(charge_network: ChargeNetwork, filepath: str) -> None:
    """Takes an empty ChargeNetwork object and adds each row of the csv
    at filepath as a charge station. This is a mutating method.

    Preconditions:
        - graph.is_empty()
        - filepath leads to a csv in the default format downloaded from the
          energy.gov Alternative Fuels Data Center
    """
    with open(filepath) as f:
        reader = csv.reader(f)
        next(reader)  # skip the header
        for row in reader:

            new_charger = ChargeStation(
                name=str(row[1]),
                address=str(row[2]),
                hours=str(row[12]),
                latitude=float(row[24]),
                longitude=float(row[25]),
                open_date=datetime.datetime.strptime(row[32], '%Y-%m-%d').date())

            charge_network.add_charge_station(new_charger, None)


if __name__ == '__main__':
    from visuals import temp_basic_map
    # TEST
    m3 = Car('Apache Automotive',
             'EV Linear Charger',
             250,
             lambda start, end: (100 * end) ** 2 - (100 * start) ** 2)

    network = ChargeNetwork(m3)

    load_chargers_to_graph(network, 'alberta_sample_subset.csv')

    temp_basic_map(network)