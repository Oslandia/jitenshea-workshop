"""Shared-bike data rendering through a Flask-RESTplus API
"""

from dateutil.parser import parse

from flask import jsonify
from flask_restplus import inputs
from flask_restplus import Resource, Api

from jitenshop import controller


def parse_timestamp(str_timestamp):
    """Parse a string and convert it to a datetime

    ISO 8601 format, i.e.
      - YYYY-MM-DD
      - YYYY-MM-DDThh
      - YYYY-MM-DDThhmm
    """
    try:
        dt = parse(str_timestamp)
    except Exception as e:
        api.abort(422, "date from the request cannot be parsed: {}".format(e))
    return dt


# API declaration
api = Api(
    title='Jitenshop: Bicycle-sharing data analysis',
    prefix='/api',
    doc=False,
    version='0.1',
    description="Retrieve some shared-bike system data."
)

# Station list rendering
station_list_parser = api.parser()
station_list_parser.add_argument(
    "limit", required=False, type=int, default=1000,
    dest='limit', location='args', help='Limit'
)
station_list_parser.add_argument(
    "geojson", required=False, default=False, dest='geojson',
    location='args', help='GeoJSON format?'
)


@api.route("/lyon/availability")
class CityStationList(Resource):
    @api.doc(parser=station_list_parser,
             description="Latest bike availability at stations")
    def get(self):
        args = station_list_parser.parse_args()
        limit = args['limit']
        geojson = args['geojson']
        return jsonify(controller.latest_availability(limit, geojson))


@api.route("/lyon/stations/<list:ids>")
class CityStation(Resource):
    @api.doc(description="Bicycle station(s)")
    def get(self, ids):
        rset = controller.specific_stations(ids)
        if not rset:
            api.abort(404, "No such id: {}".format(ids))
        return jsonify(rset)


# Bike availability rendering
timeseries_parser = api.parser()
timeseries_parser.add_argument(
    "start", required=True, dest="start", location="args",
    help="Start date YYYY-MM-DDThhmm"
)
timeseries_parser.add_argument(
    "stop", required=True, dest="stop", location="args",
    help="Stop date YYYY-MM-DDThhmm"
)


@api.route("/lyon/timeseries/<list:ids>")
class TimeseriesStation(Resource):
    """Render the bike availability timeseries in Lyon between two dates of
    interest
    """
    @api.doc(parser=timeseries_parser,
             description="Bike availability timeseries")
    def get(self, ids):
        args = timeseries_parser.parse_args()
        start = parse_timestamp(args['start'])
        stop = parse_timestamp(args['stop'])
        rset = controller.timeseries(ids, start, stop)
        if not rset:
            api.abort(
                404,
                "No such data for id: {} between {} and {}".format(
                    ids, start, stop
                )
            )
        return jsonify(rset)


# Bike station cluster rendering
clustering_parser = api.parser()
clustering_parser.add_argument(
    "geojson", required=False, type=inputs.boolean,
    default=False, dest='geojson', location='args', help='GeoJSON format?'
)


@api.route("/lyon/clusters")
class CityClusteredStation(Resource):
    @api.doc(parser=clustering_parser,
             description="Clustered stations according to k-means algorithm")
    def get(self):
        args = clustering_parser.parse_args()
        rset = controller.station_clusters(geojson=args['geojson'])
        if not rset:
            api.abort(404, ("No K-means algorithm trained in this city"))
        return jsonify(rset)


@api.route("/lyon/centroids")
class CityClusterCentroids(Resource):
    @api.doc(description="Centroids of k-means clusters")
    def get(self):
        rset = controller.cluster_profiles()
        if not rset:
            api.abort(404, ("No K-means algorithm trained in this city"))
        return jsonify(rset)
