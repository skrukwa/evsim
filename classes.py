"""
----------Objectives----------
Define custom classes to be used in other files.
"""
import datetime
import json
import math
from dataclasses import dataclass
from queue import PriorityQueue
from typing import Optional, Self

import calcs


class PathNotNeeded(Exception):
    """Exception raised when trying to find a path between the same 2 charge stations."""

    def __str__(self) -> str:
        """Return a string representation of this error."""
        return 'tried to find a path between the same 2 charge stations'


class PathNotFound(Exception):
    """Exception raised when a path between 2 charge stations does not exist."""

    def __str__(self) -> str:
        """Return a string representation of this error."""
        return 'no path between the 2 charge stations was found'


@dataclass(eq=False, frozen=True)
class ChargeStation:
    """
    A dataclass representing a charger station.

    This dataclass is used as vertices in the ChargeNetwork class.

    This dataclass in immutable so that it is hashable.

    This class falls back to id based hashing and equality checking (due to the eq=False argument).

    Instance Attributes:
        - name: station name
        - address: street address
        - hours: hours of operation
        - phone: phone number
        - latitude: the station's latitude
        - longitude: the station's longitude
        - open_date: the station's open date
    """
    name: Optional[str]
    address: Optional[str]
    hours: Optional[str]
    phone: Optional[str]
    latitude: float
    longitude: float
    open_date: Optional[datetime.date]

    @property
    def coord(self) -> tuple[float, float]:
        """Returns the latitude, longitude pair of this charge station"""
        return self.latitude, self.longitude

    @property
    def dict(self) -> dict[str, str]:
        return {
            "name": self.name,
            "address": self.address,
            "hours": self.hours,
            "phone": self.phone,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "open_date": f'{self.open_date:%B %d %Y}'.replace(' 0', ' ') if self.open_date else None
        }


class _Edge:
    """
    A dataclass representing an edge (driving route) from one charge station to another.

    An edge is said to be equal to another if its endpoints are equal.

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
        """Initializes the object."""

        self._endpoints = {charger1, charger2}
        self.road_distance = road_distance
        self.time = time

    @property
    def endpoints(self) -> set[ChargeStation]:
        """A getter for self.endpoints."""
        return self._endpoints

    def get_other_endpoint(self, charger: ChargeStation) -> ChargeStation:
        """Returns the endpoint that isn't the input charger."""
        return (self._endpoints - {charger}).pop()

    def __eq__(self, other: Self) -> bool:
        """
        Return equality (based on endpoints) between self and other.

        Used in ChargeNetwork.get_possible_edges
        """
        return self.endpoints == other.endpoints

    def __hash__(self) -> int:
        """
        Return the hash value.

        Lets _Edge objects be stored in sets.
        """
        coords = [charger.coord for charger in self.endpoints]
        coords.sort()
        return hash((self.__class__, coords[0], coords[1]))


