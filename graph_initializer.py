"""The graph_initializer.py module of the ev-trip-sim project.
https://github.com/skrukwa/ev-trip-sim

Description
===========

This module is responsible for creating charge network graphs from csv dataset files.

Copyright and Usage Information
===============================

This file is distributed under the ev-trip-sim project which is
bounded by the terms of Apache License Version 2.0. For more
information, please follow the github link above.

This file is Copyright (c) Evan Skrukwa and Nadim Mottu.
"""
from classes import ChargeNetwork, ChargeStation
import csv
import datetime
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon


def load_chargers_to_graph(charge_network: ChargeNetwork, filepath: str) -> None:
    """Takes an empty ChargeNetwork object and adds each row of the csv
    at filepath as a charge station as long as it has a sum of at least
    charge_network.min_chargers_at_station type 2 and type DC chargers
    and is located in mainland North America.

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
            type_2_count = int(row[18]) if row[18] else 0
            type_dc_count = int(row[19]) if row[19] else 0

            lat = float(row[24])
            lon = float(row[25])
            name = row[1]
            addr = row[2]
            hours = row[12]

            if type_2_count + type_dc_count >= charge_network.min_chargers_at_station and _in_mainland(lat, lon):

                date = None
                try:
                    date = datetime.datetime.strptime(row[32], '%Y-%m-%d').date()
                except ValueError:
                    print('skipped this row due to a parsing error')  # strptime error

                if date:
                    new_charger = ChargeStation(
                        name=name,
                        address=addr,
                        hours=hours,
                        latitude=lat,
                        longitude=lon,
                        open_date=date)

                    charge_network.add_charge_station(new_charger, set())


def _in_mainland(lat: float, lon: float) -> bool:
    """Returns True if the given coordinate is in mainland North America.
    >>> _in_mainland(40.7128, -74.0060) # New York
    True
    >>> _in_mainland(49.2827, -123.1207) # Vancouver
    True
    >>> _in_mainland(51.5074, -0.1278) # London
    False
    """
    point = Point(lat, lon)
    north_america_polygon = Polygon([(52, -170), (71, -166), (46, -48), (24, -80), (24, -120)])
    return north_america_polygon.contains(point)
