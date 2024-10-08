"""
Discuss and define API rate limit constants.

See also:
https://developers.google.com/maps/documentation/places/web-service/session-tokens
"""

from datetime import timedelta

"""
We use autocomplete sessions ($0.017 per session) instead of individual autocomplete requests ($0.00283 per request)
to ensure predictable billing per session (roughly the cost of 6 individual autocomplete requests).

Google defines an autocomplete session as a set of requests using a common session token that
may or may not end with a place details request "within a few minutes of the beginning of the session".
"""

PLACES_API_TOKEN_AGE_LIMIT = timedelta(minutes=2)

"""
We currently do not authenticate users and thus must have a global daily rate limit for each API endpoint.

The following front end keys are stored by unicode code points to avoid the keys being scrapped from github.
    - Maps JavaScript API key (rate limited via google cloud quota)

The following back end keys are stored in environment variables which are asserted in the flask app python file.
    - Directions API key (rate limited via quota)
    - Places API key (rate limited manually using the data_model)

The intended use case consists of the following API requests.
    - 2x Autocomplete and Place Details – Per Session        ($0.017)                        Places API
    - Directions Advanced                                    ($0.01)                     Directions API
    - Dynamic Maps                                           ($0.007)               Maps JavaScript API

let p = Places API requests per month
let d = Directions API requests per month
let m = Maps JavaScript API requests per month

Based on the $200 monthly credit for the google maps platform, we have the following equation.

p/2 = d = m

However, google currently does not support specific SKU rate limits for each endpoint. This means that if someone
were to steal a front end api key, they could use it to repeatedly charge the most expensive SKU for that endpoint.

The most expensive SKU for the Maps JavaScript API costs $0.014 per request.

(annoyingly the Maps JavaScript API does have separate quotas for map loads and 3d map loads,
but the expensive dynamic street view SKU is not counted as a 3d map load; only google earth style maps are)

0.017p + 0.01d + 0.014m = 200

Solving the above system of equations gives us the following values.

p = 6,896.552 (222 requests per day)
d = 3,448.276 (111 requests per day)
m = 3,448.276 (111 requests per day)
"""
PLACES_API_DAILY_SESSION_LIMIT = 222
DIRECTIONS_API_DAILY_REQUEST_LIMIT = 111
MAPS_JAVASCRIPT_API_DAILY_REQUEST_LIMIT = 111
