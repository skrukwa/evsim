"""
Get an updated path by making a googlemaps call.
Simulate charging on that path.
"""
from dataclasses import dataclass
from typing import Optional, Callable, Any

import googlemaps

from classes.charge_station import ChargeStation
from classes.leg import Leg


@dataclass
class ChargeStationInfo:
    """
    A dataclass containing the charging and driving info for a given charge station and leg in a path.

    Instance Attributes:
        - driving_distance: road distance from the corresponding charge station to the next in the path in meters
        - driving_time: time spent driving from the corresponding charge station to the next in the path in seconds
        - charge_time: time spent charging at the corresponding charge station in seconds
        - battery_start: battery level when arriving to the corresponding charge station (0 < x < 1)
        - battery_end: battery level when leaving to the corresponding charge station (0 < x < 1)
    """
    driving_distance: int
    driving_time: int
    charge_time: Optional[int] = None
    battery_start: Optional[float] = None
    battery_end: Optional[float] = None


def get_path_info(path: list[Leg],
                  start: ChargeStation,
                  gmaps: googlemaps.client.Client) -> tuple[list[ChargeStationInfo], str, dict[str, dict[str, float]]]:
    """
    Creates a list of ChargeStationInfo objects for each charge station beginning a leg in path
    by making a call to the given googlemaps client.

    Returns the list of ChargeStationInfo objects, a polyline string of the path, and the coordinate bounds of the path.

    Note that since a new call is made, driving_distance and driving_time could deviate from what they are in path.

    Preconditions:
        - path
    """
    charge_stations = [start]
    for leg in path:
        charge_stations.append(leg.endpoints.difference({charge_stations[-1]}).pop())  # find the next endpoint

    response = gmaps.directions(charge_stations[0].coord,
                                charge_stations[-1].coord,
                                waypoints=[cs.coord for cs in charge_stations[1:-1]],
                                optimize_waypoints=False)

    poly_overview = response[0]['overview_polyline']['points']
    bounds = response[0]['bounds']

    info = []

    for leg in response[0]['legs']:
        info.append(
            ChargeStationInfo(leg['distance']['value'], leg['duration']['value'])
        )

    return info, poly_overview, bounds


def simulate_path_charging(ev_range: float,
                           min_battery: float,
                           start_battery: float,
                           charge_curve: Callable,
                           info: list[ChargeStationInfo]) -> float:
    """
    Mutates info by updating charge_time, battery_start, and battery_end with respect to min_battery.

    Returns destination start battery (0 < x < 1).

    Note that since driving_distance and driving_time could have deviated from the original network,
    it may be required to charge OVER 1.00 to make it to the next charge station with respect to min_battery.
    """
    ev_range *= 1000

    for i, csi in enumerate(info):
        if i == 0:
            csi.battery_start = start_battery
        else:
            csi.battery_start = info[i - 1].battery_end - info[i - 1].driving_distance / ev_range

        charge_needed = min_battery + csi.driving_distance / ev_range
        if charge_needed > csi.battery_start:
            csi.battery_end = charge_needed
            csi.charge_time = charge_curve(charge_needed) - charge_curve(csi.battery_start)
        else:
            csi.battery_end = csi.battery_start
            csi.charge_time = 0

        if i == len(info) - 1:
            return csi.battery_end - csi.driving_distance / ev_range


def prepare_json_summary(path: list[Leg],
                         start: ChargeStation,
                         info: list[ChargeStationInfo],
                         polyline: str,
                         bounds: dict[str, dict[str, float]],
                         dest_start_battery: float,
                         request_data: dict[str, Any]) -> dict:
    """Returns a JSON compatible dict containing a detailed summary of the path."""
    charge_stations = [start]
    for leg in path:
        charge_stations.append(leg.endpoints.difference({charge_stations[-1]}).pop())  # find the next endpoint

    assert len(info) == len(charge_stations) - 1

    total_driving_distance = sum(csi.driving_distance for csi in info)
    total_driving_time = sum(csi.driving_time for csi in info)
    total_charge_time = sum(csi.charge_time for csi in info)
    total_time = total_driving_time + total_charge_time
    path_summary = {
        'total_driving_distance': _format_meters(total_driving_distance),
        'total_driving_time': _format_seconds(total_driving_time),
        'total_charge_time': _format_seconds(total_charge_time),
        'total_time': _format_seconds(total_time)
    }

    legs_summary = []
    for cs, csi in zip(charge_stations, info):
        legs_summary.append({
            'charge_station': cs.formatted_dict,
            'driving_distance': _format_meters(csi.driving_distance),
            'driving_time': _format_seconds(csi.driving_time),
            'charge_time': _format_seconds(csi.charge_time),
            'battery_start': _format_battery_float(csi.battery_start),
            'battery_end': _format_battery_float(csi.battery_end),
        })

    destination_summary = {
        'charge_station': charge_stations[-1].formatted_dict,
        'dest_start_battery': _format_battery_float(dest_start_battery)
    }

    result = {
        'polyline': polyline,
        'bounds': bounds,
        'path_summary': path_summary,
        'legs_summary': legs_summary,
        'destination_summary': destination_summary,
        'request_data': request_data
    }
    return result


def _format_seconds(seconds: float) -> str:
    """
    Returns a string of the following format.

    [x hrs y mins z secs] if seconds >= 60**2
    or
    [x mins y secs] otherwise
    """
    if seconds >= 60 ** 2:
        return f'{seconds // 60 ** 2:.0f} hrs {seconds % 60 ** 2 // 60:.0f} mins {seconds % 60 ** 2 % 60:.0f} secs'
    else:  # seconds < 60**2
        return f'{seconds // 60:.0f} mins {seconds % 60:.0f} secs'


def _format_meters(meters: float) -> str:
    """Returns a formatted string."""
    return f'{meters / 1000:,.1f} kms'


def _format_battery_float(value: float) -> str:
    """Returns a formatted string."""
    return f'{value:.1%}'
