# Based on Ralph Kistner code

## Selecting tracks based on OSM
https://wiki.openstreetmap.org/wiki/Key:tracktype
* if highway == 'track' then use tracktype
* if tracktype == 'grade1' then all 
* if tracktype == 'grade2' then all
* if tracktype == 'grade3' then all
* if tracktype == 'grade4' then dog
* if tracktype == 'grade5' then dog

* if highway != 'track' then use surface or directly highway

## Flow

The flow should be now in process.py

* In expects on input the list of sectors identifiers and list of available search teams
* The data should be prepared in GPKG file with all necessary inputs prepared with PostGIS, since the computing takes too long in GPKG
* The sectors are clustered into several clusters based on available and necessary search teams
* If the number of available search teams is smaller than necessary number then some clusters are not covered
* If the number of available search teams is bigger than necessary number then some teams are not used (we may think about some usage, but maybe is better to use them directly for area search)
* For each search team is calculated chinesse path
* As an output is for each search team available statistics (total length of paths to search, total length to go (some paths has to be followed more than once)) and path in a form of coordinates
* The output for now is not completely clear, but there may be some options how to specify it
