"""
Visualize ChargeNetwork objects (including those just representing a path) and cluster trees.
"""
import datetime
import io

import plotly.graph_objects as go

from classes.charge_network import ChargeNetwork
from classes.charge_station import ChargeStation
from classes.leg import Leg


def graph_network(network: ChargeNetwork, display_result: bool = False) -> str:
    """
    Creates a visualization of the charge stations and legs in the given charge network on a map.

    Every charge station is graphed on the same layer (trace) and has the same color.
    Every leg is graphed on the same layer (trace) and has the same color.

    Returns a html string of the plotly graph.
    """
    fig = go.Figure()

    marker_lats = []
    marker_lngs = []
    marker_names = []
    line_lats = []
    line_lngs = []
    edges_seen = {}

    for cs in network.charge_stations():
        marker_names.append(cs.name)
        marker_lats.append(cs.lat)
        marker_lngs.append(cs.lng)

        legs = network.charge_station_legs(cs)
        for leg in legs:
            if leg not in edges_seen:
                endpoints_iter = iter(leg.endpoints)
                cs1 = next(endpoints_iter).coord
                cs2 = next(endpoints_iter).coord
                line_lats.append(cs1[0])
                line_lats.append(cs2[0])
                line_lats.append(None)
                line_lngs.append(cs1[1])
                line_lngs.append(cs2[1])
                line_lngs.append(None)

    fig.add_trace(
        go.Scattergeo(
            lat=marker_lats,
            lon=marker_lngs,
            text=marker_names,
            hoverinfo='all',
            mode='markers'
        )
    )

    fig.add_trace(
        go.Scattergeo(
            lat=line_lats,
            lon=line_lngs,
            mode='lines',
            line=dict(width=0.2 if len(line_lats) > 100 else 1)
        )
    )

    fig.update_geos(
        scope='north america',
        resolution=50,
        lakecolor='#818a99',
        showcountries=False,
        showocean=True,
        oceancolor='#818a99'
    )

    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False
    )

    if display_result:
        fig.show()

    buffer = io.StringIO()
    fig.write_html(buffer)
    return buffer.getvalue()


def graph_clusters(clusters: list[list[ChargeStation]], display_result: bool = False) -> str:
    """
    Creates a visualization of the charge station clusters where each inner list represents 1 cluster.

    Every cluster is graphed on a different layer (trace) and (in general) has the different color.

    Note, some colors may be duplicates, but the trace number can be confirmed by mouse hover.

    Returns a html string of the plotly graph.
    """

    fig = go.Figure()

    for cluster in clusters:
        lats = []
        lngs = []
        names = []
        for cs in cluster:
            lats.append(cs.lat)
            lngs.append(cs.lng)
            names.append(cs.name)

        fig.add_trace(
            go.Scattergeo(
                lat=lats,
                lon=lngs,
                text=names,
                hoverinfo='all',
                mode='markers'
            )
        )

    fig.update_geos(
        scope='north america',
        resolution=50,
        lakecolor='#818a99',
        showcountries=False,
        showocean=True,
        oceancolor='#818a99'
    )

    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False
    )

    if display_result:
        fig.show()

    buffer = io.StringIO()
    fig.write_html(buffer)
    return buffer.getvalue()


def graph_path(path: list[Leg], display_result: bool = False) -> str:
    """
    Creates a visualization of a path by creating a temporary ChargeNetwork object and graphing it.

    Returns a html string of the plotly graph.
    """
    temp_net = ChargeNetwork(-1, -1)
    temp_net.add_charge_station(ChargeStation('', '', '', '', 0, 0, datetime.date(2000, 1, 1)), set(path))

    charge_stations = set.union(*(leg.endpoints for leg in path))
    for cs in charge_stations:
        temp_net.add_charge_station(cs)

    return graph_network(temp_net, display_result)
