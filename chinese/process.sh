#!/usr/bin/env bash

CON_STRING="dbname=patrac user=patrac password=patrac host=localhost port=5432"
CON_STRING_OGR="host=localhost user=patrac dbname=patrac password=patrac"
SECTORS_PATH=/data/patracdata/kraje/ka/vektor/ZABAGED/sectors.shp

WORKING_DIR=$1
IDS=`cat $WORKING_DIR/ids.txt`

ogr2ogr -overwrite -f "PostgreSQL" -s_srs "EPSG:5514" -t_srs "EPSG:4326" PG:"$CON_STRING_OGR" $SECTORS_PATH -sql "SELECT id FROM sectors WHERE id IN ($IDS)" -nln routing.sectors -lco GEOMETRY_NAME=geom
#echo "copy (select \"source\", target,length_m, gid, x1, y1, x2, y2 from routing.ways w join routing.sectors s on ST_Intersects(ST_Buffer(s.geom, 0.00005), w.the_geom)) to '/tmp/sector_lines.csv' CSV DELIMITER ',';" > /tmp/1.sql
echo "copy ( select \"source\", target,length_m, gid, x1, y1, x2, y2 from routing.ways w join routing.sectors s on ((ST_Intersects(ST_Buffer(s.geom, 0.00005), w.the_geom) AND (ST_Length(ST_Intersection(ST_Buffer(s.geom, 0.00010), w.the_geom)) / ST_Length(w.the_geom)) > 0.5)) OR (ST_Contains(ST_Buffer(s.geom, 0.00005), w.the_geom))) to '/tmp/sector_lines.csv' CSV DELIMITER ',';" > /tmp/1.sql
psql "$CON_STRING" -f /tmp/1.sql
echo "START_NODE,END_NODE,SEGMENT_LENGTH,SEGMENT_ID,START_NODE_LONGITUDE,START_NODE_LATITUDE,END_NODE_LONGITUDE,END_NODE_LATITITUDE" > $WORKING_DIR/$2.csv
cat /tmp/sector_lines.csv >> $WORKING_DIR/$2.csv
python3 /home/jencek/qgis3_profiles/profiles/default/python/plugins/qgis_patrac/chinese/remove_duplicate_edges.py $WORKING_DIR $2

# Extract first node as a starting one
sed -n '2 p' $WORKING_DIR/$2.csv | cut -d',' -f1 > $WORKING_DIR/$2_start.csv
#head -1 /tmp/sector_lines.csv | cut -d',' -f1 > $WORKING_DIR/$2_start.csv
#echo "3925" > $WORKING_DIR/$2_start.csv
cat $WORKING_DIR/$2_start.csv

echo "Starting CHINESE"
cd /home/jencek/Documents/Projekty/PCR/devel/chinese_postman/chinese-postman
python postman.py --csv $WORKING_DIR/$2_path.csv --gpx $WORKING_DIR/$2_path.gpx --start_node $WORKING_DIR/$2_start.csv $WORKING_DIR/$2.csv

tail +2 $WORKING_DIR/$2_path.csv | awk '{printf "%s,%s\n", NR,$0}'> /tmp/1_path.csv
echo "drop table if exists routing.path_lines CASCADE;" > 1.sql
# Start Node,End Node,Segment Length,Segment ID,Start Longitude,Start Latitude,End Longitude,End Latitude
#7368,6436,654.7960709582709,8415,12.1623058,50.2621057,12.1658758,50.2570492
echo "create table routing.path_lines (id INT, sn INT, en INT, sl FLOAT, sid INT, slon FLOAT, slat FLOAT, elon FLOAT, elat FLOAT);" >> 1.sql
echo "copy routing.path_lines from '/tmp/1_path.csv' DELIMITER ',' CSV;" >> 1.sql
echo "create view routing.path_lines_geom as select l.id, l.sid, l.sn, l.en, w.the_geom, t.ts::varchar, w.length_m length_m from routing.path_lines l join routing.ways w on (l.sid = w.gid) join routing.time_series t on (l.id = t.id);" >> 1.sql
psql "$CON_STRING" -f 1.sql
ogr2ogr -f "ESRI Shapefile" -s_srs "EPSG:4326" -t_srs "EPSG:5514" $WORKING_DIR/$2_path.shp PG:"$CON_STRING_OGR" "routing.path_lines_geom" -overwrite
#ogr2ogr -f "GPKG" -s_srs "EPSG:4326" -t_srs "EPSG:5514" $WORKING_DIR/$2_path.gpkg PG:"$CON_STRING_OGR" "routing.path_lines_geom" -overwrite
