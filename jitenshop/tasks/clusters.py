"""Luigi tasks dedicated to bike station clustering
"""

from datetime import date
import os

import luigi
from luigi.contrib.postgres import CopyToTable
from luigi.format import MixedUnicodeBytes
import pandas as pd
from sklearn.cluster import KMeans

from jitenshop import config, iodb
from jitenshop.tasks import availability
from jitenshop.tasks import one_week_ago


DATADIR = config["main"]["datadir"]


def preprocess_data_for_clustering(df):
    """Prepare data in order to apply a clustering algorithm

    Parameters
    ----------
    df : pandas.DataFrame
        Input data, *i.e.* city-related timeseries, supposed to have
    `station_id`, `ts` and `nb_bikes` columns

    Returns
    -------
    pandas.DataFrame
        Simpified version of `df`, ready to be used for clustering

    """
    # Filter unactive stations
    max_bikes = df.groupby("station_id")["nb_bikes"].max()
    unactive_stations = max_bikes[max_bikes == 0].index.tolist()
    df = df[~ df['station_id'].isin(unactive_stations)]
    # Set timestamps as the DataFrame index
    # and resample it with 5-minute periods
    df = (df.set_index("ts")
          .groupby("station_id")["nb_bikes"]
          .resample("5T")
          .mean()
          .bfill())
    df = df.unstack(0)
    # Drop week-end records
    df = df[df.index.weekday < 5]
    # Gather data regarding hour of the day
    df['hour'] = df.index.hour
    df = df.groupby("hour").mean()
    return df / df.max()


def compute_clusters(df, n_clusters=4):
    """Compute station clusters based on bike availability time series

    Parameters
    ----------
    df : pandas.DataFrame
        Input data, *i.e.* city-related timeseries, supposed to have
    `station_id`, `ts` and `nb_bikes` columns
    n_clusters : int
        Number of desired clusters

    Returns
    -------
    dict
        Two pandas.DataFrame, the former for station clusters and the latter
    for cluster centroids

    """
    df_norm = preprocess_data_for_clustering(df)
    model = KMeans(n_clusters=n_clusters, random_state=0)
    kmeans = model.fit(df_norm.T)
    df_labels = pd.DataFrame(
        {"id_station": df_norm.columns, "labels": kmeans.labels_}
    )
    df_centroids = pd.DataFrame(kmeans.cluster_centers_).reset_index()
    return {"labels": df_labels, "centroids": df_centroids}


class ComputeClusters(luigi.Task):
    """Compute clusters corresponding to bike availability in `city` stations
    between a `start` and an `end` date
    """
    n_clusters = luigi.IntParameter(default=4)
    start = luigi.DateParameter(default=one_week_ago())
    stop = luigi.DateParameter(default=date.today())

    def requires(self):
        return availability.AvailabilityToDB(self.start, self.stop)

    def outputpath(self):
        begin = self.start.strftime("%Y%m%d")
        end = self.stop.strftime("%Y%m%d")
        fname = "kmeans-{}-to-{}-{}.h5".format(begin, end, self.n_clusters)
        return os.path.join(DATADIR, "lyon", 'clustering', fname)

    def output(self):
        return luigi.LocalTarget(self.outputpath(), format=MixedUnicodeBytes)

    def run(self):
        query = (
            "SELECT id, timestamp, available_bikes "
            "FROM {schema}.timeseries "
            "WHERE timestamp >= %(start)s "
            "AND timestamp < %(stop)s;"
            ""
        ).format(schema=config["lyon"]["schema"])
        eng = iodb.engine()
        df = pd.io.sql.read_sql_query(
            query, eng, params={"start": self.start, "stop": self.stop}
        )
        df.columns = ["station_id", "ts", "nb_bikes"]
        clusters_ = compute_clusters(df, self.n_clusters)
        self.output().makedirs()
        path = self.output().path
        clusters_['labels'].to_hdf(path, '/clusters')
        clusters_['centroids'].to_hdf(path, '/centroids')


