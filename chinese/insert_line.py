import fiona
from shapely.geometry import shape
from shapely.ops import linemerge
from shapely.ops import split
from shapely.geometry import mapping
from shapely.affinity import scale
from shapely.affinity import rotate
from shapely.affinity import translate
from shapely.geometry import LineString
import json
from osgeo import ogr

def array_to_in_param(arr, quotes=False):
    output = ''
    for item in arr:
        if quotes:
            output += "'" + str(item) + "', "
        else:
            output += str(item) + ', '
    return output[:-2]

def run_query(gpkg_path, query):
    # based on https://svn.osgeo.org/gdal/trunk/autotest/ogr/ogr_gpkg.py

    gpkg_ds = ogr.Open(gpkg_path, update=1)
    gpkg_ds.ExecuteSQL(query)
    gpkg_ds.ExecuteSQL('VACUUM')

def print_features(features):
    data = {
        "type": "FeatureCollection",
        "features": features
    }
    print(json.dumps(data))

def copy_feature(feature):
    feature_output = {
        "type": "Feature",
        "properties": {},
        "geometry": feature["geometry"]
    }
    for field in feature["properties"]:
        feature_output['properties'][field] = feature['properties'][field]
    return feature_output

def get_last_id(source, layer_name):
    last_id = -1
    with fiona.open(source, layer=layer_name) as layer:
        for feature in layer:
            if int(feature['id']) > last_id:
                last_id = int(feature['id'])
    return last_id

def append_features(features, target, layer):
    with fiona.open(target, "a", layer=layer) as dst:
        print(len(dst))
        for feature in features:
            print(feature['properties']["gid"])
            dst.write(
                {
                    "geometry": feature["geometry"],
                    "properties": {
                        'rule': feature["properties"]["rule"],
                        'x1': feature["properties"]["x1"],
                        'y1': feature["properties"]["y1"],
                        'maxspeed_forward': feature["properties"]["maxspeed_forward"],
                        'cost_s': feature["properties"]["cost_s"],
                        'maxspeed_backward': feature["properties"]["maxspeed_backward"],
                        'oneway': feature["properties"]["oneway"],
                        'length_m': feature["properties"]["length_m"],
                        'target_osm': feature["properties"]["target_osm"],
                        'source': feature["properties"]["source"],
                        'reverse_cost_s': feature["properties"]["reverse_cost_s"],
                        'tag_id': feature["properties"]["tag_id"],
                        'osm_id': feature["properties"]["osm_id"],
                        'length': feature["properties"]["length"],
                        'reverse_cost': feature["properties"]["reverse_cost"],
                        'grade': feature["properties"]["grade"],
                        'source_osm': feature["properties"]["source_osm"],
                        'cost': feature["properties"]["cost"],
                        'name': feature["properties"]["name"],
                        'x2': feature["properties"]["x2"],
                        'y2': feature["properties"]["y2"],
                        'target': feature["properties"]["target"],
                        'priority': feature["properties"]["priority"],
                        'one_way': feature["properties"]["one_way"]
                    }
                }
            )
        print(len(dst))

