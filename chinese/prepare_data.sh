CON_STRING="dbname=patrac user=patrac password=patrac host=localhost port=5432"
CON_STRING_OGR="host=localhost user=patrac dbname=patrac password=patrac"

#drop table if exists routing.sectors_by_path_type;
#drop table if exists routing.sectors_neighbors;
#drop table if exists routing.sectors_neighbors_no_agg;
#drop table if exists routing.sectors_with_paths_lengths;
#drop table if exists routing.sectors_by_path_type_5;
#drop table if exists routing.sectors_by_path_type_0_4;
#drop table if exists routing.sectors_by_path_with_neighbors_agg;
#drop table if exists routing.sectors_by_path_with_neighbors_agg_export;
#drop table if exists routing.sum_length_export;
#drop table if exists routing.sectors_with_paths_lengths_export;
#drop table if exists routing.sectors_neighbors_export;
#drop table if exists routing.sectors_envelope_export;
#drop table if exists routing.ways_for_sectors;
#drop table if exists routing.ways_for_sectors_export;
#drop table if exists routing.chpostman_path;
#drop table if exists routing.chpostman_path_export;
#
#create table routing.sectors_by_path_type as select s.id, s.label, round(sum(length_m)) length_m, w.grade from routing.ways w join routing.sectors s on ((ST_Intersects(ST_Buffer(s.geom, 0.00005), w.the_geom) AND (ST_Length(ST_Intersection(ST_Buffer(s.geom, 0.00010), w.the_geom)) / ST_Length(w.the_geom)) > 0.5)) OR (ST_Contains(ST_Buffer(s.geom, 0.00005), w.the_geom)) group by s.id, s.label, w.grade order by grade desc, length_m desc;
#create table routing.sectors_neighbors as select s1.id id, string_agg(s2.id::varchar, ';') from routing.sectors s1 join routing.sectors s2 on (s1.id <> s2.id and (ST_Touches(s1.geom, s2.geom) or ST_Intersects(s1.geom, s2.geom))) group by s1.id order by s1.id;
#create table routing.sectors_neighbors_no_agg as select s1.id id, s2.id id2 from routing.sectors s1 join routing.sectors s2 on (ST_Touches(s1.geom, s2.geom) or ST_Equals(s1.geom, s2.geom)) order by s1.id;
#create table routing.sectors_by_path_type_5 as select s.id, s.label, round(sum(length_m)) length_m from routing.ways w join routing.sectors s on ((w.grade = 5) AND (ST_Intersects(ST_Buffer(s.geom, 0.00005), w.the_geom) AND (ST_Length(ST_Intersection(ST_Buffer(s.geom, 0.00010), w.the_geom)) / ST_Length(w.the_geom)) > 0.5)) OR (ST_Contains(ST_Buffer(s.geom, 0.00005), w.the_geom)) group by s.id order by length_m desc;
#create table routing.sectors_by_path_type_0_4 as select s.id, s.label, round(sum(length_m)) length_m from routing.ways w join routing.sectors s on ((w.grade < 5) AND (ST_Intersects(ST_Buffer(s.geom, 0.00005), w.the_geom) AND (ST_Length(ST_Intersection(ST_Buffer(s.geom, 0.00010), w.the_geom)) / ST_Length(w.the_geom)) > 0.5)) OR (ST_Contains(ST_Buffer(s.geom, 0.00005), w.the_geom)) group by s.id order by length_m desc;
#alter table routing.sectors_neighbors_no_agg add column type_5_length_m int;
#update routing.sectors_neighbors_no_agg n set type_5_length_m = s.length_m from routing.sectors_by_path_type_5 s where n.id2 = s.id;
#alter table routing.sectors_neighbors_no_agg add column type_0_4_length_m int;
#update routing.sectors_neighbors_no_agg n set type_0_4_length_m = s.length_m from routing.sectors_by_path_type_0_4 s where n.id2 = s.id;
#update routing.sectors_neighbors_no_agg n set type_0_4_length_m = 0 where type_0_4_length_m is null;
#update routing.sectors_neighbors_no_agg n set type_5_length_m = 0 where type_5_length_m is null;
#create table routing.sectors_by_path_with_neighbors_agg as select id, sum(type_5_length_m) type_5_length_m, sum(type_0_4_length_m) type_0_4_length_m from routing.sectors_neighbors_no_agg group by id;
#alter table routing.sectors_by_path_with_neighbors_agg add column geom Geometry(MultiPolygon, 4326);
#update routing.sectors_by_path_with_neighbors_agg a set geom = s.geom from routing.sectors_export_ka s where a.id = s.id;
#create table routing.sectors_with_pl as select s.id, round(sum(length_m)) length_m from routing.ways w right join routing.sectors s on ((ST_Intersects(ST_Buffer(s.geom, 0.00005), w.the_geom) AND (ST_Length(ST_Intersection(ST_Buffer(s.geom, 0.00010), w.the_geom)) / ST_Length(w.the_geom)) > 0.5)) OR (ST_Contains(ST_Buffer(s.geom, 0.00005), w.the_geom)) group by s.id;
#update routing.sectors_with_pl set length_m = 0 where length_m is null;
#
#create table routing.sectors_by_path_with_neighbors_agg_export as select id, type_5_length_m from routing.sectors_by_path_with_neighbors_agg order by type_5_length_m desc;
#create table routing.sum_length_export as select sum(length_m) sum_length_m from routing.sectors_by_path_type;
#create table routing.sectors_with_paths_lengths_export as select sp.id, length_m, ST_X(ST_Centroid(s.geom)) x, ST_Y(ST_Centroid(s.geom)) y from routing.sectors_with_paths_lengths sp join routing.sectors s on (s.id = sp.id);
#create table routing.sectors_neighbors_export as select * from routing.sectors_neighbors;
#create table routing.sectors_envelope_export as select st_xmin(st_Envelope(St_union(geom))) minx, st_ymin(st_Envelope(St_union(geom))) miny, st_xmax(st_Envelope(St_union(geom))) maxx, st_ymax(st_Envelope(St_union(geom))) maxy from routing.sectors;
#create table routing.ways_for_sectors as select s.id id, w.gid gid from routing.ways w join routing.sectors s on ((ST_Intersects(ST_Buffer(s.geom, 0.00005), w.the_geom) AND (ST_Length(ST_Intersection(ST_Buffer(s.geom, 0.00010), w.the_geom)) / ST_Length(w.the_geom)) > 0.5)) OR (ST_Contains(ST_Buffer(s.geom, 0.00005), w.the_geom));
#create table routing.ways_for_sectors_export as select "source", target,length_m, gid, x1, y1, x2, y2 from routing.ways limit 1;
#create table routing.chpostman_path as select gid, '1' ord, '2024-01-01 00:00:00' ts from routing.ways limit 1;
#create table routing.chpostman_path_export as select gid, '1' ord, '2024-01-01 00:00:00' ts, the_geom from routing.ways limit 1;

