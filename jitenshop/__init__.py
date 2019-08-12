__version__ = 0.1

import os
import logging
import configparser

import daiquiri
import daiquiri.formatter


_ROOT = os.path.dirname(os.path.abspath(__file__))
_CONFIG = os.path.join(_ROOT, 'config.ini')


FORMAT = (
    "%(asctime)s :: %(color)s%(levelname)s :: %(name)s :: %(funcName)s :"
    "%(message)s%(color_stop)s"
    )
daiquiri.setup(level=logging.INFO, outputs=(
    daiquiri.output.Stream(formatter=daiquiri.formatter.ColorFormatter(
        fmt=FORMAT)),
    ))
logger = daiquiri.getLogger("root")


if not os.path.isfile(_CONFIG):
    logger.error("Configuration file '%s' not found", _CONFIG)
    config = None
else:
    config = configparser.ConfigParser(allow_no_value=True)
    with open(_CONFIG) as fobj:
        config.read_file(fobj)
