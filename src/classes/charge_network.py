"""
Defines the ChargeNetwork class and related exceptions.
"""
import datetime
import json
import math
from queue import PriorityQueue
from typing import Self

from classes.charge_station import ChargeStation
from classes.leg import Leg
from utils.calcs import great_circle_distance


class ChargeNetwork:
    """
    A graph ADT representing a charge network.

    A charge station will not be in the graph if its DC fast chargers count is less than self.min_chargers_at_station.

    A leg will not be in the graph if its driving_distance is longer than self.ev_range.

    Instance Attributes:
        - min_chargers_at_station: the min number of DC fast chargers at each charge station in this graph (immutable)
        - ev_range: the max road distance in kilometers of each leg in this graph (immutable);
                    interpreted as the range of the EV vehicle this graph is based off of

    Representation Invariants:
        - all(all(cs in leg for leg in leg_set) for cs, leg_set in _graph.items())
    """
    # Private Instance Attributes:
    #   - _graph: a dict of charge stations and corresponding legs
    _min_chargers_at_station: int
    _ev_range: int
    _graph: dict[ChargeStation, set[Leg]]

    def __init__(self, min_chargers_at_station: int, ev_range: int) -> None:
        """Initializes an empty graph."""
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

    def charge_stations(self) -> set[ChargeStation]:
        """Returns a set of charge stations in the charge network."""
        return set(self._graph.keys())

    @classmethod
    def from_json(cls, filepath: str) -> Self:
        """Creates a ChargeNetwork object by unpacking the JSON file created by the export_to_json method."""
        with open(filepath, 'r') as file:
            data = json.load(file)

        min_chargers_at_station = data['min_chargers_at_station']
        ev_range = data['ev_range']

        network = cls(min_chargers_at_station, ev_range)

        # create all charge_stations
        charge_stations = {
            int(id): ChargeStation(
                cs['name'],
                cs['address'],
                cs['hours'],
                cs['phone'],
                cs['lat'],
                cs['lng'],
                datetime.datetime.strptime(cs['open_date'], '%Y-%m-%d').date() if cs['open_date'] else None
            )
            for id, cs in data['_graph']['charge_stations'].items()
        }

        # create set of all legs
        legs = {
            Leg(
                charge_stations[leg['endpoint_ids'][0]],
                charge_stations[leg['endpoint_ids'][1]],
                leg['driving_distance'],
                leg['driving_time']
            )
            for leg in data['_graph']['legs']}

        # add charge stations to graph
        for cs in charge_stations.values():
            network.add_charge_station(cs)

        # add edges to graph
        network.safe_load_legs(legs)

        return network

    def export_to_json(self, filepath: str) -> None:
        """
        Outputs a JSON file representing the ChargeNetwork self,
        using python id values of ChargeStation objects and _Leg objects.
        """
        charge_stations = {
            id(cs): {
                'name': cs.name,
                'address': cs.address,
                'hours': cs.hours,
                'phone': cs.phone,
                'lat': cs.lat,
                'lng': cs.lng,
                'open_date': str(cs.open_date) if cs.open_date else None
            }
            for cs in self._graph.keys()
        }

        legs = [
            {
                'endpoint_ids': [id(e) for e in leg.endpoints],
                'driving_distance': leg.driving_distance,
                'driving_time': leg.driving_time
            }
            for leg in set.union(*self._graph.values())  # removes duplicates since legs are equal if endpoints equal
        ]

        data = {
            'min_chargers_at_station': self.min_chargers_at_station,
            'ev_range': self.ev_range,
            '_graph': {
                'charge_stations': charge_stations,
                'legs': legs
            }
        }

        print(f'exporting network with {len(charge_stations)} charge stations and {len(legs)} legs to json')

        with open(filepath, 'w') as file:
            json.dump(data, file, indent=4)

    def charge_station_legs(self, cs: ChargeStation) -> set[Leg]:
        """
        Returns a set of legs that contain the given charge station in the charge network.

        Preconditions
            - charge_station in self._graph
        """
        return self._graph[cs]

    def add_charge_station(self, cs: ChargeStation, legs: set[Leg] = None) -> None:
        """
        Adds a charge station (and optionally a corresponding set of legs) to the graph.

        Preconditions:
            - station not in self._graph
         """
        if legs:
            self._graph[cs] = legs
        else:
            self._graph[cs] = set()

    def get_possible_legs(self) -> set[Leg]:
        """
        Returns a set of all legs that may be needed to complete this network.

        A leg that may be needed is one where the great circle distance between the two
        endpoints in less than self.ev_range. This is because a road distance between two
        charge stations will always be more than a great circle distance between two charge stations.
        """
        result = set()

        all_charge_stations = self.charge_stations()

        for i in all_charge_stations:
            for j in all_charge_stations:
                if i is not j and great_circle_distance(i.coord, j.coord) < self.ev_range:
                    edge = Leg(i, j)
                    if edge not in result:
                        result.add(edge)

        return result

    def safe_load_legs(self, legs: set[Leg]) -> None:
        """
        Takes a set of legs and mutates self by associating each leg with its 2 endpoints
        if its driving_distance is valid for this network.

        Preconditions:
            - all endpoints in all charge stations are in self
        """
        for leg in legs:
            if leg.driving_distance <= self.ev_range * 1000:
                for cs in leg.endpoints:
                    self._graph[cs].add(leg)

    def get_shortest_path(self,
                          cs1: ChargeStation,
                          cs2: ChargeStation,
                          min_leg_length: float,
                          max_leg_length: float) -> list[Leg]:
        """
        Implements A* search algorithm to return the shortest path by driving distance
        using great circle distance as heuristic since great circle distance
        will always be less than the actual shortest path (admissible and consistent).

        Returns a list of legs leading from cs1 to cs2 if a path is found.

        Raises PathNotFound or PathNotNeeded.

        min_leg_length and max_leg_length are in kilometers.

        Preconditions:
            - cs1 in self._graph and cs2 in self._graph
            - min_leg_length <= max_leg_length
            - max_leg_length <= self.ev_range
        """
        if cs1 is cs2:
            raise PathNotNeeded

        min_leg_length *= 1000  # todo convert all distances to meters
        max_leg_length *= 1000

        # fringe contains tuple of 3 values
        #     - index 0 is f_score
        #     - index 1 is a decreasing counter to ensure LIFO tie breaks and that remaining elements are never compared
        #     - index 2 is the charge station
        fringe = PriorityQueue()
        lifo_counter = -1
        fringe.put((0, lifo_counter, cs1))

        # for node n, prev_legs[n] is the leg leading to n in the shortest path currently known to n
        prev_legs = {}

        g_score = {cs: math.inf for cs in self.charge_stations()}
        g_score[cs1] = 0

        while not fringe.empty():
            curr = fringe.get()
            curr_cs = curr[2]

            if curr_cs is cs2:
                return self._reconstruct_path(prev_legs, cs2)

            for leg in self.charge_station_legs(curr_cs):

                if leg.driving_distance < min_leg_length or leg.driving_distance > max_leg_length:
                    continue  # ignore legs that do not fit length criteria

                neighbour = leg.get_other_endpoint(curr_cs)

                # since our heuristic is admissible and consistent, we will only need to
                # calculate g_score and add to fringe once per charge station
                if g_score[neighbour] == math.inf:
                    prev_legs[neighbour] = leg
                    g_score[neighbour] = g_score[curr_cs] + leg.driving_distance
                    f_score = g_score[neighbour] + great_circle_distance(neighbour.coord, cs2.coord)
                    fringe.put((f_score, lifo_counter, neighbour))
                    lifo_counter -= 1

        raise PathNotFound

    def _reconstruct_path(self, prev_legs: dict[ChargeStation, Leg], end: ChargeStation) -> list[Leg]:
        """Returns a list of legs leading from the start charge station in prev_edges to end."""
        if end not in prev_legs:
            return []
        else:
            return self._reconstruct_path(prev_legs, prev_legs[end].get_other_endpoint(end)) + [prev_legs[end]]


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
