"""
Initialize and get the database.
"""
import sqlite3

from flask import g

DATABASE = 'data_model/config/db.sqlite'
APP_CONTEXT_DB_KEY = '_db'


def get_con() -> sqlite3.Connection:
    """
    Connects to the database for this application context.

    Can only be called within an application context.
    """
    db = g.get(APP_CONTEXT_DB_KEY)
    if db is None:
        db = g._db = sqlite3.connect(DATABASE)
    return db
