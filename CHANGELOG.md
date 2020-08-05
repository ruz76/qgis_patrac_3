# Changelog 

## Version 3.12.14 (2020-08-09)

#### Improvements
* The user is informed about need to click into map when entering result
* The labels on/off now keeps the current colors symbology

#### Bug Fixes
* 24 Ukončeno bez nálezu
* 25 Chybí les v seznamu povrchů

## Version 3.12.13 (2020-07-23)

#### Improvements
* The list of tracks shows original name in brackets
* The list of tracks shows only 1 days old tracks (user has to ask for all tracks)

#### Bug Fixes
* 13 Load GPX on empty project
* 14 Set style on empty project
* 15 Step 2 on empty project
* 16 Read maxtime on empty project
* 17 Write maxtime on empty project
* 18 Recalculate sectors on empty project
* 19 Wrong statistic values
* 20 Empty GPX list - confirm
* 21 Ui_Message object has no attribute 'iface'
* 22 Can not read GPX with extensions

## Version 3.12.12 (2020-07-19)

#### Improvements
* Extended fix datastore function to download stats files
* Extended create incident to set hs users to onduty status 
* Added config file

#### Bug Fixes
* line 893, in showQrCode: AttributeError: 'Ui_Settings' object has no attribute 'searchID' 
* line 844, in accept: no file
* other parts where is missing searchID

## Version 3.12.11 (2020-07-12)

#### Improvements
* Added config files for data tests
* Added button for fixing datastore errors

## Version 3.12.10 (2020-07-08)

#### Improvements
* Changed GPX check, now it is faster
* Do not allow to close QGIS until the result is inserted
* Stats for sectors are now in sqlite database. Shoud be faster on Windows
* Added tests for Data

#### Bug Fixes

* Fixed bad GPX input

## Version 3.12.9 (2020-06-25)

#### Improvements
* Changed call handlers in two rounds
* Added check of result
* Removed not necessary toolbars
* Added distance of the users

#### Bug Fixes

* Fixed message utf8 bug #8
* Fixed bug with login into HS book
* Toolbar is missing

## Version 3.12.8 (2020-06-07)

#### Improvements

* Renamed button for recalculation (now is more clear)
* Extent area is now operational again

#### Bug Fixes

* Fixed utf8 on locations reading
* Fixed utf8 on tracks reading

## Version 3.12.7 (2020-05-26)

#### Improvements

* Show result as a new layer in the map
* Build more than 4 tiles of PDF when necessary
* Remove ascii exports
* Resend createsearch, archive search, close search requests 
in a case when there is not a network.

#### New Features

* Push result to storage server for archiving

#### Bug Fixes

* Result accept twice run
* Message not append a file to post
* HTTP reponse other than 200 is not handled
* Fixed basic test
* Fixed utf8 on unitsTime reading

## Version 3.12.6 (2020-05-15)

#### Improvements

* Moved strings into translation config files
* Translated into English

## Version 3.12.5 (2020-05-06)

#### Improvements

* Buffer only on features that are in sector.
* Activate progress tool on tab selection.
* Number of persons
* Copy doc into safe location.
* Updated image in doc.

#### Bug Fixes

* Message fix
* Exit on bad input
* Copy config
* Default value for number of persons

#### New Features

* Search track analyze for Krajnici
* Settings for speed of search

## Version 3.12.4 (2020-04-26)

#### Improvements

* Network operations moved to QThread
* Calculation on inside tracks only

#### Bug Fixes

* Metadata fix

#### New Features

* Search track analyze: 
    * Extended to another types of units 

## Version 3.12.3 (2020-04-14)

#### Bug Fixes

* Save settings into profile

#### New Features

* 4 maps in detailed scale
* Styles to template

## Version 3.12.2 (2020-04-05)

#### New Features

* Map based on recommended units 
* Smaller fonts
* Thinner grid
* Numeric scale
* New installer
* HS call
* Moved ZPM
