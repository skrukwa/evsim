"""
----------Objectives----------
Define a custom class for each coord in a polyline.
Create lists of PolylinePoint objects to represent legs of a path.
"""
from dataclasses import dataclass
from typing import Optional, Callable

import googlemaps

from classes import ChargeStation, _Edge


@dataclass
class PolylinePoint:
    """
    A dataclass representing a coordinate in a polyline.

    Instance Attributes:
        - coord: the station's coordinate in the order (lat, lon)
        - total_distance: total distance traveled in meters
        - total_driving_time: total time spent driving in seconds
        - total_charge_time: total time spent charging in seconds
        - battery_level: current battery level of the vehicle at this point
          (calculated based on total_distance)
    """
    coord: tuple[float, float]
    total_distance: int
    total_driving_time: int
    total_charge_time: Optional[float] = None
    battery_level: Optional[float] = None


def get_polyline_legs(path: list[_Edge],
                      start: ChargeStation,
                      gmaps: googlemaps.client.Client) -> list[list[PolylinePoint]]:
    """
    Creates a list of PolylinePoint objects for each leg in the given path by
    making a call to the given googlemaps client.

    Note that since a new call is being made, leg lengths could deviate from what they are in path.

    These PolylinePoint objects contain the coordinates that will make up the polyline,
    as well as updated distance and travel time values according to the call made.

    For two consecutive legs, the last PolylinePoint object of the last leg will have the same
    coord, total_distance, and total_driving_time as the first PolylinePoint object of the next leg.

    Note that the polyline will be low resolution because it uses the same coordinates as 'overview_polyline'
    since the python googlemaps library does not return 'path' under each of the 'steps'.

    Preconditions:
        - path
    """
    chargers = [start]
    for edge in path:
        chargers.append(edge.endpoints.difference({chargers[-1]}).pop())  # find the next endpoint

    response = gmaps.directions(chargers[0].coord,
                                chargers[-1].coord,
                                waypoints=[cs.coord for cs in chargers[1:-1]],
                                optimize_waypoints=False)

    path_polyline = []
    for leg in response[0]['legs']:
        steps = leg['steps']

        if not path_polyline:
            init_leg_coord = (steps[0]['start_location']['lat'], steps[0]['start_location']['lng'])
            init_leg_distance = 0
            init_leg_driving_time = 0
        else:  # use same values as last PolylinePoint object
            init_leg_coord = path_polyline[-1][-1].coord
            init_leg_distance = path_polyline[-1][-1].total_distance
            init_leg_driving_time = path_polyline[-1][-1].total_driving_time

        leg_polyline = [
            PolylinePoint(coord=init_leg_coord,
                          total_distance=init_leg_distance,
                          total_driving_time=init_leg_driving_time)
        ]

        for step in steps:
            leg_polyline.append(
                PolylinePoint(coord=(step['end_location']['lat'], step['end_location']['lng']),
                              total_distance=leg_polyline[-1].total_distance + step['distance']['value'],
                              total_driving_time=leg_polyline[-1].total_driving_time + step['duration']['value'])
            )

        path_polyline.append(leg_polyline)

    return path_polyline


def get_polyline_with_charging(polyline: list[list[PolylinePoint]],
                               ev_range: float,
                               min_battery: float,
                               start_battery: float,
                               charge_curve: Callable) -> list[list[PolylinePoint]]:
    """
    Returns a polyline where every even index is a charge period (which may be empty if charging was not needed)
    and every odd index is a leg (consisting of the same PolylinePoint objects in the original polyline) whose
    PolylinePoint objects have been mutated to have simulated total_charge_time and battery_level attributes.

    Charges least possible with respect to min_battery to maximise charge speed.

    Note that in extreme cases, battery may need to be charged OVER 100%
    due to deviations in polyline from the API call in get_polyline_legs.

    The original polyline object will be mutated in the process.

    Preconditions:
        - charge_curve gives time in seconds to charge from 0.00 to x <= 1
    """
    polyline_with_charging = []

    for index, leg in enumerate(polyline):

        # STEP 1. append charge period to polyline_with_charging

        if index == 0:
            last_total_charge_time = 0
            last_battery_level = start_battery
        else:
            last_leg = polyline[index - 1]
            last_total_charge_time = last_leg[-1].total_charge_time
            last_battery_level = last_leg[-1].battery_level

        charge_period = _get_charge_period(
            next_leg=leg,
            ev_range=ev_range,
            min_battery=min_battery,
            last_total_charge_time=last_total_charge_time,
            last_battery_level=last_battery_level,
            charge_curve=charge_curve
        )

        polyline_with_charging.append(charge_period)

        # STEP 2. update leg and append to polyline_with_charging

        if charge_period:
            last_total_charge_time = charge_period[-1].total_charge_time
            last_battery_level = charge_period[-1].battery_level

        _update_leg_charging(
            leg=leg,
            ev_range=ev_range,
            last_total_charge_time=last_total_charge_time,
            last_battery_level=last_battery_level
        )
        polyline_with_charging.append(leg)

    return polyline_with_charging


