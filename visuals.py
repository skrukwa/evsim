from classes import ChargeNetwork
import plotly.graph_objects as go


def temp_basic_map(network: ChargeNetwork) -> None:
    """graphs the charge stations in the given charge network on a map"""

    # this is completely fucked

    names = []
    addrs = []
    hours = []
    lats = []
    lons = []
    dates = []
    for charger in network._graph:
        names.append(charger.name)
        addrs.append(charger.address)
        hours.append(charger.hours)
        lats.append(charger.latitude)
        lons.append(charger.longitude)
        dates.append(charger.open_date)

    fig = go.Figure(
        data=go.Scattergeo(
            lon=lons,
            lat=lats,
            text=names,
            hoverinfo='all',
            mode='markers'
        )
    )

    fig.update_layout(
        geo=dict(
            scope='north america',
            showland=True,
            landcolor="rgb(212, 212, 212)",
            subunitcolor="rgb(255, 255, 255)",
            countrycolor="rgb(255, 255, 255)",
            showlakes=True,
            lakecolor="rgb(255, 255, 255)",
            showsubunits=True,
            showcountries=True,
            resolution=50,
            projection=dict(
                type='conic conformal',
                rotation_lon=-100
            ),
            lonaxis=dict(
                showgrid=True,
                gridwidth=0.5,
                range=[-140.0, -55.0],
                dtick=5
            ),
            lataxis=dict(
                showgrid=True,
                gridwidth=0.5,
                range=[20.0, 60.0],
                dtick=5
            )
        )
    )

    fig.show()
