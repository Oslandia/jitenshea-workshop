"""Luigi tasks dedicated to station recovery
"""

from datetime import datetime
import os
import sh
import zipfile

import luigi
from luigi.contrib.postgres import PostgresQuery
from luigi.format import MixedUnicodeBytes
import requests

from jitenshop import config, iodb
from jitenshop.tasks import db

DATADIR = config["main"]["datadir"]
LYON_STATION_URL = config["lyon"]["station_url"]


class DownloadShapefile(luigi.Task):
    """Task to download a zip files which includes the shapefile

    Need the source: rdata or grandlyon and the layer name (i.e. typename).
    """

    @property
    def path(self):
        return os.path.join(
            DATADIR, "lyon", 'lyon-stations.zip'
        )

    @property
    def url(self):
        return LYON_STATION_URL

    def output(self):
        return luigi.LocalTarget(self.path, format=MixedUnicodeBytes)

    def run(self):
        with self.output().open('w') as fobj:
            resp = requests.get(self.url)
            resp.raise_for_status()
            fobj.write(resp.content)


class UnzipShapeFile(luigi.Task):
    """Task dedicated to unzip file

    To get trace that the task has be done, the task creates a text file with
    the same same of the input zip file with the '.done' suffix. This generated
    file contains the path of the zipfile and all extracted files.
    """

    @property
    def path(self):
        return os.path.join(DATADIR, "lyon", "lyon-stations.zip")

    def requires(self):
        return DownloadShapefile()

    def output(self):
        filepath = os.path.join(DATADIR, "lyon", "unzip.done")
        return luigi.LocalTarget(filepath)

    def run(self):
        with self.output().open('w') as fobj:
            fobj.write(
                "unzip {} stations at {}\n".format("lyon", datetime.now())
            )
            zip_ref = zipfile.ZipFile(self.path)
            fobj.write("\n".join(elt.filename for elt in zip_ref.filelist))
            fobj.write("\n")
            zip_ref.extractall(os.path.dirname(self.input().path))
            zip_ref.close()


class ShapefileIntoDB(luigi.Task):
    """Dump a shapefile into a table
    """

    @property
    def projection(self):
        return config["lyon"]["srid"]

    @property
    def typename(self):
        return config["lyon"]["typename"]

    def requires(self):
        return {
            "zip": UnzipShapeFile(),
            "schema": db.CreateSchema()
        }

    def output(self):
        filepath = '_'.join(
            ["task", "shp2pgsql", "to",
             "lyon", "raw_station", "proj", self.projection]
        )
        return luigi.LocalTarget(
            os.path.join(DATADIR, "lyon", filepath + '.txt')
        )

    def run(self):
        table = "lyon.raw_station"
        dirname = os.path.abspath(os.path.dirname(self.input()['zip'].path))
        shpfile = os.path.join(dirname, self.typename + '.shp')
        shp2args = iodb.shp2pgsql_args(self.projection, shpfile, table)
        psqlargs = iodb.psql_args()
        with self.output().open('w') as fobj:
            sh.psql(sh.shp2pgsql(shp2args), psqlargs)
            fobj.write("shp2pgsql {} at {}\n".format(shpfile, datetime.now()))
            fobj.write("Create lyon.raw_station\n")


class NormalizeStationTable(PostgresQuery):
    """
    """
    host = config['database']['host']
    database = config['database']['dbname']
    user = config['database']['user']
    port = config['database']['port']
    table = "station"
    password = config['database'].get('password')

    query = (
        "DROP TABLE IF EXISTS {schema}.{tablename}; "
        "CREATE TABLE {schema}.{tablename} ("
        "id varchar,"
        "name varchar(250),"
        "address varchar(500),"
        "city varchar(100),"
        "nb_stations int,"
        "geom geometry(POINT, 4326)"
        "); "
        "INSERT INTO {schema}.{tablename} "
        "SELECT {id} AS id, {name} AS name, "
        "{address} AS address, {city} AS city, "
        "{nb_stations}::int AS nb_stations, "
        "st_transform(st_force2D(geom), 4326) as geom "
        "FROM {schema}.{raw_tablename}"
        ";"
        )

    def requires(self):
        return ShapefileIntoDB()

    def run(self):
        connection = self.output().connect()
        cursor = connection.cursor()
        sql = self.query.format(
            schema=config["lyon"]["schema"],
            tablename=self.table,
            raw_tablename='raw_station',
            id=config["lyon"]['feature_id'],
            name=config["lyon"]['feature_name'],
            address=config["lyon"]['feature_address'],
            city=config["lyon"]['feature_city'],
            nb_stations=config["lyon"]['feature_nb_stations']
        )
        cursor.execute(sql)
        # Update marker table
        self.output().touch(connection)
        # commit and close connection
        connection.commit()
        connection.close()
