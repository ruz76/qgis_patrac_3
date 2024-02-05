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
