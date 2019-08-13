# coding: utf-8

"""Database controller for the Flask Web API
"""

from itertools import groupby
from datetime import datetime, timedelta
from collections import namedtuple

import daiquiri
import pandas as pd

from jitenshop import config
from jitenshop.iodb import engine


logger = daiquiri.getLogger(__name__)


def timeseries(station_ids, start, stop):
    """Get timeseries data between two dates for a specific city and a list of
    station ids

    Feed the URL "/lyon/timeseries/<ids>"

    Parameters
    ----------
    station_ids : list
    start : datetime.datetime
    stop : datetime.datetime

    Returns
    -------
    dict
        Availability timeseries for required stations
    """
    query = """SELECT T.*
      ,S.name as name
      ,S.nb_stations as nb_stands
    FROM {schema}.timeseries AS T
    LEFT JOIN {schema}.station AS S using(id)
    WHERE id IN %(id_list)s AND timestamp >= %(start)s AND timestamp < %(stop)s
    ORDER BY id,timestamp
    """.format(schema=config["lyon"]["schema"])
    eng = engine()
    rset = eng.execute(
        query, id_list=tuple(x for x in station_ids), start=start, stop=stop
    )
    if not rset:
        return []
    data = [dict(zip(x.keys(), x)) for x in rset]
    values = []
    for k, group in groupby(data, lambda x: x['id']):
        group = list(group)
        values.append(
            {
                'id': k,
                'name': group[0]['name'],
                'nb_stands': group[0]['nb_stands'],
                "ts": [x['timestamp'] for x in group],
                'available_bikes': [x['available_bikes'] for x in group],
            }
        )
    return {"data": values}


def specific_stations(ids):
    """List of asked stations

    Feed the URL "/lyon/stations/<ids>"

    Parameters
    ----------
    ids : list

    Returns
    -------
    list of dict
        One dict by bicycle station
    """
    query = """SELECT id
      , name
      , address
      , city
      , nb_stations as nb_stands
      , st_x(geom) as x
      , st_y(geom) as y
    FROM {schema}.station
    WHERE id IN %(id_list)s
    """.format(schema=config["lyon"]["schema"])
    eng = engine()
    rset = eng.execute(query, id_list=tuple(str(x) for x in ids)).fetchall()
    if not rset:
        return []
    return {"data": [dict(zip(x.keys(), x)) for x in rset]}


def station_geojson(stations, feature_list):
    """Process station data into GeoJSON
    """
    result = []
    for data in stations:
        result.append(
            {"type": "Feature",
             "geometry": {
                 "type": "Point",
                 "coordinates": [data['x'], data['y']]
             },
             "properties": {k: data[k] for k in feature_list}
            })
    return {"type": "FeatureCollection", "features": result}


def latest_availability(limit, geojson):
    """Get bike the latest bikes availability for a specific city.

    Feed the URL "/lyon/availability"

    Parameters
    ----------
    limit : int
        Max number of stations
    geosjon : bool
        Data in geojson?
    freq : str
        Time horizon

    Returns
    -------
    dict
    """
    query = """with latest as (
      select id
        ,timestamp
        ,available_bikes as nb_bikes
        ,rank() over (partition by id order by timestamp desc) as rank
      from {city}.timeseries
      where timestamp >= %(min_date)s
    )
    select P.id
      ,P.timestamp
      ,P.nb_bikes
      ,S.name
      ,S.nb_stations as nb_stands
      ,st_x(S.geom) as x
      ,st_y(S.geom) as y
    from latest as P
    join {city}.station as S using(id)
    where P.rank=1
    order by id
    limit %(limit)s
    """.format(city=config["lyon"]["schema"])
    eng = engine()
    # avoid getting the full history
    min_date = datetime.now() - timedelta(days=2)
    rset = eng.execute(query, min_date=min_date, limit=limit)
    keys = rset.keys()
    result = [dict(zip(keys, row)) for row in rset]
    latest_date = max(x['timestamp'] for x in result)
    if geojson:
        return station_geojson(result, feature_list=['id', 'name', 'timestamp', 'nb_bikes', 'nb_stands'])
    return {"data": result, "date": latest_date}