class StoreClustersToDatabase(CopyToTable):
    """Read the cluster labels from `DATADIR/lyon/clustering.h5` file and store
    them into `clustered_stations`

    """
    n_clusters = luigi.IntParameter(default=4)
    start = luigi.DateParameter(default=one_week_ago())
    stop = luigi.DateParameter(default=date.today())

    host = config['database']['host']
    database = config['database']['dbname']
    user = config['database']['user']
    password = config['database'].get('password')

    columns = [('station_id', 'VARCHAR'),
               ('start', 'DATE'),
               ('stop', 'DATE'),
               ('cluster_id', 'VARCHAR')]

    @property
    def table(self):
        return '{schema}.cluster'.format(schema=config["lyon"]["schema"])

    def rows(self):
        inputpath = self.input().path
        clusters = pd.read_hdf(inputpath, 'clusters')
        for _, row in clusters.iterrows():
            modified_row = list(row.values)
            modified_row.insert(1, self.stop)
            modified_row.insert(1, self.start)
            yield modified_row

    def requires(self):
        return ComputeClusters(self.n_clusters, self.start, self.stop)

    def create_table(self, connection):
        if len(self.columns[0]) == 1:
            # only names of columns specified, no types
            raise NotImplementedError(("create_table() not implemented for %r "
                                       "and columns types not specified")
                                      % self.table)
        elif len(self.columns[0]) == 2:
            # if columns is specified as (name, type) tuples
            coldefs = ','.join('{name} {type}'.format(name=name, type=type)
                               for name, type in self.columns)
            query = ("CREATE TABLE {table} ({coldefs}, "
                     "PRIMARY KEY (station_id, start, stop));"
                     "").format(table=self.table, coldefs=coldefs)
            connection.cursor().execute(query)


class StoreCentroidsToDatabase(CopyToTable):
    """Read the cluster centroids from `DATADIR/lyon/clustering.h5` file and
    store them into `centroids`

    """
    n_clusters = luigi.IntParameter(default=4)
    start = luigi.DateParameter(default=one_week_ago())
    stop = luigi.DateParameter(default=date.today())

    host = config['database']['host']
    database = config['database']['dbname']
    user = config['database']['user']
    password = config['database'].get('password')
    first_columns = [('cluster_id', 'VARCHAR'),
                     ('start', 'DATE'),
                     ('stop', 'DATE')]

    @property
    def columns(self):
        if len(self.first_columns) == 3:
            self.first_columns.extend(
                [('h{:02d}'.format(i), 'DOUBLE PRECISION') for i in range(24)]
            )
        return self.first_columns

    @property
    def table(self):
        return '{schema}.centroid'.format(schema=config["lyon"]["schema"])

    def rows(self):
        inputpath = self.input().path
        clusters = pd.read_hdf(inputpath, 'centroids')
        for _, row in clusters.iterrows():
            modified_row = list(row.values)
            modified_row[0] = int(modified_row[0])
            modified_row.insert(1, self.stop)
            modified_row.insert(1, self.start)
            yield modified_row

    def requires(self):
        return ComputeClusters(self.n_clusters, self.start, self.stop)

    def create_table(self, connection):
        if len(self.columns[0]) == 1:
            # only names of columns specified, no types
            raise NotImplementedError(("create_table() not implemented for %r "
                                       "and columns types not specified")
                                      % self.table)
        elif len(self.columns[0]) == 2:
            # if columns is specified as (name, type) tuples
            coldefs = ','.join('{name} {type}'.format(name=name, type=type)
                               for name, type in self.columns)
            query = ("CREATE TABLE {table} ({coldefs}, "
                     "PRIMARY KEY (cluster_id, start, stop));"
                     "").format(table=self.table, coldefs=coldefs)
            connection.cursor().execute(query)
