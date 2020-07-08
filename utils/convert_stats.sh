#!/usr/bin/env bash

for KRAJ in jc jm ka kh lb ms ol pa pl st us vy zl
do
  rm -r /tmp/stats/
  mkdir /tmp/stats/
  cp /media/jencek/Seagate\ Backup\ Plus\ Drive/data/patracdata/kraje/$KRAJ/vektor/ZABAGED/line_x/all_stats.zip /tmp/stats/
  cd /tmp/stats/
  unzip -q all_stats.zip
  python3 /home/jencek/qgis3_profiles/profiles/default/python/plugins/qgis_patrac/utils/convert_stats.py
  cp /tmp/stats/stats.db /media/jencek/Seagate\ Backup\ Plus\ Drive/data/patracdata/kraje/$KRAJ/vektor/ZABAGED/line_x/
done
