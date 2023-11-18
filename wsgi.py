"""
Run the flask website.
"""

import re

import googlemaps
from flask import Flask, request, session, render_template

import main
from classes import PathNotNeeded, PathNotFound
from main import generic_charge_curve

app = Flask(__name__)
app.secret_key = 'who_cares_lmao'  # TODO: secure cookie data

SESSION_VARS_TYPES = {
    'start-lat': float,  # 20 <= 70
    'start-lon': float,  # -160 <= -60
    'end-lat': float,  # 20 <= 70
    'end-lon': float,  # -160 <= -60
    'min-leg-length': int,  # 0 <= 700
    'ev-range': int,  # 0 <= 1000
    'min-battery': int,  # 0 <= 100
    'max-battery': int,  # 0 <= 100
    'start-battery': int  # 0 <= 100
}

SESSION_VARS_DEFAULTS = {
    'min-leg-length': 200,
    'ev-range': 500,
    'min-battery': 10,
    'max-battery': 80,
    'start-battery': 40
}


@app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == 'GET':

        # clear session if tampered with
        if any(
                (var not in session or not isinstance(session[var], SESSION_VARS_TYPES[var]))
                for var in SESSION_VARS_TYPES
        ):
            session.pop('start-lat', None)
            session.pop('start-lon', None)
            session.pop('end-lat', None)
            session.pop('end-lon', None)
            session['min-leg-length'] = SESSION_VARS_DEFAULTS['min-leg-length']
            session['ev-range'] = SESSION_VARS_DEFAULTS['ev-range']
            session['min-battery'] = SESSION_VARS_DEFAULTS['min-battery']
            session['max-battery'] = SESSION_VARS_DEFAULTS['max-battery']
            session['start-battery'] = SESSION_VARS_DEFAULTS['start-battery']

        return render_template('form.html', errors=[])

    elif request.method == 'POST':
        input_errors = []

        # validate input formatting and store each input in session

        if re.match(r'^-?[0-9]+(\.[0-9]+)?$', request.form['start-lat']) is None:
            input_errors.append(
                f'expected start lat to match ^-?[0-9]+(\.[0-9]+)?$ but got {request.form["start-lat"]}')
            session.pop('start-lat', None)
        elif float(request.form['start-lat']) < 20:
            input_errors.append(f'expected start lat >= 20 but got {request.form["start-lat"]}')
            session.pop('start-lat', None)
        elif float(request.form['start-lat']) > 70:
            input_errors.append(f'expected start lat <= 70 but got {request.form["start-lat"]}')
            session.pop('start-lat', None)
        else:
            session['start-lat'] = float(request.form['start-lat'])

        if re.match(r'^-?[0-9]+(\.[0-9]+)?$', request.form['start-lon']) is None:
            input_errors.append(
                f'expected start lon to match ^-?[0-9]+(\.[0-9]+)?$ but got {request.form["start-lon"]}')
            session.pop('start-lon', None)
        elif float(request.form['start-lon']) < -160:
            input_errors.append(f'expected start lon >= -160 but got {request.form["start-lon"]}')
            session.pop('start-lon', None)
        elif float(request.form['start-lon']) > -60:
            input_errors.append(f'expected start lon <= -60 but got {request.form["start-lon"]}')
            session.pop('start-lon', None)
        else:
            session['start-lon'] = float(request.form['start-lon'])

        if re.match(r'^-?[0-9]+(\.[0-9]+)?$', request.form['end-lat']) is None:
            input_errors.append(f'expected end lat to match ^-?[0-9]+(\.[0-9]+)?$ but got {request.form["end-lat"]}')
            session.pop('end-lat', None)
        elif float(request.form['end-lat']) < 20:
            input_errors.append(f'expected end lat >= 20 but got {request.form["end-lat"]}')
            session.pop('end-lat', None)
        elif float(request.form['end-lat']) > 70:
            input_errors.append(f'expected end lat <= 70 but got {request.form["end-lat"]}')
            session.pop('end-lat', None)
        else:
            session['end-lat'] = float(request.form['end-lat'])

        if re.match(r'^-?[0-9]+(\.[0-9]+)?$', request.form['end-lon']) is None:
            input_errors.append(f'expected end lon to match ^-?[0-9]+(\.[0-9]+)?$ but got {request.form["end-lon"]}')
            session.pop('end-lon', None)
        elif float(request.form['end-lon']) < -160:
            input_errors.append(f'expected end lon >= -160 but got {request.form["end-lon"]}')
            session.pop('end-lon', None)
        elif float(request.form['end-lon']) > -60:
            input_errors.append(f'expected end lon <= -60 but got {request.form["end-lon"]}')
            session.pop('end-lon', None)
        else:
            session['end-lon'] = float(request.form['end-lon'])

        if request.form['min-leg-length-slider'] != request.form['min-leg-length-input']:
            input_errors.append('expected min leg length slider and input values to match but got '
                                f'{request.form["min-leg-length-slider"]} and {request.form["min-leg-length-input"]}')
            session['min-leg-length'] = SESSION_VARS_DEFAULTS['min-leg-length']
        elif not request.form['min-leg-length-slider'].isnumeric():
            input_errors.append(f'expected min leg length to be float but got {request.form["min-leg-length-slider"]}')
            session['min-leg-length'] = SESSION_VARS_DEFAULTS['min-leg-length']
        elif int(request.form['min-leg-length-slider']) < 0:
            input_errors.append(f'expected min leg length >= 0 but got {request.form["min-leg-length-slider"]}')
            session['min-leg-length'] = SESSION_VARS_DEFAULTS['min-leg-length']
        elif int(request.form['min-leg-length-slider']) > 700:
            input_errors.append(f'expected min leg length <= 700 but got {request.form["min-leg-length-slider"]}')
            session['min-leg-length'] = SESSION_VARS_DEFAULTS['min-leg-length']
        else:
            print('set session min leg length to', int(request.form['min-leg-length-slider']))
            session['min-leg-length'] = int(request.form['min-leg-length-slider'])

        if request.form['ev-range-slider'] != request.form['ev-range-input']:
            input_errors.append('expected ev range slider and input values to match but got '
                                f'{request.form["ev-range-slider"]} and {request.form["ev-range-input"]}')
            session['ev-range'] = SESSION_VARS_DEFAULTS['ev-range']
        elif not request.form['ev-range-slider'].isnumeric():
            input_errors.append(f'expected ev range to be float but got {request.form["ev-range-slider"]}')
            session['ev-range'] = SESSION_VARS_DEFAULTS['ev-range']
        elif int(request.form['ev-range-slider']) < 0:
            input_errors.append(f'expected ev range >= 0 but got {request.form["ev-range-slider"]}')
            session['ev-range'] = SESSION_VARS_DEFAULTS['ev-range']
        elif int(request.form['ev-range-slider']) > 1000:
            input_errors.append(f'expected ev range <= 700 but got {request.form["ev-range-slider"]}')
            session['ev-range'] = SESSION_VARS_DEFAULTS['ev-range']
        else:
            session['ev-range'] = int(request.form['ev-range-slider'])

        if request.form['min-battery-slider'] != request.form['min-battery-input']:
            input_errors.append('expected min battery slider and input values to match but got '
                                f'{request.form["min-battery-slider"]} and {request.form["min-battery-input"]}')
            session['min-battery'] = SESSION_VARS_DEFAULTS['min-battery']
        elif not request.form['min-battery-slider'].isnumeric():
            input_errors.append(f'expected min battery to be float but got {request.form["min-battery-slider"]}')
            session['min-battery'] = SESSION_VARS_DEFAULTS['min-battery']
        elif int(request.form['min-battery-slider']) < 0:
            input_errors.append(f'expected min battery >= 0 but got {request.form["min-battery-slider"]}')
            session['min-battery'] = SESSION_VARS_DEFAULTS['min-battery']
        elif int(request.form['min-battery-slider']) > 100:
            input_errors.append(f'expected min battery <= 700 but got {request.form["min-battery-slider"]}')
            session['min-battery'] = SESSION_VARS_DEFAULTS['min-battery']
        else:
            session['min-battery'] = int(request.form['min-battery-slider'])

        if request.form['max-battery-slider'] != request.form['max-battery-input']:
            input_errors.append('expected max battery slider and input values to match but got '
                                f'{request.form["max-battery-slider"]} and {request.form["max-battery-input"]}')
            session['max-battery'] = SESSION_VARS_DEFAULTS['max-battery']
        elif not request.form['max-battery-slider'].isnumeric():
            input_errors.append(f'expected max battery to be float but got {request.form["max-battery-slider"]}')
            session['max-battery'] = SESSION_VARS_DEFAULTS['max-battery']
        elif int(request.form['max-battery-slider']) < 0:
            input_errors.append(f'expected max battery >= 0 but got {request.form["max-battery-slider"]}')
            session['max-battery'] = SESSION_VARS_DEFAULTS['max-battery']
        elif int(request.form['max-battery-slider']) > 100:
            input_errors.append(f'expected max battery <= 700 but got {request.form["max-battery-slider"]}')
            session['max-battery'] = SESSION_VARS_DEFAULTS['max-battery']
        else:
            session['max-battery'] = int(request.form['max-battery-slider'])

        if request.form['start-battery-slider'] != request.form['start-battery-input']:
            input_errors.append('expected start battery slider and input values to match but got '
                                f'{request.form["start-battery-slider"]} and {request.form["start-battery-input"]}')
            session['start-battery'] = SESSION_VARS_DEFAULTS['start-battery']
        elif not request.form['start-battery-slider'].isnumeric():
            input_errors.append(f'expected start battery to be float but got {request.form["start-battery-slider"]}')
            session['start-battery'] = SESSION_VARS_DEFAULTS['start-battery']
        elif int(request.form['start-battery-slider']) < 0:
            input_errors.append(f'expected start battery >= 0 but got {request.form["start-battery-slider"]}')
            session['start-battery'] = SESSION_VARS_DEFAULTS['start-battery']
        elif int(request.form['start-battery-slider']) > 100:
            input_errors.append(f'expected start battery <= 700 but got {request.form["start-battery-slider"]}')
            session['start-battery'] = SESSION_VARS_DEFAULTS['start-battery']
        else:
            session['start-battery'] = int(request.form['start-battery-slider'])

        if input_errors:
            return render_template('form.html', errors=input_errors)

        # validate input requirements

        effective_range = (session['max-battery'] / 100 - session['min-battery'] / 100) * (session['ev-range'])
        if session['min-battery'] > session['max-battery']:
            input_errors.append('expected min battery <= max batter but got '
                                f'{request.form["min-battery"]} > {request.form["max-battery"]}')
        if session['min-leg-length'] > effective_range:
            input_errors.append('expected min-leg-length <= effective range but got '
                                f'{session["min-leg-length"]} > {effective_range}')
        if effective_range > 700:
            input_errors.append(f'expected effective range <= 700 but got {effective_range} > 700')

        if input_errors:
            return render_template('form.html', errors=input_errors)

        # try to display result

        try:
            result_dict = main.find_path_and_get_json_ready(
                input_filepath='created_network/network.json',
                min_leg_length=session['min-leg-length'],
                ev_range=session['ev-range'],
                min_battery=session['min-battery'] / 100,
                max_battery=session['max-battery'] / 100,
                start_battery=session['start-battery'] / 100,
                charge_curve=generic_charge_curve,
                coord1=(session['start-lat'], session['start-lon']),
                coord2=(session['end-lat'], session['end-lon'])
            )

            return render_template('gmap.html', result_dict=result_dict)

        except PathNotNeeded:
            input_errors.append('no path was needed since start coord and end coord snapped to same charge station')
            return render_template('form.html', errors=input_errors)

        except PathNotFound:
            input_errors.append('no path was found between these two coordinates')
            return render_template('form.html', errors=input_errors)

        except googlemaps.exceptions.ApiError as err:
            input_errors.append(f'no path was found due to googlemaps api error: {err}')
            return render_template('form.html', errors=input_errors)
