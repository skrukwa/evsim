"""
----------Objectives----------
Visualize ChargeNetwork objects (including those just representing a path), cluster trees, and polyline data.
"""
import datetime
import io

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from classes import ChargeStation, _Edge, ChargeNetwork
from polylines import PolylinePoint


def graph_network(network: ChargeNetwork, display_result: bool = False) -> str:
    """
    Creates a visualization of the charge stations and edges in the given charge network on a map.

    Every charge station is graphed on the same layer (trace) and has the same color.
    Every edge is graphed on the same layer (trace) and has the same color.

    Returns a html string of the plotly graph.
    """
    fig = go.Figure()

    marker_latitudes = []
    marker_longitudes = []
    marker_names = []
    line_latitudes = []
    line_longitudes = []
    edges_seen = {}

    for charger in network.charge_stations():
        marker_names.append(charger.name)
        marker_latitudes.append(charger.latitude)
        marker_longitudes.append(charger.longitude)

        edges = network.corresponding_edges(charger)
        for edge in edges:
            if edge not in edges_seen:
                endpoints_iter = iter(edge.endpoints)
                p1 = next(endpoints_iter).coord
                p2 = next(endpoints_iter).coord
                line_latitudes.append(p1[0])
                line_latitudes.append(p2[0])
                line_latitudes.append(None)
                line_longitudes.append(p1[1])
                line_longitudes.append(p2[1])
                line_longitudes.append(None)

    fig.add_trace(
        go.Scattergeo(
            lat=marker_latitudes,
            lon=marker_longitudes,
            text=marker_names,
            hoverinfo='all',
            mode='markers'
        )
    )

    fig.add_trace(
        go.Scattergeo(
            lat=line_latitudes,
            lon=line_longitudes,
            mode='lines',
            line=dict(width=0.2 if len(line_latitudes) > 100 else 1)
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
        latitudes = []
        longitudes = []
        names = []
        for charger in cluster:
            latitudes.append(charger.latitude)
            longitudes.append(charger.longitude)
            names.append(charger.name)

        fig.add_trace(
            go.Scattergeo(
                lat=latitudes,
                lon=longitudes,
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


def graph_path(path: list[_Edge], display_result: bool = False) -> str:
    """
    Creates a visualization of a path by creating a temporary ChargeNetwork object and graphing it.

    Returns a html string of the plotly graph.
    """
    temp_graph = ChargeNetwork(-1, -1)
    temp_graph.add_charge_station(ChargeStation('', '', '', '', 0, 0, datetime.date(2000, 1, 1)), set(path))

    all_chargers = set.union(*(edge.endpoints for edge in path))
    for charger in all_chargers:
        temp_graph.add_charge_station(charger, set())

    return graph_network(temp_graph, display_result)


def graph_polyline_data(polyline: list[list[PolylinePoint]], display_result: bool = False) -> str:
    """
    Creates a line plot of total_distance and battery_level over time.

    Returns a html string of the plotly graph.
    """
    time = []
    total_distance = []
    battery_level = []
    for l in polyline:
        for point in l:
            time.append((point.total_charge_time + point.total_driving_time) / 60 / 60)
            total_distance.append(point.total_distance / 1000)
            battery_level.append(point.battery_level * 100)

    fig = make_subplots(specs=[[{'secondary_y': True}]])

    fig.add_trace(
        go.Scatter(x=time, y=total_distance, name=None, mode='lines'),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(x=time, y=battery_level, mode='lines'),
        secondary_y=True,
    )

    fig.update_layout(showlegend=False)
    fig.update_xaxes(title_text='time (hrs)')
    fig.update_yaxes(title_text='total distance (km)', secondary_y=False)
    fig.update_yaxes(title_text='battery level (%)', secondary_y=True)

    if display_result:
        fig.show()

    buffer = io.StringIO()
    fig.write_html(buffer)
    return buffer.getvalue()
