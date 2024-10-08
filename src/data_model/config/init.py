"""
Initializes all tables in the database as needed.
"""
from data_model.places_api import init_places_api_table


def init_db() -> None:
    """
    Initializes all tables in database as needed.

    Can only be called within an application context.
    """
    init_places_api_table()
