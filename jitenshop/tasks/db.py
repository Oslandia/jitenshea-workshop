"""Luigi tasks dedicated to database management
"""


import luigi
from luigi.contrib.postgres import PostgresQuery

from jitenshop import config


class CreateSchema(PostgresQuery):
    """As this class inheritates from PostgresQuery, it must define host,
    database, user, password, schema and table attributes
    """
    host = config['database']['host']
    database = config['database']['dbname']
    user = config['database']['user']
    password = config['database'].get('password')
    schema = config["lyon"]["schema"]
    table = luigi.Parameter(default='create_schema')
    query = "CREATE SCHEMA IF NOT EXISTS {schema};"

    def run(self):
        connection = self.output().connect()
        cursor = connection.cursor()
        sql = self.query.format(schema=self.schema)
        cursor.execute(sql)
        # Update marker table
        self.output().touch(connection)
        # commit and close connection
        connection.commit()
        connection.close()
