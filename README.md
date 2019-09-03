# workshop-jitenshea

Light version of [Jitenshea](github.com/garaud/jitenshea) designed for presentations in workshops.

Click for the [workshop document](./workshop.md)!

## Installation

### Ubuntu

Clone the repo on your computer:

```
$ git clone git@github.com:Oslandia/workshop-jitenshea.git
```

This project aims to run with Python3. Install the dependencies:

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

### Other

For other systems, you can install the project by the way of
a [VirtualBox 6.0](https://www.virtualbox.org/). VirtualBox is used to run a
Virtual Machine (VM) pre-installed with all the software necessary for this
workshop.

To create the workshop VM you need to import the virtual appliance
`workshop-jitenshea.ova` into VirtualBox. Go to
http://hekla.oslandia.net/workshop-jitenshea/, and download the
workshop-jitenshea.ova file (4.0 GBytes).

*Note:* please open an issue if the `workshop-jitenshea.ova` file is no longer
available on the server.

You can also download the `workshop-jitenshea.ova.md5` file and check that the
`workshop-jitenshea.ova` file hasn't been corrupted during download. On Linux
you can use the following command to verify the md5 sum:

```
md5sum -c workshop-jitenshea.ova.md5
```

Now launch the VirtualBox user interface and import the virtual appliance
`workshop-jitenshea.ova`. In the "Appliance settings" window make sure you give
enough RAM to the VM. 4096 MB should be enough, but the more RAM the
better.

With the appliance imported you are ready to start the virtual machine, so go
for it!

## Configuration

A configuration file sample can be found at `jitenshop/config.ini.sample`. Copy
it as `jitenshop/config.ini` and custom it regarding your system!

## Reset the database

As a starting step, the application database can be reset with the
`reset_db.sh` command:

```
chmod +x ./reset_db.sh
./reset_db.sh
```

This program:
- read the config file (so do not forget to define it!) to get the db
  connection parameters,
- remove the data folder content,
- drop the database if it exists then re-create it from scratch,
- add the PostGIS extension to it.

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

## Get the data for the workshop

Due to connexion hazards during the workshop, you may get the useful data
before to be in the workshop room. To get them, both commands will do the job:

```
python -m luigi --local-scheduler --module jitenshop.tasks.stations DownloadShapefile
python -m luigi --local-scheduler --module jitenshop.tasks.availability Availability --start 2019-08-12 --stop 2019-08-18
```

(respectively for the shared-bike stations and bike availability history)
