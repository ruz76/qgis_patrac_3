from osgeo import ogr
import fiona

def run_query(query):
    # based on https://svn.osgeo.org/gdal/trunk/autotest/ogr/ogr_gpkg.py

    gpkg_ds = ogr.Open('/tmp/test.gpkg', update = 1)
    # gpkg_ds.ExecuteSQL('CREATE INDEX sectors_by_path_with_neighbors_agg_fld_id_idx ON sectors_by_path_with_neighbors_agg(id)')
    # gpkg_ds.ExecuteSQL('ALTER TABLE sectors_by_path_with_neighbors_agg_renamed RENAME TO sectors_by_path_with_neighbors_agg;')
    gpkg_ds.ExecuteSQL(query)
    gpkg_ds.ExecuteSQL('VACUUM')

    # gpkg_ds = ogr.Open('/tmp/test.gpkg', update = 1)
    # lyr = gpkg_ds.GetLayerByName('sectors_by_path_with_neighbors_agg')
    # if lyr is None:
    #     return 'fail'
    # lyr.SetAttributeFilter('id = 10')
    # if lyr.GetFeatureCount() != 1:
    #     return 'fail'
    #
    # return 'success'

def read_table(table_name):

    # No need to pass "layer='etc'" if there's only one layer
    with fiona.open('/tmp/test.gpkg', layer=table_name) as layer:
        for feature in layer:
            print(feature['properties']['id'])

def export_table(table_name, fields, output_path):
    with fiona.open('/tmp/test.gpkg', layer=table_name) as layer:
        with open(output_path, 'w') as out:
            for feature in layer:
                output_data = ''
                for field in fields:
                    output_data += str(feature['properties'][field]) + ','
                out.write(output_data[:-1] + '\n')

# sectors = '124, 683, 4251, 34964, 39918, 40058, 40059, 40066, 40102, 40243, 40403, 128, 160, 231, 645, 34975, 39919, 84, 94, 177, 3025, 3035, 3254, 3288, 3290, 3291, 3299, 4226, 4227, 4240, 4252, 4277, 4302, 4304, 4311, 4410, 4411, 4413, 4430, 4431, 4433, 4440, 4441, 28938, 34965, 40255, 101850, 101865, 109758, 109791, 109808, 109823, 109829, 109830, 109831, 109848, 109853, 109854, 109857, 110347, 110348, 110354, 110426, 110458, 110542, 110633, 110638, 110647, 170252, 179681, 752557, 768172, 235, 643, 922, 935, 4300, 4309, 34813, 34822, 34829, 34833, 34876, 34933, 34936, 34949, 34963, 39929, 40049, 40051, 40057, 40062, 40100, 40104, 126, 171062, 172626, 642, 897, 927, 2097, 34841, 172376, 172668, 768067, 123, 297, 902, 2356, 4261, 4310, 4412, 34838, 34839, 34842, 34879, 34900, 34976, 34977, 34989, 35101, 35154, 35195, 35207, 39798, 39965, 40060, 40441, 40443, 40444, 69953'
# 160 km
# Does not compute

# sectors = '3035, 3288, 3290, 4226, 4227, 4277, 4430, 4431, 4433, 4441, 109758, 110348, 235, 4300, 4309, 34963, 2097, 123, 2356'
# 24 km
# 1;5;handler;12373
# 0;5;pedestrian;11875

# sectors = '128, 84, 94, 177, 3025, 3035, 3254, 3288, 3290, 3299, 4226, 4227, 4277, 4301, 4302, 4304, 4410, 4430, 4431, 4433, 4440, 4441, 101850, 101865, 109758, 109791, 109848, 109853, 109854, 110347, 110348, 110354, 110426, 110430, 110434, 110458, 110500, 110542, 110633, 170252, 235, 4300, 4309, 34963, 126, 2097, 768067, 123, 2356'
# 46 km
# 0;5;handler;13706
# 1;5;pedestrian;14709
# 2;4;rider;17584

