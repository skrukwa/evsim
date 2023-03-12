"""
Specifies the Car dataclass,
ChargeStation (ADT graph vertex) dataclass,
Path (ADT graph edge) dataclass,
and ChargeNetwork (ADT graph) class.
"""
from dataclasses import dataclass
from typing import Callable
import datetime


@dataclass(frozen=True)
class Car:
    """A dataclass representing a car make and model.
    This dataclass in immutable so that it is not mutated after being passed to ChargeNetwork,
    which initializes itself based on Car properties.

    Instance Attributes:
      - make: the make of the car
      - model: the model of the car
      - charge_time_func: a (possibly anonymous) function which can take two number inputs x and y where
                          x represents the starting battery percentage (0 <= x <= 1) and
                          y represents the ending battery percentage (0 <= x <= 1) and
                          x <= y which returns the number of seconds the car will take to charge

    >>> m3 = Car('Apache Automotive',
    ...          'EV Linear Charger',
    ...          lambda start, end: (100 * end) ** 2 - (100 * start) ** 2)
    """
    make: str
    model: str
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
class Path:
    """A dataclass representing a path from one charge station to another.
    This dataclass is used as edges in the ChargeNetwork class.
    Also, while trip direction matters here, this is only to keep polyline
    in the correct order. road_distance and time can be treated as reversible.

    Instance Attributes:
      - start: the start ChargeStation
      - end: the end ChargeStation
      - road_distance: the driving distance between start and end
      - time: the driving time between start and end
      - polyline: ordered coordinates forming the polyline of the driving route between start and end
    """
    start: ChargeStation
    end: ChargeStation
    road_distance: str
    time: str
    polyline: list[tuple]


class ChargeNetwork:
    """A graph ADT representing a charge network for a SPECIFIC car range.
    A path from one ChargeStation to another will not be considered if its
    road length is longer than car_range.

    Instance Attributes:
      - car: the car this graph is based off of

    Representation Invariants:
      - every Path in _graph contains the ChargeStation of its key as Path.start or Path.end
      - in each _graph value set, there are NOT two Paths where (Path1.start = Path2.end and Path1.end = Path2.start)
    """
    # Private Instance Attributes:
    #   - _graph: a dict of ChargeStations and corresponding set of paths
    _car: Car
    _graph: dict[ChargeStation, set[Path]]

    def __init__(self, car) -> None:
        """Initialize an empty graph."""
        self._car = car
        self._graph = {}

    @property
    def car(self):
        """An immutable getter for self._car."""
        return self._car
