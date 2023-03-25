"""Implementing functions related to the process of removing clusters from our ChargeNetwork"""
from __future__ import annotations
from typing import Any, Optional
import math
from classes import ChargeNetwork, ChargeStation


class TreeCluster:
    """Tree class designed to group charge stations into clusters
    The leaves of the tree are actual existing charge stations

    Representation Invariants:
    - self._centroid is not None or self._subcluster == []
    """
    # Private Instance Attributes:
    #   - _centroid:
    #       The centermost chargestation in the subtree. None if the tree is empty.
    #   - _subcluster:
    #       The list of subclusters of this tree. This attribute is empty when
    #       self._root is None (representing an empty tree). However, this attribute
    #       may be empty when self._root is not None, which represents a tree consisting
    #       of just one item.
    _centroid: Optional[ChargeStation]
    _complete: bool
    _distance: float
    _subcluster: list[TreeCluster]

    def __init__(self, distance: float, stations: Optional[list[ChargeStation]] = None) -> None:
        """Initialize a new Tree with the given root value and subtrees.

        If root is None, the tree is empty.
        Preconditions:
            - root is not none or subtrees == []
        """
        self._subcluster = []
        if stations is None:
            self._centroid = None
        elif len(stations) == 1:
            self._centroid = stations[0]
        else:
            for i in stations:
                self._subcluster.append(TreeCluster(distance, [i]))
            self._centroid = find_lowest_average_distance(stations)
        self._distance = distance
        self._complete = False

    def is_empty(self) -> bool:
        """Return whether this tree is empty.
        """
        return self._centroid is None

    def get_cluster_free_list(self) -> list[ChargeStation]:
        """returns a list of all the stations in the tree after
        removing all elements part of a cluster other than the centroids"""
        if self._complete:
            return [self._centroid]
        else:
            return_val = []
            for i in self._subcluster:
                return_val.extend(i.get_cluster_free_list())
            return return_val

    def get_list_of_clusters(self) -> list[list[ChargeStation]]:
        """returns a list of lists containing each subcluster"""
        if self._complete:
            return [[self._centroid] + [tree._centroid for tree in self._subcluster]]
        else:
            return_val = []
            for i in self._subcluster:
                return_val.extend(i.get_list_of_clusters())
            return return_val

    def create_subclusters(self) -> None:
        """"splits the leafs into subclusters"""
        if len(self._subcluster) < 2 or all(chargers_to_km(c1._centroid, c2._centroid) < self._distance for c1 in
                                            self._subcluster for c2 in self._subcluster):
            self._complete = True
            return
        # else
        reference_stations = find_furthest_charge_stations([tree._centroid for tree in self._subcluster])
        # print(reference_stations)
        new_cluster1 = []
        new_cluster2 = []
        for i in self._subcluster:
            if chargers_to_km(i._centroid, reference_stations[0]) < chargers_to_km(i._centroid, reference_stations[1]):
                new_cluster1.append(i._centroid)
            else:
                new_cluster2.append(i._centroid)
        self._subcluster = [TreeCluster(self._distance, new_cluster1),
                            TreeCluster(self._distance, new_cluster2)]
        self._subcluster[0].create_subclusters()
        self._subcluster[1].create_subclusters()

def chargers_to_km(charger1: ChargeStation, charger2: ChargeStation) -> float:
    """
    Returns the great circle distance between two chargers
    :param charger1: First Charger
    :param charger2: Second Charger
    :return: Distance in Km
    """
    return longitude_and_latitude_to_km(charger1.longitude, charger1.latitude, charger2.longitude,
                                        charger2.latitude)


def clusterGraph(graph: ChargeNetwork, distance: float) -> None:
    """Mutates graph by removing all clustered charge station

    Precondition:
    - Graph has no paths (they will all be deleted!)
    """
    cluster_tree = TreeCluster(distance, graph.get_charge_stations())
    cluster_tree.create_subclusters()
    graph.clear_graph()
    for i in cluster_tree.get_cluster_free_list():
        graph.add_charge_station(i, None)



def find_furthest_charge_stations(chargers: list[ChargeStation]) -> tuple[ChargeStation, ChargeStation]:
    """Finds the two charge stations that are the furthest away if there are fewer than 2 charge stations
    raise index error
    """
    n = len(chargers)
    if n < 2:
        raise IndexError

    max_distance = 0
    point1 = chargers[0]
    point2 = chargers[1]

    # compare each pair of points and update furthest points
    for i in range(n):
        for j in range(i + 1, n):
            distance = chargers_to_km(chargers[i], chargers[j])
            if distance > max_distance:
                max_distance = distance
                point1 = chargers[i]
                point2 = chargers[j]

    return (point1, point2)

def find_lowest_average_distance(chargers: list[ChargeStation]):
    """"
    Takes a list of ChargeStations coords and returns the ChargeStation with the lowest average distance to all other
    charge stations
    """
    min_avg_distance = float('inf')
    min_index = 0
    for i in range(len(chargers)):
        total_distance = 0
        for j in range(len(chargers)):
            if i != j:
                total_distance += chargers_to_km(chargers[i], chargers[j])
        avg_distance = total_distance / (len(chargers)-1)
        if avg_distance < min_avg_distance:
            min_avg_distance = avg_distance
            min_index = i
    return chargers[min_index]


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

    >>> round(longitude_and_latitude_to_km(-179, 50, 100, -50))
    13508
    """
    EARTH_RADIUS_KM = 6371
    lat1_rad = (math.pi / 180) * lat1
    long1_rad = (math.pi / 180) * long1
    lat2_rad = (math.pi / 180) * lat2
    long2_rad = (math.pi / 180) * long2

    latitude_diff = abs(lat1_rad - lat2_rad)
    longitude_diff = abs(long1_rad - long2_rad)
    central_angle = 2 * (math.asin(math.sqrt(hav(latitude_diff) + (1 - hav(latitude_diff) - hav(lat1_rad + lat2_rad))
                                             * hav(longitude_diff))))
    return EARTH_RADIUS_KM * central_angle

def hav(num: float) -> float:
    """returns the harversine of the number"""
    return math.sin(num / 2) ** 2


# def remove_cluster(network: ChargeNetwork, threshold: float, sens: int) -> ChargeNetwork:
#     charge_stations = network.get_charge_stations()
#     data = [[station.latitude, station.longitude] for station in charge_stations()]
#     birch_tree = Birch(n_clusters=None, threshold=threshold)
#     birch_tree.fit(data)
#     labels = birch_tree.fit_predict(data)
#     clusters = {}
#     for i in range(len(labels)):
#         if labels[i] not in clusters:
#             clusters[labels[i]] = []
#         clusters[labels[i]] += charge_stations[i]
#     final_charger_list = []
#     for j in clusters:
#         if len(j) >= sens:
#             final_charger_list += birch_tree.
#     return NotImplemented


"""
Create a function that assigns a cluster to every charger to a cluster, then create a new tree with only the centroids

New implementation:
- Function(graph) -> return list[list[chargers]] with clusters
- Bottom up approach to tree clustering
- Check that it runs well
- Check it looks good


"""
