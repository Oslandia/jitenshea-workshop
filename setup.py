# -*- coding: utf-8 -*-

import os
import setuptools

with open("README.md") as fobj:
    LONG_DESCRIPTION = fobj.read()

INSTALL_REQUIRES = [
    "luigi @ git+https://github.com/spotify/luigi",
    "numpy<=1.17.0",
    "pandas==0.25.0",
    "requests==2.22.0",
    "psycopg2-binary==2.8.3",
    'sqlalchemy<=1.3.6',
    'lxml==4.4.0',
    'daiquiri==1.6.0',
    'Flask==1.0.2',
    'flask-restplus==0.12.1',
    'sh==1.12.14',
    'matplotlib',
    'seaborn==0.9.0',
    'scikit-learn==0.21.3',
    'jupyter==1.0.0',
    'notebook==6.0.0',
    'folium==0.10.0',
    'fiona',
    'shapely',
    'tables'
]


def find_version(*file_paths):
    here = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(here, *file_paths), "r") as f:
        for line in f:
            if line.startswith("__version__"):
                return line.strip().split("=")[1].strip(" '\"")
    raise RuntimeError(
        ("Unable to find version string. " "Should be __init__.py.")
    )


setuptools.setup(
    name='jitenshop',
    version=find_version("jitenshop", "__init__.py"),
    license='BSD',
    url='https://git.oslandia.net/Oslandia-data/jitenshea-workshop',
    packages=setuptools.find_packages(),
    include_package_data=True,
    install_requires=INSTALL_REQUIRES,
    extras_require={'dev': [
        'pytest',
        'pytest-sugar',
        'ipython',
        'ipdb'
    ]},

    author="Raphaël Delhome",
    author_email='raphael.delhome@oslandia.com',
    description="Bicycle-sharing data analysis - light workshop version",
    long_description=LONG_DESCRIPTION,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ]
)