def clustered_station_geojson(stations):
    """Process station data into GeoJSON

    Parameters
    ----------
    stations : list of dicts
        Clustered stations

    Returns
    -------
    dict
        Clustered stations formatted as a GeoJSon object
    """
    result = []
    for data in stations:
        result.append(
            {"type": "Feature",
             "geometry": {
                 "type": "Point",
                 "coordinates": [data['x'], data['y']]
             },
             "properties": {
                 "id": data['id'],
                 "cluster_id": data['cluster_id'],
                 "name": data['name'],
                 "start": data['start'],
                 "stop": data['stop']
             }})
    return {"type": "FeatureCollection", "features": result}


def get_station_ids():
    """Provides the list of shared-bike station IDs in Lyon

    Returns
    -------
    list of integers
        IDs of the shared-bike stations in Lyon
    """
    query = "SELECT id FROM {schema}.{table};".format(
        schema=config["lyon"]["schema"], table='station'
    )
    eng = engine()
    rset = eng.execute(query).fetchall()
    if not rset:
        return []
    return [row[0] for row in rset]


def station_cluster_query():
    """SQL query to get cluster IDs for some shared_bike stations within Lyon

    Returns
    -------
    str
        SQL query that gives the cluster ID for shared-bike stations in Lyon
    """
    return (
        "WITH ranked_clusters AS ("
        "SELECT cs.station_id AS id, "
        "cs.cluster_id, "
        "cs.start AS start, "
        "cs.stop AS stop, "
        "citystation.name AS name, "
        "citystation.geom AS geom, "
        "rank() OVER (ORDER BY stop DESC) AS rank "
        "FROM {schema}.cluster AS cs "
        "JOIN {schema}.station AS citystation "
        "ON citystation.id = cs.station_id "
        "WHERE cs.station_id IN %(id_list)s) "
        "SELECT id, cluster_id, start, stop, name, "
        "st_x(geom) as x, "
        "st_y(geom) as y "
        "FROM ranked_clusters "
        "WHERE rank=1"
        ";"
    ).format(schema=config["lyon"]["schema"])


def station_clusters(station_ids=None, geojson=False):
    """Return the cluster IDs of shared-bike stations in `city`, when running a
    K-means algorithm between `day` and `day+window`

    Feed the URL "/lyon/clusters"

    Parameters
    ----------
    station_ids : list of integer
        Shared-bike station IDs ; if None, all the city stations are considered
    geojson : boolean
        If true, returns the clustered stations under the GeoJSON format

    Returns
    -------
    dict
        Cluster profiles for each cluster, at each hour of the day

    """
    if station_ids is None:
        station_ids = get_station_ids()
    query = station_cluster_query()
    eng = engine()
    rset = eng.execute(query,
                       id_list=tuple(str(x) for x in station_ids))
    if not rset:
        logger.warning("rset is empty")
        return {"data": []}
    data = {"data": [dict(zip(rset.keys(), row)) for row in rset]}
    if geojson:
        return clustered_station_geojson(data["data"])
    return data


def cluster_profile_query():
    """SQL query to get cluster descriptions as 24-houred timeseries within
    in Lyon

    Returns
    -------
    str
        SQL query that gives the timeseries cluster profile in Lyon

    """
    return (
        "WITH ranked_centroids AS ("
        "SELECT *, rank() OVER (ORDER BY stop DESC) AS rank "
        "FROM {schema}.centroid"
        ") "
        "SELECT cluster_id, "
        "h00, h01, h02, h03, h04, h05, h06, h07, h08, h09, h10, h11, "
        "h12, h13, h14, h15, h16, h17, h18, h19, h20, h21, h22, h23, "
        "start, stop "
        "FROM ranked_centroids "
        "WHERE rank=1"
        ";"
    ).format(schema=config["lyon"]["schema"])


def cluster_profiles():
    """Return the cluster profiles in Lyon, when running a K-means algorithm
    between day and day+window

    Feed the URL "/lyon/centroids"

    Returns
    -------
    dict
        Cluster profiles for each cluster, at each hour of the day
    """
    query = cluster_profile_query()
    eng = engine()
    df = pd.io.sql.read_sql_query(query, eng)
    if df.empty:
        logger.warning("df is empty")
        return {"data": []}
    df = df.set_index('cluster_id')
    result = []
    for cluster_id, cluster in df.iterrows():
        result.append({
            "cluster_id": cluster_id,
            "start": cluster['start'],
            'stop': cluster['stop'],
            'hour': list(range(24)),
            'values': [
                cluster[h] for h in ["h{:02d}".format(i) for i in range(24)]
            ]
        })
    return {"data": result}
