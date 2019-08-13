"""Main task module, that contain the pipeline final task
"""

from datetime import date

import luigi

from jitenshop.tasks import one_week_ago
from jitenshop.tasks.clusters import StoreClustersToDatabase
from jitenshop.tasks.clusters import StoreCentroidsToDatabase
from jitenshop.tasks.stations import NormalizeStationTable


class Finalize(luigi.Task):
    """Program master task

    Requires to run the clustering and to store its outputs in the database, as
    well as to store a normalized version of the city stations

    """
    n_clusters = luigi.IntParameter(default=4)
    start = luigi.DateParameter(default=one_week_ago())
    stop = luigi.DateParameter(default=date.today())

    def requires(self):
        yield StoreClustersToDatabase(self.n_clusters, self.start, self.stop)
        yield StoreCentroidsToDatabase(self.n_clusters, self.start, self.stop)
        yield NormalizeStationTable()