def append_line():

    working_dir = '/home/jencek/Documents/Projekty/PCR/test_data_eustach'
    id_point = 1000000
    last_way_id = get_last_id(working_dir + '/' + 'test.gpkg', 'ways')
    id_line = last_way_id + 1
    ways_layer = 'ways'
    draw_lines_layer = 'drawn_lines'
    ids_to_delete = []

    new_features = []
    with fiona.open(working_dir + '/' + 'test.gpkg', layer=ways_layer) as layer:
        with fiona.open(working_dir + '/' + 'test.gpkg', layer=draw_lines_layer) as drawn_lines:
            lines_for_split = []
            points_ids = []
            for drawn_line in drawn_lines:
                geom_drawn_line = shape(drawn_line["geometry"])
                for feature in layer:
                    geom = shape(feature["geometry"])
                    # Simply using ratio between length and length_m for PoC
                    if geom.intersects(geom_drawn_line):
                        lines_for_split.append(geom)
                        print(feature['id'])
                        ids_to_delete.append(feature['id'])
                        lengths_ratio = feature['properties']['length_m'] / feature['properties']['length']
                        # print(feature['properties']['osm_id'])
                        # cross_point = geom.intersection(geom_drawn_line)
                        # print(cross_point)
                        first_point_geom = geom.coords[:1]
                        collection = split(geom, geom_drawn_line)
                        for line in collection:
                            # print(line.coords[:1])
                            # print(first_point_geom)
                            new_line = copy_feature(feature)
                            new_line['properties']['gid'] = id_line
                            new_line['properties']['length'] = line.length
                            new_line['properties']['length_m'] = line.length * lengths_ratio
                            new_line['geometry'] = mapping(line)
                            if line.coords[:1] == first_point_geom:
                                # print("Yes")
                                new_line['properties']['target'] = id_point
                            else:
                                new_line['properties']['source'] = id_point
                            new_features.append(new_line)
                            id_line += 1
                        points_ids.append(id_point)
                        id_point += 1
                    else:
                        # Simply add this not crossing line into collection
                        # This will work only in a case of one drawn line
                        # current_line = copy_feature(feature)
                        # current_line['geometry'] = mapping(geom)
                        # new_features.append(current_line)
                        a = 1 # Just a placeholder

                # Line is crossing on two places
                # Just PoC - DRY later
                if len(lines_for_split) == 2:
                    collection = split(geom_drawn_line, lines_for_split[0])
                    longest_part = None
                    longest_length = -1
                    for line in collection:
                        if line.length > longest_length:
                            longest_part = line
                            longest_length = line.length
                    collection = split(longest_part, lines_for_split[1])
                    longest_part = None
                    longest_length = -1
                    for line in collection:
                        if line.length > longest_length:
                            longest_part = line
                            longest_length = line.length
                    new_line = copy_feature(feature)
                    new_line['properties']['gid'] = id_line
                    new_line['properties']['length'] = longest_part.length
                    new_line['properties']['length_m'] = longest_part.length * lengths_ratio
                    new_line['geometry'] = mapping(longest_part)
                    # TODO check line direction
                    new_line['properties']['source'] = points_ids[0]
                    new_line['properties']['target'] = points_ids[1]
                    new_features.append(new_line)
                    id_line += 1

    # print_features(new_features)
    # print(json.dumps(new_features, indent=4))
    append_features(new_features, working_dir + '/' + 'test.gpkg', ways_layer)

    # TODO select right sectors based on geometry not on previous sectors
    # (ST_Intersects(ST_Buffer(s.geom, 0.00005), w.the_geom) AND (ST_Length(ST_Intersection(ST_Buffer(s.geom, 0.00010), w.the_geom)) / ST_Length(w.the_geom)) > 0.5)) OR (ST_Contains(ST_Buffer(s.geom, 0.00005), w.the_geom)
    # id is sector, gid is way
    way_id = last_way_id
    source_way_id = ids_to_delete[0]
    for i in range(4):
        if i > 1:
            source_way_id = ids_to_delete[1]
        way_id += 1
        query = "INSERT INTO ways_for_sectors (id, gid) SELECT id, '" + str(way_id) + "' FROM ways_for_sectors WHERE gid = " + str(source_way_id)
        print(query)
        run_query(working_dir + '/' + 'test.gpkg', query)

    way_id += 1
    query = "INSERT INTO ways_for_sectors (id, gid) SELECT id, '" + str(way_id) + "' FROM ways_for_sectors WHERE gid IN (" + str(ids_to_delete[0]) + ", " + str(ids_to_delete[1]) + ")"
    print(query)
    run_query(working_dir + '/' + 'test.gpkg', query)

    # delete 6556 5560
    query = 'DELETE FROM ways WHERE gid IN (' + array_to_in_param(ids_to_delete) + ')'
    run_query(working_dir + '/' + 'test.gpkg', query)
    print(query)

append_line()
