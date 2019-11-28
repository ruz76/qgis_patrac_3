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

####Requirements
- [ubuntu:19.04 disco](https://hub.docker.com/_/ubuntu)
- [qgis (3.4.6+dfsg-1build1)](https://packages.ubuntu.com/disco/qgis)

- [grass (7.6.0-1)](https://packages.ubuntu.com/disco/grass)
- [grass-dev (7.0.3-1build1)](https://packages.ubuntu.com/disco/grass-dev)

- openjdk-8-jre (8u222-b10-1ubuntu1~19.04.1)
- java 1.8 ?
- python (3.7.3) _included in qgis
- requests _included in python3

####Docker setup

You can use the patrac file. Make it executable and run
as ./patrac --help for further instruction. On first setup just
use ./patrac --build-all

Otherwise, the docker configuration is as follows:

```bash
docker pull ubuntu:19.04
# at patrac_environment direcotry
docker build -t patrac_environment .
# at patrac_plugin direcotry
docker rmi patrac_devel:latest -f
docker build -t patrac_devel .

#enable docker to use yout xhost
#this a simplyfied and recles aproach, future imrpovement might be required
xhost +local:root

#run the container
docker run -it \
    --env="DISPLAY" \
    --env="QT_X11_NO_MITSHM=1" \
    --volume="/tmp/.X11-unix:/tmp/.X11-unix:rw" \
    -v /data:/data \
    patrac_devel \
    qgis
export containerId=$(docker ps -l -q)	

##once finished, limit acces to xhost
xhost -local:root

```
####Windows 10 installation:
TODO


####Remote Debug



###Encountered errors

```
An error has occurred while executing Python code:


Traceback (most recent call last):
  File "/usr/share/qgis/python/plugins/qgis_patrac/patracdockwidget.py", line 233, in runGuideMunicipalitySearch
    self.runCreateProjectGuide(municipalityindex)
  File "/usr/share/qgis/python/plugins/qgis_patrac/patracdockwidget.py", line 178, in runCreateProjectGuide
    self.Project.createProject(index)
  File "/usr/share/qgis/python/plugins/qgis_patrac/main/project.py", line 381, in createProject
    self.widget.Sectors.recalculateSectors(True)
  File "/usr/share/qgis/python/plugins/qgis_patrac/main/sectors.py", line 283, in recalculateSectors
    f.write(str(feature['id']) + u"\n")
KeyError: 'id'


Python version:
2.7.12 (default, Aug 22 2019, 16:36:40) 
[GCC 5.4.0 20160609]


QGIS version:
2.8.6-Wien Wien, exported

Python path: ['/usr/share/qgis/python/plugins/processing', '/usr/share/qgis/python', u'/root/.qgis2/python', u'/root/.qgis2/python/plugins', '/usr/share/qgis/python/plugins', '/usr/lib/python2.7', '/usr/lib/python2.7/plat-x86_64-linux-gnu', '/usr/lib/python2.7/lib-tk', '/usr/lib/python2.7/lib-old', '/usr/lib/python2.7/lib-dynload', '/usr/local/lib/python2.7/dist-packages', '/usr/lib/python2.7/dist-packages', '/usr/lib/python2.7/dist-packages/PILcompat', '/usr/lib/python2.7/dist-packages/gtk-2.0', '/usr/lib/python2.7/dist-packages/wx-3.0-gtk2', u'/root/.qgis2//python', '/usr/share/qgis/python/plugins/fTools/tools', '/data/patracdata/kraje/pl/projekty/plzen__plzen-mesto__2019-09-18_14-06-24']
```

ID missing.