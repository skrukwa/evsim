from classes import ChargeNetwork
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
