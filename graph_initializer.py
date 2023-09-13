"""
----------Objectives----------
Create ChargeNetwork objects from csv dataset files.

----------Resources used----------
https://afdc.energy.gov/fuels/electricity_locations.html#/analyze?fuel=ELEC
"""
import csv
import datetime

from shapely.geometry import Point
from shapely.geometry.polygon import Polygon

from classes import ChargeNetwork, ChargeStation


def load_chargers_to_graph(charge_network: ChargeNetwork, filepath: str) -> None:
    """
    Takes an empty ChargeNetwork object and adds each row of the csv
    at filepath as a charge station as long as
        - it has at least charge_network.min_chargers_at_station DC fast chargers and
        - it is located in mainland North America.

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
            dc_fast_count = int(row[19]) if row[19] else 0

            lat = float(row[24])
            lon = float(row[25])
            name = row[1] if row[1] else None
            addr = row[2] if row[2] else None
            phone = row[8] if row[8] else None
            hours = row[12] if row[12] else None
            date = datetime.datetime.strptime(row[32], '%Y-%m-%d').date() if row[32] else None

            if dc_fast_count >= charge_network.min_chargers_at_station and _in_mainland(lat, lon):
                new_charger = ChargeStation(
                    latitude=lat,
                    longitude=lon,
                    name=name,
                    phone=phone,
                    address=addr,
                    hours=hours,
                    open_date=date
                )

                charge_network.add_charge_station(new_charger, set())


def _in_mainland(lat: float, lon: float) -> bool:
    """Returns True if the given coordinate is in mainland North America.
    >>> _in_mainland(40.7128, -74.0060)  # new york
    True
    >>> _in_mainland(49.2827, -123.1207)  # vancouver
    True
    >>> _in_mainland(51.5074, -0.1278)  # london
    False
    """
    point = Point(lat, lon)
    north_america_polygon = Polygon([(52, -170), (71, -166), (46, -48), (24, -80), (24, -120)])
    return north_america_polygon.contains(point)
