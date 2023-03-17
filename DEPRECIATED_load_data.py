"""
This module contains the basic methods and classes required for loading the data into a list of chargers
"""
from __future__ import annotations

import datetime
import math


def load_chargers_and_remove_clusters(data: str, distance_sen: float, quantity_sen: int)-> set[Charger]:
    """
    Create a graph from the csv file with all the charge stations while removing charge stations that are in clutters
    :param data: The location of the csv file
    :param distance_sen: How close to another charge station it must be to be considered a cluster in km
    :param quantity_sen: How many stations must be in a cluster before the cluster is consolidated
    :return: a list of charges excluding chargers that are close together

    Preconditions:
    - data is a path to a valid csv file with 68 columns
    - quantity_sen > 0

    NOTE: Currently the way to decide if two charge points form a cluster is to simply check if they are some distance
    from one another. In this implementation, if 2 points are not within distance_sen they can still be in a cluster
    together if there is a charge station between them. This is something we should think about changing.
    """

    # todo replace with correct index:
    long_index = 0
    lat_index = 1
    date_index = 2
    chargers = set()
    clusters = set()
    with open(data) as f:
        for line in f:
            new_charger = Charger(latitude=float(line[lat_index]),
                                  longitude=float(line[long_index]),
                                  open_date=string_from_data_to_date(line[date_index]))




            for charger in chargers:
                if chargers_to_km(charger, new_charger) >= distance_sen:
                    if new_charger.cluster is None and charger.cluster is None:
                        new_cluster = [charger, new_charger]
                        new_charger.cluster = new_cluster
                        charger.cluster = new_cluster
                    elif new_charger.cluster is None and charger.cluster is not None:
                        new_charger.cluster = charger.cluster
                    elif new_charger.cluster is not None and charger.cluster is None:
                        charger.cluster = new_charger.cluster
                    else:
                        # assert new_charger.cluster is not None and charger.cluster is not None
                        cluster_mutated_charger = min({charger, new_charger}, key=lambda char: len(char.cluster))
                        replacement_cluster = max({charger, new_charger}, key=lambda char: len(char.cluster))
                        for clustered_chargers in cluster_mutated_charger.cluster:
                            clustered_chargers.cluster = replacement_cluster.cluster
            chargers.add(new_charger)
            if new_charger.cluster is not None:
                clusters.add(new_charger.cluster)
        for c in clusters:
            if len(c) >= quantity_sen:
                max_average_distance = 0
                for charger in c:
                    average_distance = sum(chargers_to_km(charger, other_charger) for other_charger in c) / len(c)
                    if average_distance >= max_average_distance:
                        max_average_distance = average_distance
                        max_average_distance_charger = charger
                chargers.difference(c.remove(max_average_distance_charger))
                    # todo implement deletion
    # todo this method has waaaay too many loops, I should try to think of a way to achieve more in one loop
    return chargers

def string_from_data_to_date(str_date: str) -> datetime.date:
    """converts a string contained a date formatted in the style of US Dept. of Energy Vehicule Charging Station
    Locations to a datetime.date
    """
    # todo implement this
    raise NotImplementedError

def chargers_to_km(charger1: Charger, charger2: Charger) -> float:
    """
    Returns the great circle distance between two chargers
    :param charger1: First Charger
    :param charger2: Second Charger
    :return: Distance in Km
    """
    return longitude_and_latitude_to_km(charger1.longitude, charger1.latitude, charger2.longitude, charger2.latitude)

def longitude_and_latitude_to_km(long1: float, lat1: float, long2: float, lat2: float) -> float:
    """
    Returns the great circle distance between two points on the earth using equation:
        https://en.wikipedia.org/wiki/Great-circle_distance
    Earth radius:
        https://en.wikipedia.org/wiki/Earth_radius
    :param long1: Longitude value of first point
    :param lat1: Latitude value of first point
    :param long2: Longitude value of Second point
    :param lat2: Latitude value of first point
    :return: Distance in Km

    Preconditions:
    - -180 <= long1 <= 180
    - -90 <= lat1 <= 90
    - -180 <= long2 <= 180
    - -90 <= lat2 <= 90
    """
    EARTH_RADIUS_KM = 6371
    lat1_rad = ((2 * math.pi) / 180) * lat1
    long1_rad = ((2 * math.pi) / 180) * long1
    lat2_rad = ((2 * math.pi) / 180) * lat2
    long2_rad = ((2 * math.pi) / 180) * long2

    longitude_diff = abs(long1_rad - long2_rad)
    central_angle = math.acos((math.sin(lat1_rad) * math.sin(lat2_rad)) +
                              (math.cos(lat1_rad) * math.cos(lat2_rad) * math.cos(longitude_diff)))
    return EARTH_RADIUS_KM * central_angle
