"""
Defines the ChargeStation class.
"""
import datetime
from dataclasses import dataclass
from typing import Optional


@dataclass(eq=False)
class ChargeStation:
    """
    A dataclass representing a charger station.

    This dataclasses objects are used as vertices in the ChargeNetwork class.

    This dataclass is immutable and falls back to id based hashing and equality checking (due to the eq=False argument).

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