class ChargeNetwork:
    """
    A graph ADT representing a charge network.

    An edge from one charge station to another will not be in the graph if
    its road_distance is longer than self._ev_range.

    Instance Attributes:
        - min_chargers_at_station: the min number of DC fast chargers at each charge station in this graph (immutable)
        - ev_range: the range of the EV vehicle this graph is based off of in kilometers (immutable)

    Representation Invariants:
        - all(all(charger in edge for edge in edge_set) for charger, edge_set in _graph.items())
    """
    # Private Instance Attributes:
    #   - _graph: a dict of charge stations and corresponding edges
    _min_chargers_at_station: int
    _ev_range: int
    _graph: dict[ChargeStation, set[_Edge]]

    def __init__(self, min_chargers_at_station: int, ev_range: int) -> None:
        """Initializes an empty graph."""
        self._min_chargers_at_station = min_chargers_at_station
        self._ev_range = ev_range
        self._graph = {}

    @classmethod
    def from_json(cls, filepath: str) -> Self:
        """
        Creates a ChargeNetwork object by unpacking the JSON file created by the export_to_json method.
        """
        with open(filepath, 'r') as file:
            data = json.load(file)

        min_chargers_at_station = data['min_chargers_at_station']
        ev_range = data['ev_range']

        network = cls(min_chargers_at_station, ev_range)

        # create all charge_stations
        charge_stations = {
            int(id): ChargeStation(
                latitude=cs['latitude'],
                longitude=cs['longitude'],
                name=cs['name'],
                phone=cs['phone'],
                address=cs['address'],
                hours=cs['hours'],
                open_date=datetime.datetime.strptime(cs['open_date'], '%Y-%m-%d').date() if cs['open_date'] else None
            )
            for id, cs in data['_graph']['cs'].items()
        }

        # create all edges
        edges = {_Edge(
            charge_stations[edge['endpoint_ids'][0]],
            charge_stations[edge['endpoint_ids'][1]],
            edge['road_distance'],
            edge['time']
        ) for edge in data['_graph']['e']}

        # add charge stations to graph
        for cs in charge_stations.values():
            network.add_charge_station(cs, set())

        # add edges to graph
        network.load_edges(edges)

        return network

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
        """
        Returns a set of edges corresponding to charge_station in the charge network.

        Preconditions
            - charge_station in self._graph
        """
        return self._graph[charge_station]

    def add_charge_station(self, station: ChargeStation, edges: set[_Edge]) -> None:
        """
        Adds a charge station (and optionally a corresponding set of edges) to the graph.

        Preconditions:
            - station not in self._graph
         """
        self._graph[station] = edges

    def get_possible_edges(self) -> set[_Edge]:
        """
        Returns a set of all edges that may be needed to complete this network.

        An edge that may be needed is one where the great circle distance between the two
        endpoints in less than self.ev_range. This is because a road distance between two
        charge stations will always be more than a great circle distance between two charge stations.
        """
        result = set()

        all_charge_stations = self.charge_stations()

        for i in all_charge_stations:
            for j in all_charge_stations:
                if i is not j and calcs.great_circle_distance(i.coord, j.coord) < self.ev_range:
                    edge = _Edge(i, j)
                    if edge not in result:
                        result.add(edge)

        return result

    def load_edges(self, edges: set[_Edge]) -> None:
        """
        Takes a list of edges and mutates self by associating each edge with its 2 endpoints
        if its road_distance is valid for this network.

        Preconditions:
            - self has no edges in it
            - all endpoints in all chargers are in self
        """
        for edge in edges:
            if edge.road_distance < self.ev_range:
                for charge_station in edge.endpoints:
                    self._graph[charge_station].add(edge)

    def get_shortest_path(self,
                          charger1: ChargeStation,
                          charger2: ChargeStation,
                          min_leg_length: float,
                          max_leg_length: float) -> Optional[list[_Edge]]:
        """
        Implements A* search algorithm using great circle distance as heuristic since
        great circle distance will always be less than the actual shortest path.

        Returns a list of edges leading from charger1 to charger2 if a path is found.

        Raises PathNotFound or PathNotNeeded.

        min_leg_length and max_leg_length are in kilometers.

        Preconditions:
            - charger1 in self._graph and charger2 in self._graph
        """
        # implementation note: fringe contents are stored to enable (constant time) membership checking,
        #                      as well as being able to "remove" items from fringe by mutating their value
        #                      at index 2 to False

        fringe = PriorityQueue()  # possible chargers to expand search to

        # fringe contains lists of 4 values
        #     - index 0 is f_score
        #     - index 1 is entry index to ensure LIFO tie breaks and that remaining elements are never compared
        #     - index 2 is whether this item is valid or has instead been re-added to the queue
        #       (non-valid lists do not have their charger in fringe_contents)
        #     - index 3 is the charger

        fringe.put([0, 1, True, charger1])

        fringe_contents = {}  # maps charger in queue to its list in queue

        prev_edges = {}  # for node n, prev_edges[n] is the edge leading to n in the shortest path currently known to n

        g_scores = {charger: math.inf for charger in self._graph}
        g_scores[charger1] = 0

        entry_index = 0
        while not fringe.empty():
            current_list = fringe.get()
            if not current_list[2]:
                continue

            current_charger = current_list[3]

            if current_charger is charger2:
                result = self._reconstruct_path(charger2, prev_edges)
                if result:
                    return result
                raise PathNotNeeded

            for edge in self.corresponding_edges(current_charger):

                if min_leg_length < edge.road_distance < max_leg_length:  # ignore edges that do not fit length criteria

                    neighbour = edge.get_other_endpoint(current_charger)
                    temp_neighbour_g_score = g_scores[current_charger] + edge.road_distance

                    if temp_neighbour_g_score < g_scores[neighbour]:
                        # this path to neighbour is better than any previous one
                        prev_edges[neighbour] = edge
                        g_scores[neighbour] = temp_neighbour_g_score

                        f_score = g_scores[neighbour] + calcs.great_circle_distance(neighbour.coord, charger2.coord)

                        if neighbour in fringe_contents:  # update f_score of neighbour in fringe
                            fringe_contents[neighbour][2] = False
                        fringe_contents[neighbour] = [f_score, entry_index, True, neighbour]
                        fringe.put(fringe_contents[neighbour])
                        entry_index -= 1

        raise PathNotFound

    def _reconstruct_path(self, end: ChargeStation, prev_edges: dict[ChargeStation, _Edge]) -> list[_Edge]:
        """Returns a list of edges leading from the start charger in prev_edges to end in that order."""
        if end not in prev_edges:
            return []
        else:
            return self._reconstruct_path(prev_edges[end].get_other_endpoint(end), prev_edges) + [prev_edges[end]]

    def export_to_json(self, filepath: str) -> None:
        """
        Outputs a JSON file representing the ChargeNetwork self, using python id values
        of ChargeStation objects and _Edge objects.
        """
        charge_stations = {
            id(cs): {
                'name': cs.name,
                'address': cs.address,
                'hours': cs.hours,
                'phone': cs.phone,
                'latitude': cs.latitude,
                'longitude': cs.longitude,
                'open_date': str(cs.open_date) if cs.open_date else None
            }
            for cs in self._graph.keys()
        }

        edges = [
            {
                'endpoint_ids': [id(e) for e in edge.endpoints],
                'road_distance': edge.road_distance,
                'time': edge.time
            }
            for edge in set.union(*self._graph.values())  # removes duplicates since edges are equal if endpoints equal
        ]

        data = {
            'min_chargers_at_station': self.min_chargers_at_station,
            'ev_range': self.ev_range,
            '_graph': {
                'cs': charge_stations,
                'e': edges
            }
        }

        print(f'exporting network with {len(charge_stations)} charge stations and {len(edges)} edges to json')

        with open(filepath, 'w') as file:
            json.dump(data, file, indent=4)