ogr2ogr -overwrite -f "GPKG" /tmp/test.gpkg PG:"$CON_STRING_OGR" "routing.sectors" -nln sectors
ogr2ogr -overwrite -f "GPKG" /tmp/test.gpkg PG:"$CON_STRING_OGR" "routing.sectors" -nln sectors_all
ogr2ogr -overwrite -f "GPKG" /tmp/test.gpkg PG:"$CON_STRING_OGR" "routing.ways" -nln ways
ogr2ogr -overwrite -f "GPKG" /tmp/test.gpkg PG:"$CON_STRING_OGR" "routing.sectors_by_path_type" -nln sectors_by_path_type
ogr2ogr -overwrite -f "GPKG" /tmp/test.gpkg PG:"$CON_STRING_OGR" "routing.sectors_neighbors" -nln sectors_neighbors
ogr2ogr -overwrite -f "GPKG" /tmp/test.gpkg PG:"$CON_STRING_OGR" "routing.sectors_neighbors_no_agg" -nln sectors_neighbors_no_agg
ogr2ogr -overwrite -f "GPKG" /tmp/test.gpkg PG:"$CON_STRING_OGR" "routing.sectors_with_pl" -nln sectors_with_pl
ogr2ogr -overwrite -f "GPKG" /tmp/test.gpkg PG:"$CON_STRING_OGR" "routing.sectors_by_path_type_5" -nln sectors_by_path_type_5
ogr2ogr -overwrite -f "GPKG" /tmp/test.gpkg PG:"$CON_STRING_OGR" "routing.sectors_by_path_type_0_4" -nln sectors_by_path_type_0_4
ogr2ogr -overwrite -f "GPKG" /tmp/test.gpkg PG:"$CON_STRING_OGR" "routing.sectors_by_path_with_neighbors_agg" -nln sectors_by_path_with_neighbors_agg
ogr2ogr -overwrite -f "GPKG" /tmp/test.gpkg PG:"$CON_STRING_OGR" "routing.ways_for_sectors" -nln ways_for_sectors

ogr2ogr -overwrite -f "GPKG" /tmp/test.gpkg PG:"$CON_STRING_OGR" "routing.sectors_by_path_with_neighbors_agg_export" -nln sectors_by_path_with_neighbors_agg_export
ogr2ogr -overwrite -f "GPKG" /tmp/test.gpkg PG:"$CON_STRING_OGR" "routing.sum_length_export" -nln sum_length_export
ogr2ogr -overwrite -f "GPKG" /tmp/test.gpkg PG:"$CON_STRING_OGR" "routing.sectors_with_paths_lengths_export" -nln sectors_with_paths_lengths_export
ogr2ogr -overwrite -f "GPKG" /tmp/test.gpkg PG:"$CON_STRING_OGR" "routing.sectors_neighbors_export" -nln sectors_neighbors_export
ogr2ogr -overwrite -f "GPKG" /tmp/test.gpkg PG:"$CON_STRING_OGR" "routing.sectors_envelope_export" -nln sectors_envelope_export
ogr2ogr -overwrite -f "GPKG" /tmp/test.gpkg PG:"$CON_STRING_OGR" "routing.ways_for_sectors_export" -nln ways_for_sectors_export
ogr2ogr -overwrite -f "GPKG" /tmp/test.gpkg PG:"$CON_STRING_OGR" "routing.chpostman_path" -nln chpostman_path
ogr2ogr -overwrite -f "GPKG" /tmp/test.gpkg PG:"$CON_STRING_OGR" "routing.chpostman_path_export" -nln chpostman_path_export

#ogr2ogr -overwrite -f "GPKG" /tmp/test.gpkg PG:"$CON_STRING_OGR" -sql "select id, type_5_length_m from routing.sectors_by_path_with_neighbors_agg order by type_5_length_m desc" -nln sectors_by_path_with_neighbors_agg
#ogr2ogr -overwrite -f "GPKG" /tmp/test.gpkg PG:"$CON_STRING_OGR" -sql "select sp.id, length_m, ST_X(ST_Centroid(s.geom)), ST_Y(ST_Centroid(s.geom)) from routing.sectors_with_paths_lengths sp join routing.sectors_export_ka s on (s.id = sp.id)" -nln sectors_with_paths_lengths
