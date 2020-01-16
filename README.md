QGis Patrac 3
------
Patrac is a plugin for the geographic information system application (qgis). 
It is used to determinenethe probability of finding a missing person in various
locations near the place of his or hers last sighting. 
It determines sectors for the search and enables map printing and GPX export. 

Based on rastertransparency plugin.

Project repo [git repo](https://github.com/ruz76/qgis_patrac_3).

old project [git repo](https://github.com/ruz76/qgis_patrac/).

The [install data](http://gisak.vsb.cz/patrac/qgis/install.zip) archive contains test data for the Pilsner region. Tested for the Žihle municipality.

#### Requirements
- [ubuntu:19.04 disco](https://hub.docker.com/_/ubuntu)
- [qgis (3.4.6+dfsg-1build1)](https://packages.ubuntu.com/disco/qgis)
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
TODO


#### Remote Debug