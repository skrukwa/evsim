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


@dataclass(eq=False)
class ChargeStation:
    """
    A dataclass representing a charger station.

    This dataclasses objects are used as vertices in the ChargeNetwork class.

    This dataclass in immutable and falls back to id based hashing and equality checking (due to the eq=False argument).

    Instance Attributes:
        - name: station name
        - address: street address
        - hours: hours of operation
        - phone: phone number
        - lat: the station's latitude
        - lng: the station's longitude
        - open_date: the station's open date
    """
    name: Optional[str]
    address: Optional[str]
    hours: Optional[str]
    phone: Optional[str]
    lat: float
    lng: float
    open_date: Optional[datetime.date]

    @property
    def coord(self) -> tuple[float, float]:
        """Returns the latitude, longitude pair of this charge station."""
        return self.lat, self.lng

    @property
    def formatted_dict(self) -> dict[str, str]:
        """Returns a version of vars(self) with content formatted for user display."""
        result = vars(self).copy()

        if result['open_date'] is not None:
            result['open_date'] = f"{result['open_date']:%B %d %Y}".replace(' 0', ' ')

        for key, value in result.items():
            if value is None:
                result[key] = 'not available'

        return result


class _Leg:
    """
    A dataclass representing a driving leg from one charge station to another.

    This dataclasses objects are used as edges in the ChargeNetwork class.

    A leg is said to be equal to another if its endpoints are equal.

    Instance Attributes:
        - endpoints: start and end charge stations of this edge (immutable)
        - driving_distance: road distance between endpoints in meters
        - driving_time: time spent driving between endpoints in seconds

    Representation Invariants:
        - len(self.endpoints) == 2
    """
    _endpoints: set[ChargeStation]
    driving_distance: Optional[int]
    driving_time: Optional[int]

    def __init__(self,
                 cs1: ChargeStation,
                 cs2: ChargeStation,
                 driving_distance: int = None,
                 driving_time: int = None) -> None:
        """Initializes the object."""
        self._endpoints = {cs1, cs2}
        self.driving_distance = driving_distance
        self.driving_time = driving_time

    @property
    def endpoints(self) -> set[ChargeStation]:
        """A getter for self.endpoints."""
        return self._endpoints

    def get_other_endpoint(self, cs: ChargeStation) -> ChargeStation:
        """Returns the endpoint that isn't the input charge station."""
        return (self._endpoints - {cs}).pop()

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
        coords = [cs.coord for cs in self.endpoints]
        coords.sort()
        return hash((self.__class__, coords[0], coords[1]))


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
    _graph: dict[ChargeStation, set[_Leg]]

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

    def corresponding_legs(self, cs: ChargeStation) -> set[_Leg]:
        """
        Returns a set of legs corresponding to the given charge station in the charge network.

        Preconditions
            - charge_station in self._graph
        """
        return self._graph[cs]

    def add_charge_station(self, cs: ChargeStation, legs: set[_Leg] = None) -> None:
        """
        Adds a charge station (and optionally a corresponding set of legs) to the graph.

        Preconditions:
            - station not in self._graph
         """
        if legs:
            self._graph[cs] = legs
        else:
            self._graph[cs] = set()

    def get_possible_legs(self) -> set[_Leg]:
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
                if i is not j and calcs.great_circle_distance(i.coord, j.coord) < self.ev_range:
                    edge = _Leg(i, j)
                    if edge not in result:
                        result.add(edge)

        return result

    def safe_load_legs(self, legs: set[_Leg]) -> None:
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
                          max_leg_length: float) -> list[_Leg]:
        """
        Implements A* search algorithm using great circle distance as heuristic since
        great circle distance will always be less than the actual shortest path.

        Returns a list of legs leading from cs1 to cs2 if a path is found.

        Raises PathNotFound or PathNotNeeded.

        min_leg_length and max_leg_length are in kilometers.

        Preconditions:
            - cs1 in self._graph and cs2 in self._graph
        """
        min_leg_length *= 1000
        max_leg_length *= 1000

        # implementation note: fringe contents are stored to enable (constant time) membership checking,
        #                      as well as being able to "remove" items from fringe by mutating their value
        #                      at index 2 to False

        fringe = PriorityQueue()  # possible chargers to expand search to

        # fringe contains lists of 4 values
        #     - index 0 is f_score
        #     - index 1 is entry index to ensure LIFO tie breaks and that remaining elements are never compared
        #     - index 2 is whether this item is valid or has instead been re-added to the queue
        #       (non-valid lists do not have their charger in fringe_contents)
        #     - index 3 is the charge station

        fringe.put([0, 1, True, cs1])

        fringe_contents = {}  # maps charger in queue to its list in queue

        prev_legs = {}  # for node n, prev_legs[n] is the leg leading to n in the shortest path currently known to n

        g_scores = {cs: math.inf for cs in self.charge_stations()}
        g_scores[cs1] = 0

        entry_index = 0
        while not fringe.empty():
            curr_list = fringe.get()
            if not curr_list[2]:
                continue

            curr_cs = curr_list[3]

            if curr_cs is cs2:
                result = self._reconstruct_path(prev_legs, cs2)
                if result:
                    return result
                else:
                    raise PathNotNeeded

            for leg in self.corresponding_legs(curr_cs):

                if min_leg_length < leg.driving_distance < max_leg_length:  # ignore legs that do not fit length criteria

                    neighbour = leg.get_other_endpoint(curr_cs)
                    neighbour_temp_g_score = g_scores[curr_cs] + leg.driving_distance

                    if neighbour_temp_g_score < g_scores[neighbour]:
                        # this path to neighbour is better than any previous one
                        prev_legs[neighbour] = leg
                        g_scores[neighbour] = neighbour_temp_g_score

                        f_score = g_scores[neighbour] + calcs.great_circle_distance(neighbour.coord, cs2.coord)

                        if neighbour in fringe_contents:  # update f_score of neighbour in fringe
                            fringe_contents[neighbour][2] = False
                        fringe_contents[neighbour] = [f_score, entry_index, True, neighbour]
                        fringe.put(fringe_contents[neighbour])
                        entry_index -= 1

        raise PathNotFound

    def _reconstruct_path(self, prev_legs: dict[ChargeStation, _Leg], end: ChargeStation) -> list[_Leg]:
        """Returns a list of legs leading from the start charge station in prev_edges to end."""
        if end not in prev_legs:
            return []
        else:
            return self._reconstruct_path(prev_legs, prev_legs[end].get_other_endpoint(end)) + [prev_legs[end]]

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
            _Leg(
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