sectors = '128, 84, 94, 177, 3025, 3035, 3038, 3254, 3288, 3290, 3291, 3295, 3299, 4226, 4227, 4238, 4277, 4301, 4302, 4304, 4311, 4410, 4413, 4427, 4430, 4431, 4433, 4440, 4441, 28938, 40255, 101753, 101850, 101865, 109484, 109758, 109791, 109808, 109819, 109823, 109829, 109830, 109831, 109848, 109853, 109854, 109855, 109857, 110347, 110348, 110354, 110425, 110426, 110430, 110434, 110446, 110458, 110500, 110542, 110633, 110638, 110647, 170252, 179681, 752557, 768172, 235, 4300, 4309, 34963, 126, 2097, 768067, 123, 297, 2356, 4310, 39965, 40060, 40441'
# 70 km
# 1;5;handler;13990
# 3;5;pedestrian;15856
# 0;4;rider;19799
# 2;4;rider;20048

run_query('DELETE FROM sectors')
run_query('INSERT INTO sectors SELECT * FROM sectors_all WHERE id IN (' + sectors + ')')

# run_query('drop table if exists sectors_by_path_type')
# run_query('drop table if exists sectors_neighbors')
# run_query('drop table if exists sectors_neighbors_no_agg')
# run_query('drop table if exists sectors_with_pl')

# run_query("SELECT CreateSpatialIndex('sectors', 'geom')")
# run_query("SELECT CreateSpatialIndex('ways', 'the_geom')")

# This query takes to long, so we have to prepare the data on PostGIS and then only load results
# run_query('create table sectors_by_path_type as select s.id, s.label, round(sum(length_m)) length_m, w.grade from ways w join sectors s on ((ST_Intersects(ST_Buffer(s.geom, 0.00005), w.the_geom) AND (ST_Length(ST_Intersection(ST_Buffer(s.geom, 0.00010), w.the_geom)) / ST_Length(w.the_geom)) > 0.5)) OR (ST_Contains(ST_Buffer(s.geom, 0.00005), w.the_geom)) group by s.id, s.label, w.grade order by grade desc, length_m desc')

# read_table('sectors_by_path_with_neighbors_agg_export')
run_query('delete from sectors_by_path_with_neighbors_agg_export')
run_query("insert into sectors_by_path_with_neighbors_agg_export (id, type_5_length_m) select id, type_5_length_m from sectors_by_path_with_neighbors_agg WHERE id IN (" + sectors + ") order by type_5_length_m desc")
export_table('sectors_by_path_with_neighbors_agg_export', ['id', 'type_5_length_m'], '/tmp/sectors_by_path_with_neighbors_agg.csv')

run_query('delete from sum_length_export')
run_query("insert into sum_length_export (sum_length_m) select round(sum(length_m) / 1000) sum_length_m from sectors_by_path_type WHERE id IN (" + sectors + ")")
export_table('sum_length_export', ['sum_length_m'], '/tmp/sum_length.csv')

run_query('delete from sectors_with_paths_lengths_export')
run_query("insert into sectors_with_paths_lengths_export (id, length_m, x, y) select sp.id, length_m, ST_X(ST_Centroid(s.geom)) x, ST_Y(ST_Centroid(s.geom)) y from sectors_with_pl sp join sectors s on (s.id IN (" + sectors + ") AND s.id = sp.id)")
export_table('sectors_with_paths_lengths_export', ['id', 'length_m', 'x', 'y'], '/tmp/sectors_with_paths_lengths.csv')

run_query('delete from sectors_neighbors_export')
run_query("insert into sectors_neighbors_export (id, string_agg) select id, string_agg from sectors_neighbors WHERE id IN (" + sectors + ")")
export_table('sectors_neighbors_export', ['id', 'string_agg'], '/tmp/sectors_neighbors.csv')

run_query('delete from sectors_envelope_export')
run_query("insert into sectors_envelope_export (minx, miny, maxx, maxy) select MIN(ST_MinX(geom)) AS min_x, MIN(ST_MinY(geom)) AS min_y, MAX(ST_MaxX(geom)) AS max_x, MAX(ST_MaxY(geom)) AS max_y FROM sectors")
export_table('sectors_envelope_export', ['minx', 'miny', 'maxx', 'maxx'], '/tmp/sectors_envelope.csv')
