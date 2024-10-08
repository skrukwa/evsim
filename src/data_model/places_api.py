"""
Defines functionality using the places_api table.
"""
from datetime import timedelta
from time import time

from werkzeug.local import LocalProxy

from data_model.config.con import get_con
from data_model.config.limits import PLACES_API_TOKEN_AGE_LIMIT, PLACES_API_DAILY_SESSION_LIMIT

con = LocalProxy(get_con)

TYPE_AUTO_COMPLETE = 'autocomplete'
TYPE_DETAILS = 'details'


def init_places_api_table() -> None:
    """
    Initialize places_api table in database as needed.
    """
    with con:
        con.execute(f"""
            CREATE TABLE IF NOT EXISTS places_api (
                uuid4_token     TEXT    NOT NULL,
                unix_time       NUMERIC NOT NULL,
                type            TEXT    NOT NULL CHECK (type IN ('{TYPE_AUTO_COMPLETE}', '{TYPE_DETAILS}')),
                PRIMARY KEY (uuid4_token, unix_time)
            )
        """)


def can_make_places_api_req(token: str) -> bool:
    """
    Returns if a Places API request with the following token can be made based on the following logic.
        - total session count in the past 24 hours is less than PLACES_API_DAILY_SESSION_LIMIT
        - the token corresponds to an active session or the token is a new token
    """
    with con:

        # check number of requests made on this unix day
        cur = con.execute("""
            SELECT COUNT(*)
            FROM (
                SELECT uuid4_token
                FROM places_api
                GROUP BY uuid4_token
                HAVING MIN(unix_time) > ?
            )
        """, (time() - time() % timedelta(days=1).total_seconds(),))
        if cur.fetchone()[0] >= PLACES_API_DAILY_SESSION_LIMIT:
            return False

        # check session expired (already made a place details request)
        cur = con.execute("""
            SELECT *
            FROM places_api
            WHERE uuid4_token = ? AND type = 'details'
        """, (token,))
        if cur.fetchall():
            return False

        # check session expired (too old)
        cur = con.execute("""
            SELECT *
            FROM places_api
            WHERE uuid4_token = ? AND unix_time < ?
        """, (token, time() - PLACES_API_TOKEN_AGE_LIMIT.total_seconds()))
        if cur.fetchall():
            return False

    return True


def insert_places_api_req(token: str, type: str) -> None:
    """
    Inserts a Places API request with the given token and type.
    """
    with con:
        con.execute("""
            INSERT INTO places_api (uuid4_token, unix_time, type)
            VALUES (?, ?, ?)
        """, (token, time(), type))