def _get_charge_period(next_leg: list[PolylinePoint],
                       ev_range: float,
                       min_battery: float,
                       last_total_charge_time: float,
                       last_battery_level: float,
                       charge_curve: Callable) -> list[PolylinePoint]:
    """
    Returns a charge period where the car is charged enough to complete next_leg with min_battery remaining.

    This is a list of new PolylinePoint objects which update total_charge_time and battery level
    for every percentage charged, or an empty list if no additional charge for the leg is needed.
    """
    charge_period = []

    total_leg_distance = next_leg[-1].total_distance - next_leg[0].total_distance
    total_charge_needed = total_leg_distance / (ev_range * 1000) + min_battery

    if total_charge_needed > last_battery_level:

        # add initial PolylinePoint
        charge_period = [
            PolylinePoint(
                coord=next_leg[0].coord,
                total_distance=next_leg[0].total_distance,
                total_driving_time=next_leg[0].total_driving_time,
                total_charge_time=last_total_charge_time,
                battery_level=last_battery_level
            )
        ]

        # add PolylinePoint for every percentage charged
        while charge_period[-1].battery_level + 0.01 < total_charge_needed:
            charge_period.append(
                PolylinePoint(
                    coord=next_leg[0].coord,
                    total_distance=next_leg[0].total_distance,
                    total_driving_time=next_leg[0].total_driving_time,
                    total_charge_time=
                    charge_period[-1].total_charge_time +
                    charge_curve(charge_period[-1].battery_level + 0.01) -
                    charge_curve(charge_period[-1].battery_level),
                    battery_level=charge_period[-1].battery_level + 0.01
                )
            )

        # add final PolylinePoint
        last_charge_needed = total_charge_needed - charge_period[-1].battery_level
        charge_period.append(
            PolylinePoint(
                coord=next_leg[0].coord,
                total_distance=next_leg[0].total_distance,
                total_driving_time=next_leg[0].total_driving_time,
                total_charge_time=
                charge_period[-1].total_charge_time +
                charge_curve(charge_period[-1].battery_level + last_charge_needed) -
                charge_curve(charge_period[-1].battery_level),
                battery_level=charge_period[-1].battery_level + last_charge_needed
            )
        )

    return charge_period


def _update_leg_charging(leg: list[PolylinePoint],
                         ev_range: float,
                         last_total_charge_time: float,
                         last_battery_level: float) -> None:
    """
    Mutates each PolylinePoint in leg by simulating total_charge_time and battery_level attributes
    """
    for index, point in enumerate(leg):
        if index == 0:
            point.total_charge_time = last_total_charge_time
            point.battery_level = last_battery_level
        else:
            prev_point = leg[index - 1]
            point.total_charge_time = prev_point.total_charge_time
            point.battery_level = \
                prev_point.battery_level - (point.total_distance - prev_point.total_distance) / (ev_range * 1000)


def get_json_ready(path: list[_Edge], start: ChargeStation, polyline_with_charging: list[list[PolylinePoint]]) -> dict:
    """
    Takes the polyline returned from get_polyline_with_charging where
        - every even index is a charge period (which may be empty if charging was not needed)
        - every odd index is a leg

    Returns a JSON ready dict containing a detailed summary of the path.
    """
    legs_summary = []

    chargers = [start]
    for edge in path:
        chargers.append(edge.endpoints.difference({chargers[-1]}).pop())  # find the next endpoint

    assert len(chargers) - 1 == len(polyline_with_charging) / 2

    for charge_station, charge_period, next_leg in zip(
            chargers, polyline_with_charging[::2], polyline_with_charging[1::2]
    ):
        legs_summary.append({
            "charge_station": charge_station.dict,
            "polyline": [point.coord for point in next_leg],
            "charge_time": _format_seconds(
                charge_period[-1].total_charge_time - charge_period[0].total_charge_time if charge_period else 0
            ),
            "battery_start": _format_battery_float(
                charge_period[0].battery_level if charge_period else next_leg[0].battery_level
            ),
            "battery_end": _format_battery_float(
                next_leg[0].battery_level
            ),
            "drive_time": _format_seconds(
                next_leg[-1].total_driving_time - next_leg[0].total_driving_time
            ),
            "drive_distance": _format_meters(
                next_leg[-1].total_distance - next_leg[0].total_distance
            )
        })

    destination_summary = {
        "charge_station": chargers[-1].dict,
        "battery_end": _format_battery_float(
            polyline_with_charging[-1][-1].battery_level
        ),
        "total_time": _format_seconds(
            polyline_with_charging[-1][-1].total_driving_time + polyline_with_charging[-1][-1].total_charge_time
        ),
        "total_driving_time": _format_seconds(
            polyline_with_charging[-1][-1].total_driving_time
        ),
        "total_charge_time": _format_seconds(
            polyline_with_charging[-1][-1].total_charge_time
        ),
        "total_distance": _format_meters(
            polyline_with_charging[-1][-1].total_distance
        )
    }

    result = {"legs_summary": legs_summary,
              "destination_summary": destination_summary}

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
    """
    Returns a formatted string.
    """
    return f'{meters / 1000:,.1f} kms'


def _format_battery_float(value: float) -> str:
    """
    Returns a formatted string.
    """
    return f'{value:.1%}'
