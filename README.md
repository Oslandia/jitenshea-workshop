# workshop-jitenshea

Light version of [Jitenshea](github.com/garaud/jitenshea) designed for presentations in workshops.

## Installation

Clone the repo on your computer:

```
$ git clone git@github.com:Oslandia/workshop-jitenshea.git
```

Install the Python dependencies:

```
$ cd workshop-jitenshea
$ virtualenv -p /usr/bin/python3 venv
$ source venv/bin/activate
(venv)$ python setup.py install
```

Install the javascript dependencies, we will use `yarn`. Let's install it on Debian/Ubuntu:

```
curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | sudo apt-key add -
echo "deb https://dl.yarnpkg.com/debian/ stable main" | sudo tee /etc/apt/sources.list.d/yarn.list
sudo apt-get update && sudo apt-get install yarn
yarn install
```

(See the `yarn` [installation procedure](https://yarnpkg.com/en/docs/install#debian-stable) for other platforms.)

This repo is made for `yarn==1.17.3`. Check your version with `yarn --version`.

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
