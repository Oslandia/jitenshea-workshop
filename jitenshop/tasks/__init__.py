"""
"""

from datetime import date, timedelta

def one_week_ago():
    """Return the date seven days before today
    """
    return date.today() - timedelta(7)
