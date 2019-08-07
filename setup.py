# -*- coding: utf-8 -*-

import os
import setuptools

with open("README.md") as fobj:
    LONG_DESCRIPTION = fobj.read()

INSTALL_REQUIRES = [
    "luigi",
    "numpy",
    "pandas",
    "requests",
    "psycopg2-binary",
    'sqlalchemy',
    'lxml',
    'xgboost',
    'daiquiri',
    'Flask==1.0.2',
    'flask-restplus==0.12.1',
    'sh',
    'seaborn',
    'scikit-learn',
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
    extras_require={'dev': ['pytest', 'pytest-sugar', 'ipython', 'ipdb',
                            'jupyter', 'notebook']},

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
