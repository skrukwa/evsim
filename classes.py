"""The classes.py module of the ev-trip-sim project.
https://github.com/skrukwa/ev-trip-sim

Description
===========

This module specifies the following:
  - ChargeStation (ADT graph vertex) dataclass
  - _Edge (ADT graph edge) dataclass
  - ChargeNetwork (ADT graph) class

Copyright and Usage Information
===============================

This file is distributed under the ev-trip-sim project which is
bounded by the terms of Apache License Version 2.0. For more
information, please follow the github link above.

This file is Copyright (c) Evan Skrukwa and Nadim Mottu.
"""
from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Optional

import calcs


@dataclass(frozen=True)
class ChargeStation:
    """A dataclass representing a charger station.
    This dataclass is used as vertices in the ChargeNetwork class.
    Also, this dataclass in immutable so that it is hashable.

    Instance Attributes:
        - name: station name
        - address: street address
        - hours: hours of operation (access times)
        - latitude: the station's latitude
        - longitude: the station's longitude
        - open_date: the station's open date
    """
    name: str
    address: str
    hours: str
    latitude: float
    longitude: float
    open_date: datetime.date

    @property
    def coord(self) -> tuple[float, float]:
        """Returns the latitude, longitude pair of this charge station"""
        return self.latitude, self.longitude


class _Edge:
    """A dataclass representing an edge (driving route) from one charge station to another.

    An edge is said to be equal to another if its endpoints are equal.

    NOTE: A user of this class is forbidden to create duplicate edges (it will result in duplicate hashes).

    Instance Attributes:
        - endpoints: the start and end charge stations of this edge (immutable)
        - road_distance: the driving distance between endpoints in kilometers
        - time: the driving duration between endpoints in seconds

    Representation Invariants:
        - len(self.endpoints) == 2
    """
    _endpoints: set[ChargeStation]
    road_distance: Optional[float]
    time: Optional[int]

    def __init__(self,
                 charger1: ChargeStation,
                 charger2: ChargeStation,
                 road_distance: float = None,
                 time: int = None) -> None:

        self._endpoints = {charger1, charger2}
        self.road_distance = road_distance
        self.time = time

    @property
    def endpoints(self) -> set[ChargeStation]:
        """A getter for self.endpoints."""
        return self._endpoints

    def get_other_endpoint(self, charger: ChargeStation) -> ChargeStation:
        """Returns the endpoint that isn't the input charger"""
        return (self._endpoints - {charger}).pop()

    def __eq__(self, other: _Edge) -> bool:
        """Return equality (based on endpoints) between self and other."""
        return self.endpoints == other.endpoints

    def __hash__(self) -> int:
        """Return the hash value."""
        coords = [charger.coord for charger in self.endpoints]
        coords.sort()
        return hash((self.__class__, coords[0], coords[1]))


