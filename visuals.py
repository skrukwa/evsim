from classes import ChargeNetwork, ChargeStation
import plotly.graph_objects as go


def temp_basic_map(network: ChargeNetwork) -> None:
    """graphs the charge stations in the given charge network on a map"""
    # this is purly for testing right now

    names = []
    lats = []
    lons = []
    for charger in network._graph:
        names.append(charger.name)
        lats.append(charger.latitude)
        lons.append(charger.longitude)

    fig = go.Figure(
        go.Scattergeo(
            lon=lons,
            lat=lats,
            text=names,
            hoverinfo='all',
            mode='markers'
        )
    )

    fig.update_geos(
        scope='north america',
        resolution=50,
        showcountries=False
    )

    fig.show()


def temp_cluster_map(clusters: list[list[ChargeStation]]) -> None:
    """ok"""
    fig = go.Figure()

    for cluster in clusters:
        lons = []
        lats = []
        names = []
        for charger in cluster:
            lons.append(charger.longitude)
            lats.append(charger.latitude)
            names.append(charger.name)

        fig.add_trace(
            go.Scattergeo(
                lon=lons,
                lat=lats,
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
