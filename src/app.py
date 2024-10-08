"""
Run the flask website.
"""
import os
from typing import Self

import googlemaps
import requests
from flask import Flask, request, session, g, render_template
from pydantic import BaseModel, Field, ValidationError, model_validator
from werkzeug.local import LocalProxy

from classes.charge_network import PathNotNeeded, PathNotFound
from data_model.config.con import get_con, APP_CONTEXT_DB_KEY
from data_model.config.init import init_db
from data_model.places_api import can_make_places_api_req, insert_places_api_req, TYPE_AUTO_COMPLETE, TYPE_DETAILS
from get_path import generic_charge_curve, handle_get_path_request

MAX_RANGE = 700  # todo read value from network

assert os.environ['PLACES_API_KEY']
assert os.environ['DIRECTIONS_API_KEY']

con = LocalProxy(get_con)

app = Flask(__name__)
app.secret_key = 'who_cares_lmao'  # todo: secure cookie data
with app.app_context():
    init_db()

SESSION_VARS_DEFAULTS = {
    'min-leg-length': 250,
    'ev-range': 550,
    'min-battery': 15,
    'max-battery': 100,
    'start-battery': 40
}


class InputData(BaseModel):
    """
    A pydantic class to validate user input data.
    """

    start_lat: float = Field(ge=20, le=70)
    start_lng: float = Field(ge=-160, le=-60)
    start_location: str = Field(min_length=1, max_length=200)
    end_lat: float = Field(ge=20, le=70)
    end_lng: float = Field(ge=-160, le=-60)
    end_location: str = Field(min_length=1, max_length=200)
    min_leg_length: int = Field(ge=0, le=700)
    ev_range: int = Field(ge=0, le=1000)
    min_battery: int = Field(ge=0, le=100)
    max_battery: int = Field(ge=0, le=100)
    start_battery: int = Field(ge=0, le=100)

    @model_validator(mode='after')
    def check_battery_bounds(self) -> Self:
        """Raises ValueError if min battery greater than max battery."""
        if not (self.min_battery <= self.max_battery):
            raise ValueError('min battery greater than max battery')
        return self

    @model_validator(mode='after')
    def check_effective_range(self) -> Self:
        """Raises ValueError if effective range not within min leg length and max range."""
        effective_range = (self.max_battery - self.min_battery) * self.ev_range / 100
        if not (self.min_leg_length <= effective_range <= MAX_RANGE):
            raise ValueError('effective range not within min leg length and max range')
        return self


def validate_session(s: session) -> InputData:
    """
    Pass input data to InputData pydantic class, returning the verified and formatted data or raising a ValidationError.

    Used to validate saved session data on GET requests.

    Used to validate input form data on POST requests.
    """
    return InputData(
        start_location=s.get('start-location'),
        start_lat=s.get('start-lat'),
        start_lng=s.get('start-lng'),
        end_location=s.get('end-location'),
        end_lat=s.get('end-lat'),
        end_lng=s.get('end-lng'),
        min_leg_length=s.get('min-leg-length'),
        ev_range=s.get('ev-range'),
        min_battery=s.get('min-battery'),
        max_battery=s.get('max-battery'),
        start_battery=s.get('start-battery')
    )


def reset_session(s: session) -> None:
    """
    Reset session data to default values or None.
    """
    s.pop('start-location', None)
    s.pop('start-lat', None)
    s.pop('start-lng', None)
    s.pop('end-location', None)
    s.pop('end-lat', None)
    s.pop('end-lng', None)
    s['min-leg-length'] = SESSION_VARS_DEFAULTS['min-leg-length']
    s['ev-range'] = SESSION_VARS_DEFAULTS['ev-range']
    s['min-battery'] = SESSION_VARS_DEFAULTS['min-battery']
    s['max-battery'] = SESSION_VARS_DEFAULTS['max-battery']
    s['start-battery'] = SESSION_VARS_DEFAULTS['start-battery']


