"""The classes.py module of the ev-trip-sim project.
https://github.com/skrukwa/ev-trip-sim

Description
===========

This module specifies the following:
  - Car dataclass
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
from dataclasses import dataclass
from typing import Callable, Iterable, Optional
import datetime


@dataclass(frozen=True)
class Car:
    """A dataclass representing a car make and model.
    This dataclass in immutable so that it is not mutated after being passed to ChargeNetwork,
    which initializes itself based on Car properties (specifically range).

    Instance Attributes:
        - make: the make of the car
        - model: the model of the car
        - range: the full range of the car in kilometers
        - charge_time_func: a (possibly anonymous) function which can take two number inputs x and y where
                            x represents the starting battery percentage (0 <= x <= 1) and
                            y represents the ending battery percentage (0 <= x <= 1) and
                            x <= y which returns the number of seconds the car will take to charge

    >>> m3 = Car('Apache Automotive',
    ...          'EV Linear Charger',
    ...          250,
    ...          lambda start, end: (100 * end) ** 2 - (100 * start) ** 2)
    """
    make: str
    model: str
    range: int
    charge_time_func: Callable[[float, float], float]


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
    def coord(self):
        return self.latitude, self.longitude


class _Edge:
    """A dataclass representing an edge (driving route) from one charge station to another.

    Instance Attributes:
        - endpoints: the start and end charge stations of this edge
        - road_distance: the driving distance between endpoints in kilometers
        - time: the driving time between endpoints in seconds

    Representation Invariants:
    - len(self.endpoints) == 2
    """
    endpoints: set[ChargeStation]
    road_distance: float
    time: int

    def __int__(self, charger1: ChargeStation, charger2: ChargeStation, road_distance: float, time: int):
        self.endpoints = {charger1, charger2}
        self.road_distance = road_distance
        self.time = time

    def get_other_endpoint(self, charger: ChargeStation) -> ChargeStation:
        """Return the endpoint of this edge that is not equal to the given charge station.

        Preconditions:
            - charger in self.endpoints
        """
        return (self.endpoints - {charger}).pop()


class ChargeNetwork:
    """A graph ADT representing a charge network for a SPECIFIC car.

    An edge from one ChargeStation to another will not be considered (in the graph) if its
    road_distance is longer than self.car.range.

    Note, if a charge station in this graph has its set of edges as None (as opposed to an empty set),
    it denotes that the edges have not yet been initialized.

    Instance Attributes:
        - car: the car this graph is based off of (immutable)
        - min_chargers_at_station: the min sum of type 2 and type DC chargers at each
                                   charge station in this graph (immutable)

    Representation Invariants:
        - all(all(charger in edge for edge in edge_set) for charger, edge_set in _graph.items())
    """
    # Private Instance Attributes:
    #   - _graph: a dict of charge stations and corresponding edges
    _car: Car
    _min_chargers_at_station: int
    _graph: dict[ChargeStation, Optional[set[_Edge]]]

    def __init__(self, min_chargers_at_station, car) -> None:
        """Initialize an empty graph."""
        self._min_chargers_at_station = min_chargers_at_station
        self._car = car
        self._graph = {}

    @property
    def min_chargers_at_station(self) -> int:
        """An immutable getter for self._car."""
        return self._min_chargers_at_station

    @property
    def car(self) -> Car:
        """An immutable getter for self._car."""
        return self._car

    def is_empty(self) -> bool:
        """Returns whether this graph is empty."""
        return not self._graph

    def charge_stations(self) -> set[ChargeStation]:
        """Returns a set of charge stations in the charge network."""
        return set(self._graph.keys())

    def add_charge_station(self, station: ChargeStation, edges: Optional[set[_Edge]] = None) -> None:
        """Adds a charge station (and optionally a corresponding set of edges) to the graph.

        Preconditions:
            - station not in self._graph
         """
        self._graph[station] = edges