class ChargeNetwork:
    """A graph ADT representing a charge network.

    An edge from one charge station to another will not be considered (in the graph) if its
    road_distance is longer than self._ev_range.

    Instance Attributes:
        - ev_range: the range of the EV vehicle this graph is based off of in kilometers (immutable)
        - min_chargers_at_station: the min sum of type 2 and type DC chargers at each
                                   charge station in this graph (immutable)

    Representation Invariants:
        - all(all(charger in edge for edge in edge_set) for charger, edge_set in _graph.items())
    """
    # Private Instance Attributes:
    #   - _graph: a dict of charge stations and corresponding edges
    _min_chargers_at_station: int
    _ev_range: int
    _graph: dict[ChargeStation, set[_Edge]]

    def __init__(self, min_chargers_at_station: int, ev_range: int) -> None:
        """Initialize an empty graph."""
        self._min_chargers_at_station = min_chargers_at_station
        self._ev_range = ev_range
        self._graph = {}

    @property
    def min_chargers_at_station(self) -> int:
        """A getter for self._min_chargers_at_station."""
        return self._min_chargers_at_station

    @property
    def ev_range(self) -> int:
        """A getter for self._ev_range."""
        return self._ev_range

    def is_empty(self) -> bool:
        """Returns whether this graph is empty."""
        return not self._graph

    def charge_stations(self) -> set[ChargeStation]:
        """Returns a set of charge stations in the charge network."""
        return set(self._graph.keys())

    def corresponding_edges(self, charge_station: ChargeStation) -> set[_Edge]:
        """Returns a set of edges corresponding to charge_station in the charge network.

        Preconditions
            - charge_station in self._graph
        """
        return self._graph[charge_station]

    def add_charge_station(self, station: ChargeStation, edges: set[_Edge]) -> None:
        """Adds a charge station (and optionally a corresponding set of edges) to the graph.

        Preconditions:
            - station not in self._graph
         """
        self._graph[station] = edges

    def get_list_of_possible_edges(self) -> list[_Edge]:
        """Returns a list of all edges that may be needed to complete this network.

        An edge that may be needed is one where the great circle distance between the two
        endpoints in less than self.ev_range. This is because a road distance between two
        charge stations will always be more than a great circle distance between two charge stations.

        The returned list will have no duplicates in it (and is only a list due to hashing constraints).
        """
        result = []

        all_charge_stations = self.charge_stations()

        for i in all_charge_stations:
            for j in all_charge_stations:
                if i != j and calcs.great_circle_distance(i.coord, j.coord) < self.ev_range:
                    edge = _Edge(i, j)
                    if edge not in result:
                        result.append(edge)

        return result

    def load_edges(self, edges: list[_Edge]) -> None:
        """Takes a list of edges and mutates self by associating each edge with its 2 endpoints.

        Preconditions:
            - self has no edges in it
            - all endpoints in all chargers are in self
        """
        for edge in edges:
            if edge.road_distance < self.ev_range:
                for charge_station in edge.endpoints:
                    self._graph[charge_station].add(edge)

    # THE REST OF THE CODE IS SHORTEST WEIGHTED PATH FINDING

    def get_hereditary_edges(self, initial: ChargeStation, final: ChargeStation) -> list[_Edge]:
        """Orders and slices the given list of charge stations based on great circle distance to the destination.

        Used in a greedy path finding implementation to reduce number of paths which need to be checked.
        """
        lst = list(self._graph[initial])

        lst.sort(key=lambda u: calcs.great_circle_distance(u.get_other_endpoint(initial).coord, final.coord))
        return lst[:2]

    def get_shortest_path(self, charger1: ChargeStation, charger2: ChargeStation) -> Optional[list[_Edge]]:
        """Return a sequence of edges that represent a path from charger1 to charger2
        in this graph which minimizes the total travel time, or None if no path is found.

        Preconditions:
            - charger1 in self._graph
            - charger2 in self._graph
        """
        return self.get_shortest_path_helper(charger1, charger2, set(), None)

    def get_shortest_path_helper(self,
                                 charge1: ChargeStation,
                                 charge2: ChargeStation,
                                 visited: set[ChargeStation],
                                 min_length: Optional[float]) -> Optional[list[_Edge]]:
        """Recursive helper for the get_shortest_path method."""
        if charge1 == charge2:
            return []

        my_output = None
        new_min = min_length
        v2 = visited.copy()
        v2.add(charge1)
        if new_min is not None and new_min <= 0:
            return None
        for u in self.get_hereditary_edges(charge1, charge2):
            other_charger = u.get_other_endpoint(charge1)
            if other_charger not in visited:
                if new_min is not None:
                    neighbors_path = self.get_shortest_path_helper(
                        other_charger, charge2, v2, new_min - u.time
                    )
                else:
                    neighbors_path = self.get_shortest_path_helper(other_charger, charge2, v2, None)
                if neighbors_path is not None:
                    neighbors_path_len = sum([i.time for i in neighbors_path]) + u.time
                    if new_min is None or new_min > neighbors_path_len:
                        new_min = neighbors_path_len
                        my_output = ([u] + neighbors_path)
        return my_output


if __name__ == '__main__':
    import doctest
    doctest.testmod()

    import python_ta
    python_ta.check_all(config={
        'max-line-length': 120,
        'disable': ['forbidden-import', 'too-many-nested-blocks']
    })
