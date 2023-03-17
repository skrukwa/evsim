"""The classes.py module of the ev-trip-sim project.
https://github.com/skrukwa/ev-trip-sim

Description
===========

This module specifies the following:
  - Car dataclass
  - ChargeStation (ADT graph vertex) dataclass
  - _Path (ADT graph edge) dataclass
  - ChargeNetwork (ADT graph) class

Copyright and Usage Information
===============================

This file is distributed under the ev-trip-sim project which is
bounded by the terms of Apache License Version 2.0. For more
information, please follow the github link above.

This file is Copyright (c) Evan Skrukwa and Nadim Mottu.
"""
from __future__ import annotations
import csv
from dataclasses import dataclass
from typing import Callable
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


@dataclass
class _Path:
    """A dataclass representing a path from one charge station to another.
    This dataclass is used as edges in the ChargeNetwork class.
    Also, while trip direction matters here, this is only to keep polyline
    in the correct order. road_distance and time can be treated as reversible.

    Instance Attributes:
        - start: the start ChargeStation
        - end: the end ChargeStation
        - road_distance: the driving distance between start and end in kilometers
        - time: the driving time between start and end in seconds
        - polyline: ordered coordinates forming the polyline of the driving route between start and end
    """
    start: ChargeStation
    end: ChargeStation
    road_distance: str
    time: str
    polyline: list[tuple]


class ChargeNetwork:
    """A graph ADT representing a charge network for a SPECIFIC car.
    A path from one ChargeStation to another will not be considered (in the graph) if its
    road_distance is longer than self.car.range. Furthermore, if a ChargeStation in the
    graph has paths as None (as opposed to an empty set), it denotes that the edges have
    not yet been initialized.

    Instance Attributes:
        - car: the car this graph is based off of (immutable)

    Representation Invariants:
        - every _Path in _graph contains the ChargeStation of its key as path.start or path.end
        - in each _graph value set, there are NOT two _Paths where (path1.start = path2.end and path1.end = path2.start)
    """
    # Private Instance Attributes:
    #   - _graph: a dict of ChargeStations and corresponding set of paths
    _car: Car
    _graph: dict[ChargeStation, set[_Path] | None]

    def __init__(self, car) -> None:
        """Initialize an empty graph."""
        self._car = car
        self._graph = {}

    @property
    def car(self):
        """An immutable getter for self._car."""
        return self._car

    def is_empty(self) -> bool:
        """Return whether this ChargeNetwork object is empty."""
        return self._graph == {}

    def add_charge_station(self, station: ChargeStation, paths: set[_Path] | None):
        """Adds a charge station and corresponding set of paths to the graph.

        Preconditions:
            - station not in self._graph
         """
        self._graph[station] = paths
