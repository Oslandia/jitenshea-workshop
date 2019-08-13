"""Jitenshop webapp init module
"""

from datetime import datetime, date

from flask.json import JSONEncoder
from werkzeug.routing import BaseConverter


ISO_DATE = '%Y-%m-%d'
ISO_DATETIME = '%Y-%m-%dT%H:%M:%S'


class CustomJSONEncoder(JSONEncoder):
    """Custom JSON encoder to handle date
    """
    def default(self, obj):
        try:
            if isinstance(obj, datetime):
                return obj.strftime(ISO_DATETIME)
            if isinstance(obj, date):
                return obj.strftime(ISO_DATE)
            iterable = iter(obj)
        except TypeError:
            pass
        else:
            return list(iterable)
        return JSONEncoder.default(self, obj)


class ListConverter(BaseConverter):
    """URL <-> Python converter for a list of elements seperated by a ','

    Example URL/user/john,mary to get the john resource and mary resource
    Inspired from
    http://exploreflask.com/en/latest/views.html#custom-converters
    """
    def to_python(self, value):
        return value.split(',')

    def to_url(self, values):
        return ','.join(
            BaseConverter.to_url(value) for value in values
        )
