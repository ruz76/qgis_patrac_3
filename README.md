# QGIS Patrac 3

## Support
Výstupy vznikly v rámci projektu číslo VI20172020088 „Využití vyspělých technologií a čichových schopností psů pro zvýšení efektivity vyhledávání pohřešovaných osob v terénu“ 
(dále jen „projekt Pátrač“), který byl řešen v období 2017 až 2021 
s finanční podporou Ministerstva vnitra ČR z programu bezpečnostního výzkumu.

## Install
The install process is described at http://sarops.info/patrac/qgis3/install/index.html

## Use
The user manual is described at http://sarops.info/patrac/qgis3/install/index.html

## Development
Patrac is a plugin for the geographic information system application (QGIS). 
It is used to determinenate probability of finding a missing person in various
locations near the place of his or her last sighting. 
It determines sectors for the search and enables map printing and GPX export. 

Based on rastertransparency plugin.

Project repo [git repo](https://github.com/ruz76/qgis_patrac_3).

old project [git repo](https://github.com/ruz76/qgis_patrac/).

The [install data](http://gisak.vsb.cz/patrac/qgis/install.zip) archive contains test data for the Pilsner region. Tested for the Žihle municipality.

#### Requirements
- [ubuntu:19.04 disco](https://hub.docker.com/_/ubuntu)
change to 20.04
- [qgis (3.4.6+dfsg-1build1)](https://packages.ubuntu.com/disco/qgis)
chang to qgis (3.10.4+dfsg-1ubuntu2) https://packages.ubuntu.com/focal/qgis
- [grass (7.6.0-1)](https://packages.ubuntu.com/disco/grass)
- [grass-dev (7.0.3-1build1)](https://packages.ubuntu.com/disco/grass-dev)
- openjdk-8-jre (8u222-b10-1ubuntu1~19.04.1)
- python (3.7.3) _included in qgis
- requests _included in python3

#### Docker setup

You can use the patrac file. Make it executable and run
as ./patrac --help for further instruction. On first setup just
use ./patrac --build-all

Otherwise, the docker configuration is as follows:

```bash
TODO
```
#### Windows 10 installation:
You need data instalation drive. If you do not have any, contact support, please. 
[See install manual](http://sarops.info/patrac/qgis3/install/)

#### User manual
The manual is part of the repository. It should be same as 
[User manual](http://sarops.info/patrac/qgis3/user/)


#### Remote Debug
The `RemoteDebugger` class handles debugging. It might prove a slight challenge, to debug python programs executed using the
shell and bash scripts. But we can look into that later. The so-far the debugger works as follows:

- we use the `pydevd` library for debugging
- to remote debug one must first run the python debugger from ide listening on localhost:10999 *(The port is chosen at random.)*
- it's important to set the correct path mapping - this is ide specific
(something like /home/krystof/Projects/qgis_patrac_3=/usr/share/qgis/python/plugins/qgis_patrac)
- ai. *the path on the host machine to the plugin files* = *the path to the plugin files in the container*
- the open port 10999 on host must be accessible from the container
- a simple solution for this is to run the container with the `--net=host option` 
- once the debugger is running, one can start the debugger by calling the method 
`RemoteDebugger.setup_remote_pydev_debug('localhost',10999)` from the patrac script
- idealy have it be the first line of the PatracPlugin classes constructor in the patrac.py file

#### Restarting stoped container
xhost + && docker start patrac -a

#### Commit existing container
docker commit patrac patrac_devel:tag
