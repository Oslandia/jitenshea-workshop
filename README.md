# workshop-jitenshea

Light version of [Jitenshea](github.com/garaud/jitenshea) designed for presentations in workshops.

## Installation

Clone the repo on your computer:

```
$ git clone git@github.com:Oslandia/workshop-jitenshea.git
```

Install the Python dependencies:

```
$ cd jitenshop
$ virtualenv -p /usr/bin/python3 venv
$ source venv/bin/activate
(venv)$ python setup.py install
```

Install the javascript dependencies:

```
yarn install
```

## Configuration

A configuration file sample can be found at `jitenshop/config.ini.sample`. Copy
it as `jitenshop/config.ini` and custom it regarding your system!

## Work on the project notebooks

Everything is in the `examples` folder!

```
cd examples
jupyter notebook
```

## Open Data

During the workshop, one will work with data from Lyon, France.

You can visit
the [Lyon Open Data portal](https://data.beta.grandlyon.com/en/accueil) by
curiosity, or directly focus on
the
[bike-sharing system data](https://download.data.grandlyon.com/catalogue/srv/eng/catalog.search#/metadata/9bc6806d-e8a0-463b-aaa1-4364a75e44d7).
