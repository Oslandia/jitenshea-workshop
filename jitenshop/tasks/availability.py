"""Luigi tasks dedicated to bike availability timeseries recovery
"""

from datetime import datetime
import json
import os

import luigi
from luigi.contrib.postgres import CopyToTable
from luigi.format import UTF8
import pandas as pd
import requests

from jitenshop import config
from jitenshop.tasks import db, stations
from jitenshop.tasks import one_week_ago

DATADIR = config["main"]["datadir"]
LYON_BIKEAVAILABILITY_URL = config["lyon"]["availability_url"]
LYON_BIKEFULLAVAILABILITY_URL = config["lyon"]["full_availability_url"]


class RealTimeAvailability(luigi.Task):
    """
    """

    @property
    def path(self):
        return os.path.join(
            DATADIR, "lyon", '{year}', '{month:02d}', '{day:02d}', '{ts}.json'
        )

    @property
    def timestamp(self):
        return datetime.now()

    @property
    def url(self):
        return LYON_BIKEAVAILABILITY_URL

    def requires(self):
        return stations.NormalizeStationTable()

    def output(self):
        def triple(x):
            return (x.year, x.month, x.day)
        year, month, day = triple(self.timestamp)
        ts = self.timestamp.strftime("%HH%MM")  # 16H35
        return luigi.LocalTarget(
            self.path.format(year=year, month=month, day=day, ts=ts),
            format=UTF8
        )

    def run(self):
        session = requests.Session()
        resp = session.get(LYON_BIKEAVAILABILITY_URL)
        with self.output().open('w') as fobj:
            json.dump(resp.json(), fobj, ensure_ascii=False)


class RealTimeAvailabilityToCSV(luigi.Task):
    """Turn real-time bike availability to CSV files
    """

    @property
    def path(self):
        return os.path.join(
            DATADIR, "lyon", '{year}', '{month:02d}', '{day:02d}', '{ts}.csv'
        )

    @property
    def timestamp(self):
        return datetime.now()

    def requires(self):
        return RealTimeAvailability(self.timestamp)

    def output(self):
        def triple(x):
            return (x.year, x.month, x.day)
        year, month, day = triple(self.timestamp)
        ts = self.timestamp.strftime('%HH%M')  # 16H35
        return luigi.LocalTarget(
            self.path.format(year=year, month=month, day=day, ts=ts),
            format=UTF8
        )

    def run(self):
        with self.input().open() as fobj:
            data = json.load(fobj)
            df = pd.DataFrame(data['values'], columns=data['fields'])
            status_key = config['lyon']['feature_status']
            df[status_key] = df[status_key].apply(
                lambda x: 'open' if x == 'OPEN' else 'closed'
            )
        df = df[[config["lyon"]['feature_avl_id'],
                 config["lyon"]['feature_timestamp'],
                 config["lyon"]['feature_avl_stands'],
                 config["lyon"]['feature_avl_bikes'],
                 config["lyon"]['feature_status']]]
        df.columns = [
            "id", "timestamp", "available_stands", "available_bikes", "status"
        ]
        df = df.sort_values(by="id")
        with self.output().open('w') as fobj:
            df.to_csv(fobj, index=False)


class RealTimeAvailabilityToDB(CopyToTable):
    """Insert bike availability data into a PostgreSQL table
    """

    host = config['database']['host']
    database = config['database']['dbname']
    user = config['database']['user']
    password = config['database'].get('password')

    columns = [('id', 'VARCHAR'),
               ('timestamp', 'TIMESTAMP'),
               ('available_stands', 'INT'),
               ('available_bikes', 'INT'),
               ('status', 'VARCHAR(12)')]

    @property
    def table(self):
        return '{schema}.{tablename}'.format(
            schema=config["lyon"]["schema"],
            tablename='realtime'
        )

    def requires(self):
        return RealTimeAvailabilityToCSV()

    def rows(self):
        """overload the rows method to skip the first line (header)
        """
        with self.input().open('r') as fobj:
            df = pd.read_csv(fobj)
            for idx, row in df.iterrows():
                if row.status == 'None' or row.available_stands == 'None':
                    continue
                yield row.values


class Availability(luigi.Task):
    """
    """
    start = luigi.DateParameter(default=one_week_ago())
    stop = luigi.DateParameter(default=datetime.now())

    def requires(self):
        return db.CreateSchema()

    @property
    def path(self):
        return os.path.join(
            DATADIR, "lyon", "full_availability",
            "{date_begin}-{date_end}.json"
        )

    @property
    def url(self):
        start_date = self.start.strftime("%Y-%m-%dT%H:%M:%SZ")
        stop_date = self.stop.strftime("%Y-%m-%dT%H:%M:%SZ")
        return LYON_BIKEFULLAVAILABILITY_URL.format(start_date, stop_date)

    def output(self):
        begin = self.start.strftime("%Y%m%d")
        end = self.stop.strftime("%Y%m%d")
        return luigi.LocalTarget(
            self.path.format(date_begin=begin, date_end=end),
            format=UTF8
        )

    def run(self):
        session = requests.Session()
        resp = session.get(self.url)
        with self.output().open('w') as fobj:
            json.dump(resp.json(), fobj, ensure_ascii=False)


class AvailabilityToCSV(luigi.Task):
    """Turn real-time bike availability to CSV files
    """
    start = luigi.DateParameter(default=one_week_ago())
    stop = luigi.DateParameter(default=datetime.now())

    @property
    def path(self):
        return os.path.join(
            DATADIR, "lyon", "full_availability", "{date_begin}-{date_end}.csv"
        )

    def requires(self):
        return Availability(self.start, self.stop)

    def output(self):
        begin = self.start.strftime("%Y%m%d")
        end = self.stop.strftime("%Y%m%d")
        return luigi.LocalTarget(
            self.path.format(date_begin=begin, date_end=end),
            format=UTF8
        )

    def run(self):
        with self.input().open() as fobj:
            data = json.load(fobj)
            datalist = []
            for d in data["ObservationCollection"]["member"]:
                cur_d = d["result"]["DataArray"]["values"]
                station_id = d["name"].split("-")[1]
                cur_d = [
                    [item[0], int(float(item[1])), station_id]
                    for item in cur_d
                ]
                datalist += cur_d
            df = pd.DataFrame(
                datalist, columns=["timestamp", "available_bikes", "id"]
            )
            df.loc[:, "timestamp"] = pd.to_datetime(df["timestamp"])
            df.sort_values("timestamp")
            with self.output().open('w') as fobj:
                df.to_csv(fobj, index=False)


class AvailabilityToDB(CopyToTable):
    """Insert bike availability data into a PostgreSQL table
    """
    start = luigi.DateParameter(default=one_week_ago())
    stop = luigi.DateParameter(default=datetime.now())

    host = config['database']['host']
    database = config['database']['dbname']
    user = config['database']['user']
    password = config['database'].get('password')

    columns = [('timestamp', 'TIMESTAMP'),
               ('available_bikes', 'INT'),
               ('id', 'VARCHAR')]

    @property
    def table(self):
        return '{schema}.timeseries'.format(schema=config["lyon"]["schema"])

    def requires(self):
        return AvailabilityToCSV(self.start, self.stop)

    def rows(self):
        """overload the rows method to skip the first line (header)
        """
        with self.input().open('r') as fobj:
            df = pd.read_csv(fobj)
            for idx, row in df.iterrows():
                yield row.values
