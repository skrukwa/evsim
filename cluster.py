"""
----------Objectives----------
Create a Divisive Hierarchical Clustering tree containing charge stations.
"""
from typing import Self

import calcs
from classes import ChargeStation


class ClusterTree:
    """
    A recursive Divisive Hierarchical Clustering tree which clusters charge stations until
    each cluster has a diameter less than max_cluster_diameter.

    After being fully initialized,
        - every charge station in the graph can be found as a leaf
        - every leaf is a ChargeStation object
        - every non-leaf is a ClusterTree object
        - every direct parent of a leaf is the centroid of a cluster of charge points
          which are its children (including itself)
        - given any node, a child is a leaf if and only if all children are leafs

    Instance Attributes:
        - max_cluster_diameter: the diameter in kilometers of a circle such that clusters which fit
                                into the circle will not be further split up (immutable)

    Representation Invariants:
        - _max_cluster_diameter >= 0
    """
    _centroid: ChargeStation
    _subclusters: set[Self | ChargeStation]
    _max_cluster_diameter: float

    def __init__(self, charge_stations: set[ChargeStation], max_cluster_diameter: float) -> None:
        """
        Recursively initialize the tree using Divisive Hierarchical Clustering as referenced below.

        https://en.wikipedia.org/wiki/Hierarchical_clustering

        This algorithm's structure roughly follows the steps outlined below.

        STEP 1.
        Assign the root as one charge station which represents the cluster of all charge stations given
        (and all charge stations below it in the tree) by minimizing the average distance to all
        other charge stations.

        STEP 2.
        If all the charge stations are within the cluster distance specified then each charge
        station can be added as a child of root, and the root represents the cluster.
        Note that this implicitly covers len(charge_stations) == 1 since the distance would then be 0.

        Otherwise, the charge stations are then split into two groups and recursed on (meaning
        that this tree will be binary if we ignore leafs). This is done by picking the charge
        stations that are the furthest apart, and then dividing the charge stations into two groups
        depending based on the distance of each charge station to two chosen charge stations.

        Preconditions:
            - len(charge_stations) >= 1
        """
        self._max_cluster_diameter = max_cluster_diameter

        # STEP 1. assign _centroid to be the charge station with the lowest average distance
        #         to all charge stations it represents

        self._centroid = calcs.find_lowest_average_distance(
            points=charge_stations,
            distance_func=calcs.great_circle_distance,
            coords_key=lambda charger: charger.coord
        )

        # STEP 2. see if the charge stations need to be further clustered

        charge_station1, charge_station2 = calcs.find_furthest_apart(
            points=charge_stations,
            distance_func=calcs.great_circle_distance,
            coords_key=lambda charger: charger.coord
        )

        distance_furthest_apart = calcs.great_circle_distance(charge_station1.coord, charge_station2.coord)

        if distance_furthest_apart <= self.max_cluster_diameter:
            self._subclusters = charge_stations
        else:
            new_cluster1 = set()
            new_cluster2 = set()
            for charge_station in charge_stations:
                if calcs.great_circle_distance(charge_station.coord, charge_station1.coord) < \
                        calcs.great_circle_distance(charge_station.coord, charge_station2.coord):
                    new_cluster1.add(charge_station)
                else:
                    new_cluster2.add(charge_station)

            self._subclusters = {
                ClusterTree(new_cluster1, max_cluster_diameter),
                ClusterTree(new_cluster2, max_cluster_diameter)
            }

    @property
    def max_cluster_diameter(self) -> float:
        """An immutable getter for self._max_cluster_diameter."""
        return self._max_cluster_diameter

    def get_list_of_clusters(self) -> list[list[ChargeStation]]:
        """
        Returns a list of clusters of charge stations by traversing the
        tree in order to accumulate all groups of leafs.
        """

        assert self._subclusters  # we should not have recursed into leafs

        random_child = next(iter(self._subclusters))

        if isinstance(random_child, ChargeStation):  # the child is a leaf, so in this tree, all children are leafs
            return [list(self._subclusters)]

        else:  # the child is not a leaf, so in this tree, all children are not leafs
            result = []
            for child in self._subclusters:
                result.extend(child.get_list_of_clusters())
            return result

    def get_list_of_final_centroids(self) -> list[ChargeStation]:
        """
        Returns a list of charge stations which are the centroids representing the clusters
        of charge stations by traversing the tree in order to accumulate all parents of groups of leafs.
        """

        assert self._subclusters  # we should not have recursed into leafs

        random_child = next(iter(self._subclusters))

        if isinstance(random_child, ChargeStation):  # the child is a leaf, so in this tree, all children are leafs
            return [self._centroid]

        else:  # the child is not a leaf, so in this tree, all children are not leafs
            result = []
            for child in self._subclusters:
                result.extend(child.get_list_of_final_centroids())
            return result
