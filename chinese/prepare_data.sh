CON_STRING="dbname=patrac user=patrac password=patrac host=localhost port=5432"
CON_STRING_OGR="host=localhost user=patrac dbname=patrac password=patrac"


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

#ogr2ogr -overwrite -f "GPKG" /tmp/test.gpkg PG:"$CON_STRING_OGR" -sql "select id, type_5_length_m from routing.sectors_by_path_with_neighbors_agg order by type_5_length_m desc" -nln sectors_by_path_with_neighbors_agg
#ogr2ogr -overwrite -f "GPKG" /tmp/test.gpkg PG:"$CON_STRING_OGR" -sql "select sp.id, length_m, ST_X(ST_Centroid(s.geom)), ST_Y(ST_Centroid(s.geom)) from routing.sectors_with_paths_lengths sp join routing.sectors_export_ka s on (s.id = sp.id)" -nln sectors_with_paths_lengths
