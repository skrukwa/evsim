"""The visuals.py module of the ev-trip-sim project.
https://github.com/skrukwa/ev-trip-sim

Description
===========

This module is responsible for various visualization functions.

Copyright and Usage Information
===============================

This file is distributed under the ev-trip-sim project which is
bounded by the terms of Apache License Version 2.0. For more
information, please follow the github link above.

This file is Copyright (c) Evan Skrukwa and Nadim Mottu.
"""
from classes import ChargeNetwork, ChargeStation
import plotly.graph_objects as go


def graph_network(network: ChargeNetwork) -> None:
    """Creates a visualization of the charge stations in the given charge network on a map.

    Every charge station is graphed on the same layer (trace) and has the same color.
    """

    latitudes = []
    longitudes = []
    names = []
    for charger in network.charge_stations():
        names.append(charger.name)
        latitudes.append(charger.latitude)
        longitudes.append(charger.longitude)

    fig = go.Figure(
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

    fig.show()


def graph_clusters(clusters: list[list[ChargeStation]]) -> None:
    """Creates a visualization of the charge station clusters where each inner list represents 1 cluster.

    Every cluster is graphed on a different layer (trace) and (in general) has the different color.

    Note, some colors may be duplicates, but the trace number can be confirmed by mouse hover.
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

    fig.show()
