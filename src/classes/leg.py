"""
Defines the Leg class.
"""
from typing import Optional, Self

from classes.charge_station import ChargeStation


class Leg:
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

        Allows Leg objects to be stored in sets.
        """
        coords = [cs.coord for cs in self.endpoints]
        coords.sort()
        return hash((self.__class__, coords[0], coords[1]))
