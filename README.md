# QGIS Patrac 3

## Support
Výstupy vznikly v rámci projektu číslo VI20172020088 „Využití vyspělých technologií a čichových schopností psů pro zvýšení efektivity vyhledávání pohřešovaných osob v terénu“ 
(dále jen „projekt Pátrač“), který byl řešen v období 2017 až 2021 
s finanční podporou Ministerstva vnitra ČR z programu bezpečnostního výzkumu.

## Install
The install process is described at http://sarops.info/patrac/qgis3/install/index.html

## Use
The user manual is described at http://sarops.info/patrac/qgis3/install/index.html

## Data
The data that are from 2024 year available to download via Patrac are based on ZABAGED®
Data ZABAGED® area published by Zeměměřický úřad without fee as an open data, licenced by Creative Commons CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/deed.cs).
The layers cesta, lespru and vodtok are original data with removed some attributes.
The layer sectors is based on all polygon and line layers from ZABAGED®. The data has been processed in these steps:
* All polygon and line layers has been merged together as lines.
* This spaghetti model has been polygonized.
* The resulting polygons has been merged together to form search sectors of size 10-20 hectares to cover only one type of landuse.

## Development
Patrac is a plugin for the geographic information system application (QGIS). 
It is used to determinenate probability of finding a missing person in various
locations near the place of his or her last sighting. 
It determines sectors for the search and enables map printing and GPX export. 

Based on rastertransparency plugin.

Project repo [git repo](https://github.com/ruz76/qgis_patrac_3).

old project [git repo](https://github.com/ruz76/qgis_patrac/).

#### Windows 10 installation:
[See install manual](http://sarops.info/patrac/qgis3/install/)

#### User manual
The manual is part of the repository. It should be same as 
[User manual](http://sarops.info/patrac/qgis3/user/)