def set_session(s: session, data: InputData) -> None:
    """
    Set session data to corresponding InputData data.
    """
    s['start-location'] = data.start_location
    s['start-lat'] = data.start_lat
    s['start-lng'] = data.start_lng
    s['end-location'] = data.end_location
    s['end-lat'] = data.end_lat
    s['end-lng'] = data.end_lng
    s['min-leg-length'] = data.min_leg_length
    s['ev-range'] = data.ev_range
    s['min-battery'] = data.min_battery
    s['max-battery'] = data.max_battery
    s['start-battery'] = data.start_battery


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        try:
            validate_session(session)
        except ValidationError:
            reset_session(session)
        return render_template('form.html', error='')

    if request.method == 'POST':
        try:
            input_data = validate_session(request.form)
        except ValidationError as err:
            return render_template('form.html', error=str(err))
        else:
            set_session(session, input_data)

            try:
                json_dict = handle_get_path_request(input_filepath='created_network/network.json',
                                                    min_leg_length=input_data.min_leg_length,
                                                    ev_range=input_data.ev_range,
                                                    min_battery=input_data.min_battery / 100,
                                                    max_battery=input_data.max_battery / 100,
                                                    start_battery=input_data.start_battery / 100,
                                                    charge_curve=generic_charge_curve,
                                                    coord1=(input_data.start_lat, input_data.start_lng),
                                                    coord2=(input_data.end_lat, input_data.end_lng))

                return render_template('gmap.html', result_dict=json_dict)
            except PathNotNeeded:
                return render_template('form.html',
                                       error='no path was needed since start coord and end coord snapped to same charge station')
            except PathNotFound:
                return render_template('form.html',
                                       error='no path was found between these two coordinates')
            except googlemaps.exceptions.ApiError as err:
                return render_template('form.html',
                                       error=f'no path was found due to googlemaps api error: {str(err)}')
            except Exception as err:
                return render_template('form.html',
                                       error=f'no path was found due to unknown error: {str(err)}')


@app.route('/googleapis/maps/api/place/autocomplete/json', methods=['GET'])
def place_autocomplete_wrapper():
    """
    Wrapper for the Places API Autocomplete endpoint that validates the session token and enforces daily limits.
    """
    input_query = request.args.get('input')
    components = request.args.get('components')
    language = request.args.get('language')
    session_token = request.args.get('sessiontoken')

    if not input_query:
        return {
            'predictions': [],
            'status': 'INVALID_REQUEST',
            'error_message': 'Missing "input" for this API wrapper.'
        }

    if (components != 'country:us|country:ca') or (language != 'en') or (not session_token):
        return {
            'predictions': [],
            'status': 'REQUEST_DENIED',
            'error_message': 'Unexpected or missing "components", "language", or "sessiontoken" for this API wrapper.'
        }

    if not can_make_places_api_req(session_token):
        return {
            'predictions': [],
            'status': 'REQUEST_DENIED',
            'error_message': 'You have either given an invalid token or exceeded the rate-limit for this API wrapper.'
        }

    try:
        insert_places_api_req(session_token, TYPE_AUTO_COMPLETE)
    except Exception as e:
        return {
            'predictions': [],
            'status': 'UNKNOWN_ERROR',
            'error_message': f'This API wrapper has encountered an unknown error: {e}'
        }

    query_string = request.query_string.decode()
    url = 'https://maps.googleapis.com/maps/api/place/autocomplete/json?' \
          + query_string + '&key=' + os.environ['PLACES_API_KEY']
    response = requests.get(url)
    return response.json()


@app.route('/googleapis/maps/api/place/details/json', methods=['GET'])
def place_details_wrapper():
    """
    Wrapper for the Places API Details endpoint that validates the session token and enforces daily limits.
    """
    place_id = request.args.get('place_id')
    fields = request.args.get('fields')
    language = request.args.get('language')
    session_token = request.args.get('sessiontoken')

    if not place_id:
        return {
            'html_attributions': [],
            'status': 'INVALID_REQUEST',
            'error_message': 'Missing "place_id" for this API wrapper.'
        }

    if (fields != 'geometry') or (language != 'en') or (not session_token):
        return {
            'html_attributions': [],
            'status': 'REQUEST_DENIED',
            'error_message': 'Unexpected or missing "fields", "language", or "sessiontoken" for this API wrapper.'
        }

    if not can_make_places_api_req(session_token):
        return {
            'html_attributions': [],
            'status': 'REQUEST_DENIED',
            'error_message': 'You have either given an invalid token or exceeded the rate-limit for this API wrapper.'
        }

    try:
        insert_places_api_req(session_token, TYPE_DETAILS)
    except Exception as e:
        return {
            'html_attributions': [],
            'status': 'UNKNOWN_ERROR',
            'error_message': f'This API wrapper has encountered an unknown error: {e}'
        }

    query_string = request.query_string.decode()
    url = 'https://maps.googleapis.com/maps/api/place/details/json?' \
          + query_string + '&key=' + os.environ['PLACES_API_KEY']
    response = requests.get(url)
    return response.json()


@app.teardown_appcontext
def teardown_db(exception):
    db = g.pop(APP_CONTEXT_DB_KEY, None)
    if db is not None:
        db.close()
