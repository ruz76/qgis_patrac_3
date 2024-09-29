"""
Based on Ralf Kistner postman
"""

import os
from osgeo import ogr
from osgeo import osr
import fiona
from fiona.crs import from_epsg
import math
import random
import csv
import networkx as nx
import xml.dom.minidom as minidom
from datetime import datetime, timedelta
import json
from shapely.geometry import mapping, shape
from shapely.ops import polygonize
from shapely.geometry import Point
from operator import itemgetter, attrgetter

QGIS_RUN=True
if QGIS_RUN:
    from qgis.PyQt.QtCore import *
    from qgis.PyQt.QtGui import *

    from qgis.core import *
    from qgis.gui import *

_NX_BELOW_2_DOT_1 = False

def pairs(lst, circular=False):
    """
    Loop through all pairs of successive items in a list.

    >>> list(pairs([1, 2, 3, 4]))
    [(1, 2), (2, 3), (3, 4)]
    >>> list(pairs([1, 2, 3, 4], circular=True))
    [(1, 2), (2, 3), (3, 4), (4, 1)]
    """
    i = iter(lst)
    first = prev = item = next(i)
    for item in i:
        yield prev, item
        prev = item
    if circular:
        yield item, first

def specify_positions(graph):
    lat_min = min([data['latitude'] for n, data in graph.nodes(data=True)])
    lat_max = max([data['latitude'] for n, data in graph.nodes(data=True)])
    lon_min = min([data['longitude'] for n, data in graph.nodes(data=True)])
    lon_max = max([data['longitude'] for n, data in graph.nodes(data=True)])

    for node, data in graph.nodes(data=True):
        latitude = data['latitude']
        longitude = data['longitude']
        y = (latitude - lat_min) / (lat_max - lat_min) * 1000
        x = (longitude - lon_min) / (lon_max - lon_min) * 1000
        graph.nodes[node]['pos'] = "%d,%d" % (int(x), int(y))

def graph_components(graph):
    # The graph may contain multiple components, but we can only handle one connected component. If the graph contains
    # more than one connected component, we only use the largest one.
    components = list(graph.subgraph(c) for c in nx.connected_components(graph))
    components.sort(key=lambda c: c.size(), reverse=True)

    return components

def odd_graph(graph):
    """
    Given a graph G, construct a graph containing only the vertices with odd degree from G. The resulting graph is
    fully connected, with each weight being the shortest path between the nodes in G.

    Complexity: O(V'*(E + V log(V)) )
    """
    result = nx.Graph()
    odd_nodes = [n for n in graph.nodes() if graph.degree(n) % 2 == 1]
    for u in odd_nodes:
        # We calculate the shortest paths twice here, but the overall performance hit is low
        paths = nx.shortest_path(graph, source=u, weight='weight')
        lengths = nx.shortest_path_length(graph, source=u, weight='weight')
        for v in odd_nodes:
            if u <= v:
                # We only add each edge once
                continue
            # The edge weights are negative for the purpose of max_weight_matching (we want the minimum weight)
            result.add_edge(u, v, weight=-lengths[v], path=paths[v])

    return result


def as_gpx(graph, track_list, name=None):
    """
    Convert a list of tracks to GPX format
    Example:

    >>> g = nx.Graph()
    >>> g.add_node(1, latitude="31.1", longitude="-18.1")
    >>> g.add_node(2, latitude="31.2", longitude="-18.2")
    >>> g.add_node(3, latitude="31.3", longitude="-18.3")
    >>> print(as_gpx(g, [{'points': [1,2,3]}]))
    <?xml version="1.0" ?><gpx version="1.0"><trk><name>Track 1</name><number>1</number><trkseg><trkpt lat="31.1" lon="-18.1"><ele>1</ele></trkpt><trkpt lat="31.2" lon="-18.2"><ele>2</ele></trkpt><trkpt lat="31.3" lon="-18.3"><ele>3</ele></trkpt></trkseg></trk></gpx>
    """
    doc = minidom.Document()

    root = doc.createElement("gpx")
    root.setAttribute("version", "1.0")
    doc.appendChild(root)

    if name:
        gpx_name = doc.createElement("name")
        gpx_name.appendChild(doc.createTextNode(name))
        root.appendChild(gpx_name)

    for i, track in enumerate(track_list):
        nr = i+1
        track_name = track.get('name') or ("Track %d" % nr)
        trk = doc.createElement("trk")
        trk_name = doc.createElement("name")
        trk_name.appendChild(doc.createTextNode(track_name))
        trk.appendChild(trk_name)
        trk_number = doc.createElement("number")
        trk_number.appendChild(doc.createTextNode(str(nr)))
        trk.appendChild(trk_number)
        trkseg = doc.createElement("trkseg")

        for u in track['points']:
            longitude = graph.nodes[u].get('longitude')
            latitude = graph.nodes[u].get('latitude')
            trkpt = doc.createElement("trkpt")
            trkpt.setAttribute("lat", str(latitude))
            trkpt.setAttribute("lon", str(longitude))
            ele = doc.createElement("ele")
            ele.appendChild(doc.createTextNode(str(u)))
            trkpt.appendChild(ele)
            trkseg.appendChild(trkpt)

        trk.appendChild(trkseg)
        root.appendChild(trk)

    return doc.toxml()

def write_csv(graph, nodes, out):
    writer = csv.writer(out)
    writer.writerow(["Start Node", "End Node", "Segment Length", "Segment ID", "Start Longitude", "Start Latitude", "End Longitude", "End Latitude"])
    for u, v in pairs(nodes, False):
        length = graph[u][v]['weight']
        id = graph[u][v]['id']
        start_latitude = graph.nodes[u].get('latitude')
        start_longitude = graph.nodes[u].get('longitude')
        end_latitude = graph.nodes[v].get('latitude')
        end_longitude = graph.nodes[v].get('longitude')
        writer.writerow([u, v, length, id, start_longitude, start_latitude, end_longitude, end_latitude])

def edge_sum(graph):
    total = 0
    for u, v, data in graph.edges(data=True):
        total += data['weight']
    return total

def matching_cost(graph, matching):
    # Calculate the cost of the additional edges
    cost = 0
    for u, v in (matching.items() if _NX_BELOW_2_DOT_1 else matching):
        if _NX_BELOW_2_DOT_1 and (v <= u):
            continue
        data = graph[u][v]
        cost += abs(data['weight'])
    return cost


def find_matchings(graph, n=5):
    """
    Find the n best matchings for a graph. The best matching is guaranteed to be the best, but the others are only
    estimates.

    A matching is a subset of edges in which no node occurs more than once.

    The result may contain less than n matchings.

    See https://networkx.github.io/documentation/stable/reference/algorithms/generated/networkx.algorithms.matching.max_weight_matching.html
    """
    best_matching = nx.max_weight_matching(graph, True)
    matchings = [best_matching]

    for u, v in (best_matching.items() if _NX_BELOW_2_DOT_1 else best_matching):
        if _NX_BELOW_2_DOT_1 and (v <= u):
            continue
        # Remove the matching
        smaller_graph = nx.Graph(graph)
        smaller_graph.remove_edge(u, v)
        matching = nx.max_weight_matching(smaller_graph, True)
        if len(matching) > 0:
            # We may get an empty matching if there is only one edge (that we removed).
            matchings.append(matching)

    matching_costs = [(matching_cost(graph, matching), matching) for matching in matchings]
    matching_costs.sort(key=lambda k: k[0])

    # HACK: The above code end up giving duplicates of the same path, even though the matching is different. To prevent
    # this, we remove matchings with the same cost.
    final_matchings = []
    last_cost = None
    for cost, matching in matching_costs:
        if cost == last_cost:
            continue
        last_cost = cost
        final_matchings.append((cost, matching))

    return final_matchings


def build_eulerian_graph(graph, odd, matching):
    """
    Build an Eulerian graph from a matching. The result is a MultiGraph.
    """

    # Copy the original graph to a multigraph (so we can add more edges between the same nodes)
    eulerian_graph = nx.MultiGraph(graph)

    # For each matched pair of odd vertices, connect them with the shortest path between them
    for u, v in (matching.items() if _NX_BELOW_2_DOT_1 else matching):
        if _NX_BELOW_2_DOT_1 and (v <= u):
            # With max_weight_matching of NetworkX <2.1 each matching occurs twice in the matchings: (u => v) and (v => u). We only count those where v > u
            continue
        edge = odd[u][v]
        path = edge['path']  # The shortest path between the two nodes, calculated in odd_graph()

        # Add each segment in this path to the graph again
        for p, q in pairs(path):
            eulerian_graph.add_edge(p, q, weight=graph[p][q]['weight'])

    return eulerian_graph

def eulerian_circuit(graph, start_node=None):
    """
    Given an Eulerian graph, find one eulerian circuit. Returns the circuit as a list of nodes, with the first and
    last node being the same.
    """
    node = None
    if start_node in graph.nodes():
        node = start_node
    # print(graph.nodes()[start_node])
    print("eulerian_circuit: " + str(node))
    circuit = list(nx.eulerian_circuit(graph, source=node))
    nodes = []
    for u, v in circuit:
        nodes.append(u)
    # Close the loop
    nodes.append(circuit[0][0])
    return nodes

def chinese_postman_paths(graph, n=5, start_node=None):
    """
    Given a graph, return a list of node id's forming the shortest chinese postman path.
    """

    # Find all the nodes with an odd degree, and create a graph containing only them
    odd = odd_graph(graph)

    # Find the best matching of pairs of odd nodes
    matchings = find_matchings(odd, n)

    paths = []
    for cost, matching in matchings[:n]:
        # Copy the original graph to a multigraph (so we can add more edges between the same nodes)
        eulerian_graph = build_eulerian_graph(graph, odd, matching)

        # Now that we have an eulerian graph, we can calculate the eulerian circuit
        nodes = eulerian_circuit(eulerian_graph, start_node)

        paths.append((eulerian_graph, nodes))
    return paths


def single_chinese_postman_path(graph):
    """
    Given a graph, return a list of node id's forming the shortest chinese postman path.

    If we assume V' (number of nodes with odd degree) is at least some constant fraction of V (total number of nodes),
    say 10%, the overall complexity is O(V^3).
    """

    # Build a fully-connected graph containing only the odd edges.  Complexity: O(V'*(E + V log(V)) )
    odd = odd_graph(graph)

    # Find the best matching of pairs of odd nodes. Complexity: O(V'^3)
    matching = nx.max_weight_matching(odd, True)

    # Complexity of the remainder is less approximately O(E)
    eulerian_graph = build_eulerian_graph(graph, odd, matching)
    nodes = eulerian_circuit(eulerian_graph)

    return eulerian_graph, nodes

def run_query(gpkg_path, query):
    # based on https://svn.osgeo.org/gdal/trunk/autotest/ogr/ogr_gpkg.py

    gpkg_ds = ogr.Open(gpkg_path, update=1)
    gpkg_ds.ExecuteSQL(query)
    gpkg_ds.ExecuteSQL('VACUUM')
    gpkg_ds = None

def run_queries(gpkg_path, queries):
    # based on https://svn.osgeo.org/gdal/trunk/autotest/ogr/ogr_gpkg.py

    gpkg_ds = ogr.Open(gpkg_path, update=1)
    for query in queries:
        gpkg_ds.ExecuteSQL(query)
    gpkg_ds.ExecuteSQL('VACUUM')
    gpkg_ds = None

def get_table_data(gpkg_path, table_name, fields):
    features_output = []
    with fiona.open(gpkg_path, layer=table_name) as layer:
        for feature in layer:
            feature_output = {}
            for field in fields:
                feature_output[field] = feature['properties'][field]
            features_output.append(feature_output)
    return features_output

def save_layer_as_geojson(gpkg_path, table_name, fields, output_path):
    features_output = []
    print('Before fiona open')
    print(fiona.__version__)
    with fiona.open(gpkg_path, layer=table_name) as layer:
        for feature in layer:
            # print(feature)
            # print(feature["geometry"])
            # print(shape(feature["geometry"]))
            try:
                print(mapping(shape(feature["geometry"])))
            except Exception as e:
                print(e)
            # feature_output = {
            #     "type": "Feature",
            #     "properties": {},
            #     "geometry": mapping(shape(feature["geometry"]))
            # }
            feature_output = {
                "type": "Feature",
                "properties": {},
                "geometry": feature["geometry"]
            }
            # print('Before fields')
            for field in fields:
                feature_output['properties'][field] = feature['properties'][field]
            # print('After fields')
            features_output.append(feature_output)
    data = {
        "type": "FeatureCollection",
        "features": features_output
    }
    print('Before write')
    with open(output_path, 'w') as out:
        json.dump(data, out)

def save_layer_as_shp(gpkg_path, table_name, label, output_path):
    vector = QgsVectorLayer(gpkg_path + '|layername=' + table_name, label, "ogr")
    crs = QgsCoordinateReferenceSystem(4326)
    print('Saving into: ' + output_path)
    QgsVectorFileWriter.writeAsVectorFormat(vector, output_path, "utf-8", crs, "ESRI Shapefile")

def array_to_in_param(arr, quotes=False):
    output = ''
    for item in arr:
        if quotes:
            output += "'" + str(item) + "', "
        else:
            output += str(item) + ', '
    return output[:-2]

def prepare_data(config):
    output_data = {}
    sectors = array_to_in_param(config['sectors'])

    run_query(config['gpkg_path'], 'DELETE FROM sectors')
    run_query(config['gpkg_path'], 'INSERT INTO sectors SELECT * FROM sectors_all WHERE id IN (' + sectors + ')')

    run_query(config['gpkg_path'], 'delete from sectors_by_path_with_neighbors_agg_export')
    run_query(config['gpkg_path'], "insert into sectors_by_path_with_neighbors_agg_export (id, type_5_length_m) select id, type_5_length_m from sectors_by_path_with_neighbors_agg WHERE id IN (" + sectors + ") order by type_5_length_m desc")
    output_data['sectors_by_path_with_neighbors_agg'] = get_table_data(config['gpkg_path'], 'sectors_by_path_with_neighbors_agg_export', ['id', 'type_5_length_m'])

    run_query(config['gpkg_path'], 'delete from sum_length_export')
    run_query(config['gpkg_path'], "insert into sum_length_export (sum_length_m) select round(sum(length_m) / 1000) sum_length_m from sectors_by_path_type WHERE id IN (" + sectors + ")")
    output_data['sum_length'] = get_table_data(config['gpkg_path'], 'sum_length_export', ['sum_length_m'])

    run_query(config['gpkg_path'], 'delete from sectors_with_paths_lengths_export')
    run_query(config['gpkg_path'], "insert into sectors_with_paths_lengths_export (id, length_m, x, y) select sp.id, length_m, ST_X(ST_Centroid(s.geom)) x, ST_Y(ST_Centroid(s.geom)) y from sectors_with_pl sp join sectors s on (s.id IN (" + sectors + ") AND s.id = sp.id)")
    output_data['sectors_with_paths_lengths'] = get_table_data(config['gpkg_path'], 'sectors_with_paths_lengths_export', ['id', 'length_m', 'x', 'y'])

    run_query(config['gpkg_path'], 'delete from sectors_neighbors_export')
    run_query(config['gpkg_path'], "insert into sectors_neighbors_export (id, string_agg) select id, string_agg from sectors_neighbors WHERE id IN (" + sectors + ")")
    output_data['sectors_neighbors'] = get_table_data(config['gpkg_path'], 'sectors_neighbors_export', ['id', 'string_agg'])

    run_query(config['gpkg_path'], 'delete from sectors_envelope_export')
    run_query(config['gpkg_path'], "insert into sectors_envelope_export (minx, miny, maxx, maxy) select MIN(ST_MinX(geom)) AS min_x, MIN(ST_MinY(geom)) AS min_y, MAX(ST_MaxX(geom)) AS max_x, MAX(ST_MaxY(geom)) AS max_y FROM sectors")
    output_data['sectors_envelope'] = get_table_data(config['gpkg_path'], 'sectors_envelope_export', ['minx', 'miny', 'maxx', 'maxy'])

    return output_data

def get_cluster(config, clusters, sectors, placement, grid):
    distance = 1000000
    sector_id = -1
    for sector in sectors:
        # The sector is not used yet
        if sector not in clusters:
            curdistance = math.sqrt(math.pow(sectors[sector]['x'] - grid[placement][0], 2) + math.pow(sectors[sector]['y'] - grid[placement][1], 2))
            if curdistance < distance:
                if config['log_level'] == 'debug':
                    print(curdistance)
                    print(sector)
                    print(sectors[sector])
                sector_id = sector
                distance = curdistance

    return sector_id


def get_grid_position(sector, grid):
    distance = 1000000
    grid_id = -1
    pos = 0
    for grid_item in grid:
        curdistance = math.sqrt(math.pow(sector['x'] - grid_item[0], 2) + math.pow(sector['y'] - grid_item[1], 2))
        if curdistance < distance:
            grid_id = pos
            distance = curdistance
        pos += 1
    return grid_id


def grid_position_is_empty(grid_pos, clusters):
    is_empty = True
    for cluster_id in clusters:
        if clusters[cluster_id]['grid'] == grid_pos:
            is_empty = False
    return is_empty


def is_neighbor(sector_id, clusters, sectors_neighbors):
    is_neighbor = False
    for cluster_id in clusters:
        if cluster_id in sectors_neighbors[sector_id]:
            is_neighbor = True
    return is_neighbor


def is_already_in_clusters(clusters, sector_id):
    for cluster_id in clusters:
        if sector_id in clusters[cluster_id]['sectors']:
            return True
    return False


def append_sector_into_cluster(clusters, sectors, sectors_neighbors, cluster_id):
    for sector_in_cluster in clusters[cluster_id]['sectors']:
        for sector_in_neighbors in sectors_neighbors[sector_in_cluster]:
            if not is_already_in_clusters(clusters, sector_in_neighbors):
                # print(sector_in_neighbors)
                # if sector_in_neighbors == "3035":
                #     print(sectors)
                if sector_in_neighbors in sectors:
                    clusters[cluster_id]['sectors'].append(sector_in_neighbors)
                    clusters[cluster_id]['length'] += sectors[sector_in_neighbors]['length']
                    return

def fix_not_assigned(config, sectors_not_assigned, clusters, sectors_neighbors, sectors, iteration):
    if config['log_level'] == 'debug':
        print(sectors_not_assigned)
    items_to_remove = []
    for not_assigned_sector in sectors_not_assigned:
        if config['log_level'] == 'debug':
            print('Processing: ' + str(not_assigned_sector))
        cluster_candidates = {}
        for cluster_id in clusters:
            for sector_id in clusters[cluster_id]['sectors']:
                if not_assigned_sector in sectors_neighbors[sector_id]:
                    if iteration > 5:
                        cluster_candidates[cluster_id] = clusters[cluster_id]['length']
                    else:
                        if clusters[cluster_id]['length'] < config['covers'][clusters[cluster_id]['unit']] * 1000:
                            cluster_candidates[cluster_id] = clusters[cluster_id]['length']
        if config['log_level'] == 'debug':
            print('Len cluster_candidates: ' + str(len(cluster_candidates)))
        if len(cluster_candidates) < 1:
            if config['log_level'] == 'debug':
                print("We have a problem with: " + str(not_assigned_sector))
        if len(cluster_candidates) > 0:
            cluster_id_candidate = - 1
            max_diff_length_candidate = -10000000
            for cluster_id in cluster_candidates:
                if (config['covers'][clusters[cluster_id]['unit']] * 1000 - clusters[cluster_id]['length']) > max_diff_length_candidate:
                    cluster_id_candidate = cluster_id
                    max_diff_length_candidate = config['covers'][clusters[cluster_id]['unit']] * 1000 - clusters[cluster_id]['length']
            clusters[cluster_id_candidate]['sectors'].append(not_assigned_sector)
            clusters[cluster_id_candidate]['length'] += sectors[not_assigned_sector]['length']
            if config['log_level'] == 'debug':
                print('Removing: ' + str(not_assigned_sector))
            items_to_remove.append(not_assigned_sector)

    # Remove the items
    for item in items_to_remove:
        sectors_not_assigned.remove(item)

def get_the_most_undersized_or_oversized_cluster(config, clusters):
    cluster_id_candidate = - 1
    max_diff_length_candidate_in_percent = -10000000
    for cluster_id in clusters:
        if config['log_level'] == 'debug':
            print(str(cluster_id) + ': ' + str(clusters[cluster_id]['length']))
        difference = abs(config['covers'][clusters[cluster_id]['unit']] * 1000 - clusters[cluster_id]['length'])
        current_max_diff_length_candidate_in_percent = difference / (config['covers'][clusters[cluster_id]['unit']] * 1000 / 100)
        if current_max_diff_length_candidate_in_percent > max_diff_length_candidate_in_percent:
            cluster_id_candidate = cluster_id
            max_diff_length_candidate_in_percent = current_max_diff_length_candidate_in_percent
    if config['log_level'] == 'debug':
        print(max_diff_length_candidate_in_percent)
        print('Candidate: ' + str(cluster_id_candidate))
    if max_diff_length_candidate_in_percent > 10:
        return cluster_id_candidate
    else:
        return -1

def get_type_of_optimized_cluster(cluster_id, clusters, covers):
    difference = covers[clusters[cluster_id]['unit']] * 1000 - clusters[cluster_id]['length']
    if difference < 0:
        return -1
    else:
        return 1

def get_cluster_candidate(cluster_candidates, clusters, covers, increase):
    # We should move the sector that in result makes difference for the current_cluster_id length from optimal smallest
    # But also the one that will be used from the cluster that has the biggest difference of the length from optimal
    # The flow is not probably optimal, but first we find the suitable cluster
    # Then we select one of the sector from the cluster that covers the first condition
    cluster_id_candidate = - 1
    max_diff_length_candidate_in_percent = -10000000
    for cluster_id in cluster_candidates:
        difference = clusters[cluster_id]['length'] - covers[clusters[cluster_id]['unit']] * 1000
        if not increase:
            difference = covers[clusters[cluster_id]['unit']] * 1000 - clusters[cluster_id]['length']
        current_max_diff_length_candidate_in_percent = difference / (covers[clusters[cluster_id]['unit']] * 1000 / 100)
        if current_max_diff_length_candidate_in_percent > max_diff_length_candidate_in_percent:
            cluster_id_candidate = cluster_id
            max_diff_length_candidate_in_percent = current_max_diff_length_candidate_in_percent
    return cluster_id_candidate

def get_sector_candidate(current_cluster_id, cluster_id_candidate, cluster_candidates, clusters, sectors, covers, sectors_neighbors, increase):
    sector_id_candidate = -1
    min_diff_length_candidate = 10000000
    if increase:
        for sector_id in cluster_candidates[cluster_id_candidate]:
            if increase:
                if (abs(clusters[current_cluster_id]['length'] + sectors[sector_id]['length'] - covers[clusters[current_cluster_id]['unit']] * 1000)) < min_diff_length_candidate:
                    sector_id_candidate = sector_id
                    min_diff_length_candidate = abs(clusters[current_cluster_id]['length'] + sectors[sector_id]['length'] - covers[clusters[current_cluster_id]['unit']] * 1000)
    else:
        # We have to loop all sectors in current_cluster_id since we want to decrease the current_cluster_id
        # We have to check if the sector is neighbor with any sector in cluster_id_candidate and if the decrease brings the best result
        for sector_id in clusters[current_cluster_id]['sectors']:
            for current_sector_id in clusters[cluster_id_candidate]['sectors']:
                if sector_id in sectors_neighbors[current_sector_id]:
                    if (abs(clusters[current_cluster_id]['length'] - sectors[sector_id]['length'] - covers[clusters[current_cluster_id]['unit']] * 1000)) < min_diff_length_candidate:
                        sector_id_candidate = sector_id
                        min_diff_length_candidate = abs(clusters[current_cluster_id]['length'] + sectors[sector_id]['length'] - covers[clusters[current_cluster_id]['unit']] * 1000)

    return sector_id_candidate

def move_sector_between_clusters(config, current_cluster_id, clusters, sectors, sectors_neighbors):
    cluster_candidates = {}
    for cluster_id in clusters:
        if cluster_id != current_cluster_id:
            for sector_id in clusters[cluster_id]['sectors']:
                for current_sector_id in clusters[current_cluster_id]['sectors']:
                    if sector_id in sectors_neighbors[current_sector_id]:
                        # The sector_id is a neighbor of the current_sector_id
                        if cluster_id not in cluster_candidates:
                            cluster_candidates[cluster_id] = [sector_id]
                        else:
                            cluster_candidates[cluster_id].append(sector_id)

    current_cluster_optimize_type = get_type_of_optimized_cluster(current_cluster_id, clusters, config['covers'])
    if current_cluster_optimize_type == 1:
        cluster_id_candidate = get_cluster_candidate(cluster_candidates, clusters, config['covers'], True)
        sector_id_candidate = get_sector_candidate(current_cluster_id, cluster_id_candidate, cluster_candidates, clusters, sectors, config['covers'], sectors_neighbors, True)
    else:
        cluster_id_candidate = get_cluster_candidate(cluster_candidates, clusters, config['covers'], False)
        sector_id_candidate = get_sector_candidate(current_cluster_id, cluster_id_candidate, cluster_candidates, clusters, sectors, config['covers'], sectors_neighbors, False)

    # We know the final candidate, so we move it from its cluster into current processed cluster
    if config['log_level'] == 'debug':
        print('Type: ' + str(current_cluster_optimize_type))
        print('Before: ' + str(clusters[current_cluster_id]['length']) + ' ' + str(clusters[cluster_id_candidate]['length']))
        print('Sector length: ' + str(sectors[sector_id_candidate]['length']))
    if current_cluster_optimize_type == 1:
        clusters[current_cluster_id]['sectors'].append(sector_id_candidate)
        clusters[cluster_id_candidate]['sectors'].remove(sector_id_candidate)
        clusters[current_cluster_id]['length'] += sectors[sector_id_candidate]['length']
        clusters[cluster_id_candidate]['length'] -= sectors[sector_id_candidate]['length']
    else:
        clusters[cluster_id_candidate]['sectors'].append(sector_id_candidate)
        clusters[current_cluster_id]['sectors'].remove(sector_id_candidate)
        clusters[current_cluster_id]['length'] -= sectors[sector_id_candidate]['length']
        clusters[cluster_id_candidate]['length'] += sectors[sector_id_candidate]['length']
    if config['log_level'] == 'debug':
        print(current_cluster_id + ' ' + cluster_id_candidate)
        print('After: ' + str(clusters[current_cluster_id]['length']) + ' ' + str(clusters[cluster_id_candidate]['length']))

def optimize_clusters(config, clusters, sectors, sectors_neighbors):
    for i in range(100):
        cluster_id_to_optimize = get_the_most_undersized_or_oversized_cluster(config, clusters)
        if cluster_id_to_optimize != -1:
            move_sector_between_clusters(config, cluster_id_to_optimize, clusters, sectors, sectors_neighbors)
        else:
            if config['log_level'] == 'debug':
                print('Breaking optimization at ' + str(i) + ' iteration')
            break

def print_clusters(clusters):
    with open('/tmp/clusters.csv', 'w') as out:
        for cluster_id in clusters:
            for sector in clusters[cluster_id]['sectors']:
                out.write(sector + ';' + str(clusters[cluster_id]['grid']) + ';' + clusters[cluster_id]['type'] + ';' + clusters[cluster_id]['unit'] + ';' + str(cluster_id) + '\n')

def print_clusters_2(clusters):
    for cluster_id in clusters:
        print(str(clusters[cluster_id]['grid']) + ';' + clusters[cluster_id]['type'] + ';' + clusters[cluster_id]['unit'] + ';' + str(clusters[cluster_id]['length']))

def get_used_searchers(config, total_length):

    used_searchers = {
        "handler": 0,
        "pedestrian": 0,
        "rider": 0,
        "quad_bike": 0
    }

    cover = config['searchers']['handler'] * config['covers']['handler']
    cover += config['searchers']['pedestrian'] * config['covers']['pedestrian']
    cover += config['searchers']['rider'] * config['covers']['rider']
    cover += config['searchers']['quad_bike'] * config['covers']['quad_bike']

    print('COVER: ' + str(cover))

    # We do not cover whole area
    if cover < total_length:
        diff = total_length - cover
        if diff < config['covers']['pedestrian'] / 2:
            used_searchers = config['searchers']
        else:
            used_searchers = config['searchers']
            used_searchers['pedestrian'] += math.ceil(diff / config['covers']['pedestrian'])

    # We cover perfectly the whole area - should not happen so often
    if cover == total_length:
        used_searchers = config['searchers']

    # We do cover whole area and have more units
    if cover > total_length:
        diff = cover - total_length
        if diff < config['covers']['pedestrian'] / 2:
            used_searchers = config['searchers']
        else:
            cover = 0
            for i in range(config['searchers']['handler']):
                cover += config['covers']['handler']
                if cover <= total_length:
                    used_searchers['handler'] += 1
            for i in range(config['searchers']['pedestrian']):
                cover += config['covers']['pedestrian']
                if cover <= total_length:
                    used_searchers['pedestrian'] += 1
            for i in range(config['searchers']['rider']):
                cover += config['covers']['rider']
                if cover <= total_length:
                    used_searchers['rider'] += 1
            for i in range(config['searchers']['quad_bike']):
                cover += config['covers']['quad_bike']
                if cover <= total_length:
                    used_searchers['quad_bike'] += 1
            # TODO maybe necessary to add last unit once more
            if used_searchers['handler'] == 0:
                used_searchers['handler'] = 1

    return used_searchers

def get_clusters(config, data):
    total_length = int(float(data['sum_length'][0]['sum_length_m']))
    print('TOTAL LENGTH: ' + str(total_length))

    used_searchers = get_used_searchers(config, total_length)
    number_of_clusters = used_searchers['handler'] + used_searchers['pedestrian'] + used_searchers['rider'] + used_searchers['quad_bike']
    clusters = {}

    if number_of_clusters == 1:
        clusters['0'] = {
            "unit": 'handler',
            "type": "5",
            "sectors": config['sectors'],
            "length": total_length,
            "grid": 1
        }
        return clusters

    number_of_5_type_searchers = config['searchers']['handler'] + config['searchers']['pedestrian']
    sectors = {}
    sectors_neighbors = {}
    sectors_5_max_order = []
    bbox = []
    grid = []
    grid_size = math.ceil(math.sqrt(number_of_clusters))
    print('GRID: ' + str(grid_size))
    grid_rows = grid_size
    grid_cols = grid_size

    for item in data['sectors_by_path_with_neighbors_agg']:
        sectors_5_max_order.append(str(item['id']))

    for item in data['sectors_with_paths_lengths']:
        sectors[str(item['id'])] = {"length": int(item['length_m']), "x": item['x'], "y": item['y']}

    for item in data['sectors_neighbors']:
        neighbors = item['string_agg'].split(';')
        sectors_neighbors[str(item['id'])] = neighbors

    bbox.append(data['sectors_envelope'][0]['minx'])
    bbox.append(data['sectors_envelope'][0]['miny'])
    bbox.append(data['sectors_envelope'][0]['maxx'])
    bbox.append(data['sectors_envelope'][0]['maxy'])

    area_width = bbox[2] - bbox[0]
    area_height =  bbox[3] - bbox[1]
    cell_width = area_width / grid_cols
    cell_height = area_height / grid_rows
    for row in range(grid_rows):
        for col in range(grid_cols):
            x = bbox[0] + cell_width * col + (cell_width / 2)
            y = bbox[1] + cell_height * row + (cell_height / 2)
            grid.append([x, y])

    grid = random.sample(grid, number_of_clusters)


    # We set the first 5 type cluster, if we have a person/handler for it
    used_handlers = 0
    used_pedestrians = 0
    if number_of_5_type_searchers > 0:
        grid_pos = get_grid_position(sectors[sectors_5_max_order[0]], grid)
        unit = 'handler'
        if used_searchers['handler'] == 0:
            unit = 'pedestrian'
            used_pedestrians += 1
        else:
            used_handlers += 1
        clusters[sectors_5_max_order[0]] = {
            "unit": unit,
            "type": "5",
            "sectors": [sectors_5_max_order[0]],
            "length": sectors[sectors_5_max_order[0]]['length'],
            "grid": grid_pos
        }

    while len(clusters) < number_of_5_type_searchers:
        for sector_id in sectors_5_max_order:
            if sector_id not in clusters and sector_id in sectors and not is_neighbor(sector_id, clusters, sectors_neighbors):
                grid_pos = get_grid_position(sectors[sector_id], grid)
                unit = 'handler'
                if used_handlers == used_searchers['handler']:
                    unit = 'pedestrian'
                    used_pedestrians += 1
                else:
                    used_handlers += 1
                if grid_position_is_empty(grid_pos, clusters):
                    clusters[sector_id] = {
                        "unit": unit,
                        "type": "5",
                        "sectors": [sector_id],
                        "length": sectors[sector_id]['length'],
                        "grid": grid_pos
                    }
                    if config['log_level'] == 'debug':
                        print(len(clusters))
                    break
    used_riders = 0
    used_quad_bike = 0
    for i in range(number_of_clusters):
        if grid_position_is_empty(i, clusters):
            cluster_id = get_cluster(config, clusters, sectors, i, grid)
            unit = 'rider'
            if used_riders == used_searchers['rider']:
                unit = 'quad_bike'
                used_quad_bike += 1
            else:
                used_riders += 1
            clusters[cluster_id] = {
                "unit": unit,
                "type": "4",
                "sectors": [cluster_id],
                "length": sectors[cluster_id]['length'],
                "grid": i
            }

    for it in range(100):
        if config['log_level'] == 'debug':
            print("Iteration: " + str(it))
        for cluster_id in clusters:
            if config['log_level'] == 'debug':
                print("Cluster: " + str(cluster_id))
            if clusters[cluster_id]['length'] < config['covers'][clusters[cluster_id]['unit']] * 1000:
                if config['log_level'] == 'debug':
                    print("Adding another sector into cluster.")
                append_sector_into_cluster(clusters, sectors, sectors_neighbors, cluster_id)
            else:
                if config['log_level'] == 'debug':
                    print("Cluster is full. Skipping.")

    # print(sectors)
    # print(sectors_neighbors)
    # print(clusters)
    # return

    sectors_not_assigned = []
    for sector in sectors:
        sector_is_assigned = False
        for cluster_id in clusters:
            if sector in clusters[cluster_id]['sectors']:
                sector_is_assigned = True
        if not sector_is_assigned:
            sectors_not_assigned.append(sector)

    # print(sectors_not_assigned)
    #
    for i in range(10):
        if config['log_level'] == 'debug':
            print("Fix not assigned. Iteration: " + str(i))
        fix_not_assigned(config, sectors_not_assigned, clusters, sectors_neighbors, sectors, i)

    optimize_clusters(config, clusters, sectors, sectors_neighbors)
    # print(clusters)
    if config['log_level'] == 'debug':
        print_clusters_2(clusters)
        print_clusters(clusters)

    return clusters


def prepare_data_for_graph_based_on_polygon(config):

    # TODO use grades as well
    run_query(config['gpkg_path'], 'delete from ways_for_sectors_export')
    sql = "insert into ways_for_sectors_export (source, target, length_m, gid, x1, y1, x2, y2) select distinct source, target, length_m, ways.gid gid, x1, y1, x2, y2 from ways, new_polygon_layer where st_intersects(ways.the_geom, st_buffer(new_polygon_layer.geom, -0.00005))"
    # print(sql)
    run_query(config['gpkg_path'], sql)
    output_data = get_table_data(config['gpkg_path'], 'ways_for_sectors_export', ['source', 'target', 'length_m', 'gid', 'x1', 'y1', 'x2', 'y2'])

    return output_data

def prepare_data_for_graph(config, sectors_list, grades):
    sectors = array_to_in_param(sectors_list)

    run_query(config['gpkg_path'], 'delete from ways_for_sectors_export')
    # sql = "insert into ways_for_sectors_export (source, target, length_m, gid, x1, y1, x2, y2) select distinct source, target, length_m, ways.gid gid, x1, y1, x2, y2 from ways join ways_for_sectors wfs on (grade in (" + grades + ") and id IN (" + sectors + ") and ways.gid = wfs.gid)"
    # print(sql)
    sql = "insert into ways_for_sectors_export (source, target, length_m, gid, x1, y1, x2, y2) select distinct source, target, length_m, ways.gid gid, x1, y1, x2, y2 from ways join ways_for_sectors wfs on (grade in (" + grades + ") and ways.gid = wfs.gid)"
    run_query(config['gpkg_path'], sql)
    output_data = get_table_data(config['gpkg_path'], 'ways_for_sectors_export', ['source', 'target', 'length_m', 'gid', 'x1', 'y1', 'x2', 'y2'])

    return output_data

    # TODO - seems that the implementation is wrong
    # This is an optimisation where we removed nodes that are not on intersection or are not isolated nodes (end of line)
    nodes = {

    }

    for way in output_data:
        if way['source'] in nodes:
            nodes[way['source']] += 1
        else:
            nodes[way['source']] = 1

        if way['target'] in nodes:
            nodes[way['target']] += 1
        else:
            nodes[way['target']] = 1

    output_data_fixed = []
    for key in nodes:
        if nodes[key] == 2:
            # This should be a node that is not necessary since it is not a node on intersection, and it is not an isolated node
            ways_to_merge = []
            for way in output_data:
                if way['source'] == key or way['target'] == key:
                    ways_to_merge.append(way)
            if len(ways_to_merge) > 1:
                # We start on 0 source and end on 1 target
                if ways_to_merge[0]['target'] == ways_to_merge[1]['source']:
                    merged_way = ways_to_merge[0]
                    merged_way['target'] = ways_to_merge[1]['target']
                    merged_way['length_m'] += ways_to_merge[1]['length_m']
                    output_data_fixed.append(merged_way)
                # We start on 0 source and end on 1 source
                if ways_to_merge[0]['target'] == ways_to_merge[1]['target']:
                    merged_way = ways_to_merge[0]
                    merged_way['target'] = ways_to_merge[1]['source']
                    merged_way['length_m'] += ways_to_merge[1]['length_m']
                    output_data_fixed.append(merged_way)
                # We start on 1 source and end on 0 target
                if ways_to_merge[0]['source'] == ways_to_merge[1]['target']:
                    merged_way = ways_to_merge[1]
                    merged_way['target'] = ways_to_merge[0]['target']
                    merged_way['length_m'] += ways_to_merge[0]['length_m']
                    output_data_fixed.append(merged_way)
                # We start on 0 target and end on 1 target
                if ways_to_merge[0]['source'] == ways_to_merge[1]['source']:
                    merged_way = ways_to_merge[1]
                    merged_way['source'] = ways_to_merge[0]['target']
                    merged_way['length_m'] += ways_to_merge[0]['length_m']
                    output_data_fixed.append(merged_way)
        else:
            # These nodes should be correct
            for way in output_data:
                if way['source'] == key or way['target'] == key:
                    output_data_fixed.append(way)

    return output_data_fixed

def build_graph(features, used_edges):
    # print(nx.__version__)
    graph = nx.Graph()
    for feature in features:
        # print(used_edges)
        if feature['gid'] not in used_edges:
            # print(feature['gid'])
            graph.add_edge(str(feature['source']), str(feature['target']), weight=feature['length_m'], id=str(feature['gid']), label=str(feature['gid']))
            # We keep the GPS coordinates as strings
            graph.nodes[str(feature['source'])]['longitude'] = feature['x1']
            graph.nodes[str(feature['source'])]['latitude'] = feature['y1']
            graph.nodes[str(feature['target'])]['longitude'] = feature['x2']
            graph.nodes[str(feature['target'])]['latitude'] = feature['y2']

    return graph

def solve_graph(graph, config, name):
    components = graph_components(graph)
    # for component in components:
    #     print(component)
    #     for item in component:
    #         print(item)

    if len(components) > 1:
        print("Warning: the selected area contains multiple disconnected " +
                                "components.")

    if len(components) == 0:
        print("Error: Could not find any components. Try selecting different features.")
        return

    outputs = []
    component_id = 0
    for component in components:

        eulerian_graph, nodes = single_chinese_postman_path(component)

        in_length = edge_sum(component)/1000.0
        path_length = edge_sum(eulerian_graph)/1000.0
        duplicate_length = path_length - in_length

        info = "Component: " + str(component_id) + "\n"
        info += "Total length of roads: %.3f km\n" % in_length
        info += "Total length of path: %.3f km\n" % path_length
        info += "Length of sections visited twice: %.3f km\n" % duplicate_length

        print(info)

        create_layer(config, graph, nodes, name + '_' + str(component_id))

        output = {
            "id": name + '_' + str(component_id),
            "total_roads": in_length,
            "total_path": path_length,
            "duplicate_length": duplicate_length
        }

        outputs.append(output)
        component_id += 1

    return outputs

def create_layer(config, graph, nodes, name):
    run_query(config['gpkg_path'], 'delete from chpostman_path')
    pos = 0
    ts = datetime.now()
    queries = []
    # for u, v in pairs(nodes, False):
    #     pos += 1
    #     ts = ts + timedelta(seconds=1)
    #     queries.append("insert into chpostman_path (gid, ord, ts) values (" + graph[u][v]['id'] + ", '" + str(pos) + "', '" + str(ts).split('.')[0] + "')")
    # Projití všech hran a vypsání jejich vah
    for u, v, data in graph.edges(data=True):
        pos += 1
        ts = ts + timedelta(seconds=1)
        queries.append("insert into chpostman_path (gid, ord, ts) values (" + data['id'] + ", '" + str(pos) + "', '" + str(ts).split('.')[0] + "')")
        # print(f'Hrana mezi {u} a {v} má váhu {data["weight"]}')

    run_queries(config['gpkg_path'], queries)
    run_query(config['gpkg_path'], 'delete from chpostman_path_export')
    run_query(config['gpkg_path'], "insert into chpostman_path_export (gid, ord, ts, the_geom) select ch.gid, ch.ord, ch.ts, w.the_geom from chpostman_path ch join ways w on (ch.gid = w.gid)")

    print('Before export')

    # Crashes when running inside QGIS, so we will do not use fiona for export in QGIS but QGIS API
    # save_layer_as_geojson(config['gpkg_path'], 'chpostman_path_export', ['gid', 'ord', 'ts'], os.path.join(config['output_dir'], name + '.geojson'))
    save_layer_as_shp(config['gpkg_path'], 'chpostman_path_export', name, os.path.join(config['output_dir'], name + '.shp'))

    print('After export')

def get_units_grades(unit):
    if unit == 'handler':
        return '0, 1, 2, 3, 4, 5, 6'
        # return '5'
    if unit == 'pedestrian':
        return '0, 1, 2, 3, 4, 5, 6'
    if unit == 'rider':
        return '0, 1, 2, 3'
    if unit == 'quad_bike':
        return '0, 1, 2, 3'
    return '0, 1, 2, 3'

def solve_area(config):
    # Reads sectors and prepares data for clustering
    data = prepare_data(config)
    # Returns clusters
    clusters = get_clusters(config, data)
    solutions = []
    used_edges = []
    for cluster_id in clusters:
        # print(clusters[cluster_id]['sectors'])
        print(clusters[cluster_id]['unit'])
        # Prepares data in a form of nodes and edges
        grades = get_units_grades(clusters[cluster_id]['unit'])
        print(grades)
        graph_data_input = prepare_data_for_graph(config, clusters[cluster_id]['sectors'], grades)
        graph = build_graph(graph_data_input, used_edges)
        # Remembers already used edges
        for edge in graph_data_input:
            used_edges.append(edge['gid'])
        # print(graph_data_input)
        used_edges = [] # Use this if you do not want to remove duplicities
        graph_solution = solve_graph(graph, config, clusters[cluster_id]['unit'] + '_' + str(cluster_id))
        solutions.append(graph_solution)
    return solutions

def test_me():
    config = {
        "log_level": "debug",
        "gpkg_path": "/home/jencek/Documents/Projekty/PCR/test_data/test.gpkg",
        "output_dir": "/tmp/",
        "covers": {
            "handler": 12,
            "pedestrian": 12,
            "rider": 16,
            "quad_bike": 20
        },
        "searchers": {
            "handler": 1,
            "pedestrian": 1,
            "rider": 2,
            "quad_bike": 3
        },
        "sectors": [128, 84, 94, 177, 3025, 3035, 3038, 3254, 3288, 3290, 3291, 3295, 3299, 4226, 4227, 4238, 4277, 4301, 4302, 4304, 4311, 4410, 4413, 4427, 4430, 4431, 4433, 4440, 4441, 28938, 40255, 101753, 101850, 101865, 109484, 109758, 109791, 109808, 109819, 109823, 109829, 109830, 109831, 109848, 109853, 109854, 109855, 109857, 110347, 110348, 110354, 110425, 110426, 110430, 110434, 110446, 110458, 110500, 110542, 110633, 110638, 110647, 170252, 179681, 752557, 768172, 235, 4300, 4309, 34963, 126, 2097, 768067, 123, 297, 2356, 4310, 39965, 40060, 40441]
    }
    solve_area(config)


def solve_one_part(start_node, end_node, config, graph_data_input):
    if os.path.exists(end_node + '_graph.json'):
        # Deserializace z JSON
        with open(end_node + '_graph.json', 'r') as f:
            data = json.load(f)
        G_union = nx.node_link_graph(data)
        graph_solution = solve_graph(G_union, config, 'test_' + str(end_node))
        print(graph_solution)

    else:
        graph = build_graph(graph_data_input, [])
        print(graph)
        if not start_node in graph or end_node not in graph:
            if not start_node in graph:
                print("Nod " + str(start_node) + " není v grafu")
            if end_node not in graph:
                print("Nod " + str(end_node) + " není v grafu")
            return

        # Výpočet nejkratší trasy mezi těmito uzly
        try:
            shortest_path = nx.shortest_path(graph, source=start_node, target=end_node, weight='weight')
            shortest_path_length = nx.shortest_path_length(graph, source=start_node, target=end_node, weight='weight')
        except:
            print('Nebyla nalezena trasa mezi výchozím a cílovým bodem')
            return

        # Výpis výsledků
        print(f'Náhodně vybrané uzly: {start_node} a {end_node}')
        print(f'Nejkratší trasa mezi {start_node} a {end_node} je: {shortest_path}')
        print(f'Délka nejkratší trasy je: {shortest_path_length}')

        # Vytvoření nového grafu obsahujícího hrany z obou nejkratších cest
        H = nx.Graph()

        # Přidání hran z první nejkratší cesty
        for i in range(len(shortest_path) - 1):
            u, v = shortest_path[i], shortest_path[i + 1]
            H.add_edge(u, v, weight=graph.get_edge_data(u, v)['weight'], id=graph.get_edge_data(u, v)['id'])

        # Odstranění hran, které tvoří nalezenou trasu, z grafu. Ponechání první hrany.
        for i in range(len(shortest_path) - 2):
            graph.remove_edge(shortest_path[i + 1], shortest_path[i + 2])
        # graph.remove_edge(shortest_path[len(shortest_path) - 2], shortest_path[len(shortest_path) - 1])

        # Výpočet nejkratší trasy mezi těmito uzly
        start_node_orig = start_node
        start_node = end_node
        end_node = start_node_orig

        try:
            shortest_path = nx.shortest_path(graph, source=start_node, target=end_node, weight='weight')
            shortest_path_length = nx.shortest_path_length(graph, source=start_node, target=end_node, weight='weight')
        except Exception as e:
            print(e)
            print(f'Hrany v grafu: {graph.edges(data=True)}')
            return

        # Výpis výsledků
        print(f'Náhodně vybrané uzly: {start_node} a {end_node}')
        print(f'Nejkratší trasa mezi {start_node} a {end_node} je: {shortest_path}')
        print(f'Délka nejkratší trasy je: {shortest_path_length}')

        # Přidání hran z druhé nejkratší cesty
        for i in range(len(shortest_path) - 1):
            u, v = shortest_path[i], shortest_path[i + 1]
            if not H.has_edge(u, v):
                H.add_edge(u, v, weight=graph.get_edge_data(u, v)['weight'], id=graph.get_edge_data(u, v)['id'])

        # Výpis hran nového grafu
        # print(f'Hrany v novém grafu: {H.edges(data=True)}')

        # Vypsání hran z původního grafu, které jsou napojeny pouze na uzly nového grafu
        # connected_edges = []
        # for node in H.nodes:
        #     # print('Node: ' + str(node))
        #     for neighbor in graph.neighbors(node):
        #         # print('Neighbor: ' + str(neighbor))
        #         len_neighbors_2 = 0
        #         for neighbor2 in graph.neighbors(neighbor):
        #             len_neighbors_2 += 1
        #             # print('\tNN: ' + str(neighbor2))
        #         if len_neighbors_2 == 1:
        #             print('\t\tIsolated: ' + str(neighbor))
        #             if graph.has_edge(node, neighbor) and neighbor not in H.nodes:
        #                 print('\t\t' + str(node) + ' ' + str(neighbor))
        #                 edge_data = graph[node][neighbor]
        #                 print(edge_data)
        #                 connected_edges.append([node, neighbor, edge_data['weight'], edge_data['id']])
        #                 # connected_edges.add([node, neighbor, edge_data])
        #                 # print(edge_data)
        #
        # # Přidání napojených hran do nového grafu
        # for edge in connected_edges:
        #     H.add_edge(edge[0], edge[1], weight=edge[2], id=edge[3])
        #
        # # Výpis hran nového grafu po přidání napojených hran
        # print(f'Hrany v novém grafu po přidání napojených hran: {H.edges(data=True)}')

        create_layer(config, H, H.nodes, 'test_ring_only_' + str(start_node))
        get_ring_polygon(config)
        graph_data_input_missing_edges = prepare_data_for_graph_based_on_polygon(config)
        graph_missing_edges = build_graph(graph_data_input_missing_edges, [])
        # print(graph_missing_edges)

        G_union = nx.compose(H, graph_missing_edges)
        # print(G_union)

        graph_solution = solve_graph(G_union, config, 'test_' + str(start_node))
        print(graph_solution)

    return [graph_solution, G_union]

def get_ring_polygon(config):
    with fiona.open(config['gpkg_path'], layer='chpostman_path_export') as layer:
        lines = []
        for feature in layer:
            # print(feature)
            line = shape(feature['geometry'])
            # print(line)
            lines.append(line)
        polygons = list(polygonize(lines))
        # print(polygons)
        for polygon in polygons:
            print(polygon)

    # Soubor GeoPackage, do kterého chceme uložit polygony
    gpkg_path = config['gpkg_path']
    # layer_name = 'new_polygon_layer'
    #
    # # Specifikace CRS (zde EPSG:4326, můžete upravit podle potřeby)
    # crs = from_epsg(4326)
    #
    # # Definice schématu pro novou vrstvu
    # schema = {
    #     'geometry': 'Polygon',
    #     'properties': {
    #         'id': 'int',
    #     },
    # }

    # Přidání nové vrstvy do existujícího souboru GPKG
    # nefunguje - nevím proč
    # print(config['gpkg_path'])
    # with fiona.open(gpkg_path, 'a', driver='GPKG', schema=schema, layer=layer_name, crs=crs) as sink:
    #     # Přidání polygonů do nové vrstvy
    #     for i, polygon in enumerate(polygons):
    #         sink.write({
    #             'geometry': mapping(polygon),
    #             'properties': {'id': i},
    #         })
    #
    # print(f'Polygony byly úspěšně uloženy do vrstvy {layer_name} v souboru {gpkg_path}.')

    # Soubor GeoPackage, do kterého chceme uložit polygony
    layer_name = 'new_polygon_layer'

    # Specifikace CRS (zde EPSG:4326, můžete upravit podle potřeby)
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)

    # Otevření souboru GeoPackage
    gpkg_ds = ogr.Open(gpkg_path, update=1)
    if not gpkg_ds:
        raise ValueError(f"Could not open {gpkg_path}")

    # Kontrola a odstranění existující vrstvy
    layer = gpkg_ds.GetLayerByName(layer_name)
    if layer:
        gpkg_ds.DeleteLayer(layer_name)
        print(f"Layer {layer_name} was deleted.")

    # Vytvoření nové vrstvy
    layer = gpkg_ds.CreateLayer(layer_name, srs, ogr.wkbPolygon)
    if not layer:
        raise ValueError(f"Could not create layer {layer_name}")

    # Přidání pole 'id'
    field_defn = ogr.FieldDefn('id', ogr.OFTInteger)
    if layer.CreateField(field_defn) != 0:
        raise ValueError("Creating 'id' field failed")

    # Přidání polygonů do nové vrstvy
    for i, polygon in enumerate(polygons):
        feature = ogr.Feature(layer.GetLayerDefn())
        feature.SetField('id', i)
        geom = ogr.CreateGeometryFromWkt(polygon.wkt)
        feature.SetGeometry(geom)
        if layer.CreateFeature(feature) != 0:
            raise ValueError("Failed to create feature in layer")
        feature = None  # Zajistí, že funkce bude uvolněna

    # Uvolnění datasetu
    gpkg_ds.ExecuteSQL('VACUUM')
    gpkg_ds = None

    print(f'Polygony byly úspěšně uloženy do vrstvy {layer_name} v souboru {gpkg_path}.')

def find_points(config, nodes_with_degree_one):
    source_point = config['start_point'] #[15.0339242, 49.340751]
    edge_points = []
    diff_x = 0.025
    diff_y = 0.018

    if 'end_point' in config and config['end_point'] is not None:
        end_point = config['end_point']
        edge_points.append(Point(end_point[0], end_point[1]))

    else:

        # top
        edge_points.append(Point(source_point[0] - diff_x, source_point[1] + diff_y))
        edge_points.append(Point(source_point[0], source_point[1] + diff_y))
        edge_points.append(Point(source_point[0] + diff_x, source_point[1] + diff_y))
        # middle
        edge_points.append(Point(source_point[0] - diff_x, source_point[1]))
        edge_points.append(Point(source_point[0] + diff_x, source_point[1]))
        # bottom
        edge_points.append(Point(source_point[0] - diff_x, source_point[1] - diff_y))
        edge_points.append(Point(source_point[0], source_point[1] - diff_y))
        edge_points.append(Point(source_point[0] + diff_x, source_point[1] - diff_y))

    closets_points = {}
    for i in range(8):
        closets_points[i] = []

    print(edge_points)
    start_point = [0, 1000000]
    start_point_point = Point(source_point[0], source_point[1])

    with fiona.open(config['gpkg_path'], layer='ways_nodes') as layer:
        for feature in layer:
            # node = shape(feature['geometry'])
            # print(node)
            point_to_check = Point(feature['geometry']['coordinates'])
            pos = 0
            for point in edge_points:
                # point1 = Point(x1, y1)
                cur_distance = point.distance(point_to_check)
                if cur_distance < diff_x and feature['properties']['source'] not in nodes_with_degree_one:
                    if {"id": feature['properties']['source'], "distance": cur_distance} not in closets_points[pos]:
                        closets_points[pos].append({"id": feature['properties']['source'], "distance": cur_distance})
                pos += 1
            cur_distance = start_point_point.distance(point_to_check)
            if cur_distance < start_point[1]:
                start_point = [feature['properties']['source'], cur_distance]

    # print(start_point)
    for key in closets_points:
        closets_points[key] = sorted(closets_points[key], key=itemgetter('distance'))
    # print(closets_points)
    # cp = ''
    # for key in closets_points:
    #     cp += ', ' + str(closets_points[key][0])
    # print(cp)

    return [start_point, closets_points]

def is_subgraph(G1, G2):
    """
    Checks if G1 is a subgraph of G2.
    This means all nodes and edges of G1 are contained in G2.
    """
    # Check if all nodes of G1 are in G2
    for node in G1.nodes():
        if node not in G2.nodes():
            return False

    # Check if all edges of G1 are in G2
    for edge in G1.edges():
        if edge not in G2.edges() and (edge[1], edge[0]) not in G2.edges():
            return False

    return True

def are_graphs_identical(G1, G2):
    missing_any = 0
    # Check if all nodes of G1 are in G2
    for node in G1.nodes():
        if node not in G2.nodes():
            missing_any += 1

    for node in G2.nodes():
        if node not in G1.nodes():
            missing_any += 1

    # Check if all edges of G1 are in G2
    for edge in G1.edges():
        if edge not in G2.edges() and (edge[1], edge[0]) not in G2.edges():
            missing_any += 1

    # Check if all edges of G2 are in G1
    for edge in G2.edges():
        if edge not in G1.edges() and (edge[1], edge[0]) not in G1.edges():
            missing_any += 1

    if missing_any > 0:
        return False
    else:
        return True

def export_linies_into_xy_csv(shp_path):
    with fiona.open(shp_path) as layer:
        with open(shp_path + ".csv", "w") as out_csv:
            for feature in layer:
                print(feature["properties"]["ord"])
                line = shape(feature["geometry"])
                for coord in line.coords:
                    print(coord)
                    out_csv.write(str(coord[0]) + ',' + str(coord[1]) + '\n')

def test_approach_based_on_shortest_path():
    config = {
        "log_level": "debug",
        "gpkg_path": "/home/jencek/Documents/Projekty/PCR/test_data_eustach/test_short.gpkg",
        "output_dir": "/tmp/",
        "covers": {
            "handler": 12,
            "pedestrian": 12,
            "rider": 16,
            "quad_bike": 20
        },
        "searchers": {
            "handler": 1,
            "pedestrian": 1,
            "rider": 2,
            "quad_bike": 3
        },
        "sectors": [142442, 142444, 143254, 143263, 143884, 143941, 145390, 145401, 145405, 145408, 145446, 145448, 145453, 145464, 145465, 145468, 145525, 145526, 145529, 145547, 145555, 145556, 145557, 145558, 145603, 660753, 660758, 660783, 660800, 660824, 660832, 660837, 660838, 660840, 660843, 664917, 673397, 674517, 674663, 674668, 674669, 674679, 674682, 674693, 674694, 674695, 674696, 674697, 674700, 674704, 674706, 674707, 674712, 674715, 674734, 674736, 674742, 674743, 674744, 674746, 674748, 674750, 674753, 674755, 674762, 674763, 674764, 674767, 674769, 674770, 674771, 674773, 674778, 674779, 674780, 674781, 674783, 674784, 674790, 674795, 674796, 674797, 674798, 674800, 674806, 674813, 674836, 674842, 674844, 674940, 674941, 674943, 674944, 674946, 674952, 674955, 674958, 674959, 674961, 674962, 674963, 674967, 674971, 674973, 674975, 674977, 674983, 675011, 675012, 675919, 676991, 688010, 145350, 145359, 145392, 145418, 145457, 145462, 145463, 145489, 145575, 668767, 674411, 674520, 674533, 674598, 674609, 674667, 674671, 674676, 674683, 674688, 674689, 674699, 674709, 674710, 674716, 674717, 674722, 674725, 674726, 674727, 674745, 674815, 674816, 674817, 674819, 674822, 674826, 674828, 674831, 674832, 674833, 674838, 674843, 674846, 674850, 674866, 674884, 674887, 674897, 674899, 674913, 674914, 674916, 674925, 674926, 674927, 674929, 674931, 674933, 674934, 674937, 674982, 674984, 674989, 674990, 674991, 674993, 674997, 675000, 675001, 675003, 675004, 675008, 675016, 675017, 687754, 687968, 765584, 674751, 142598, 142602, 142656, 142671, 142687, 145458, 654010, 657634, 657673, 657714, 657811, 659980, 660699, 660847, 660856, 663634, 663636, 663639, 663640, 663643, 663660, 663671, 674935, 647978, 674851, 144824, 144828, 144935, 145388, 145427, 145480, 145535, 145539, 145565, 647941, 647949, 671820, 672039, 672041, 672042, 672106, 674662, 674670, 674687, 674692, 674698, 674703, 674733, 674810, 674812, 674814, 685157, 687920, 143201, 144025, 144057, 145373, 145387, 145399, 145404, 145409, 145412, 145444, 145445, 145454, 145455, 145456, 145459, 145528, 145537, 145540, 145542, 145548, 145566, 145598, 145602, 672057, 674446, 674449, 674483, 674600, 674655, 674680, 674684, 674685, 674701, 674702, 674705, 674708, 674718, 674721, 674728, 674731, 674738, 674741, 674747, 674752, 674756, 674757, 674758, 674759, 674760, 674761, 674768, 674777, 674785, 674786, 674787, 674788, 674789, 674792, 674793, 674794, 674799, 674804, 674805, 674809, 674947, 674948, 674949, 674950, 674956, 674957, 674960, 674964, 674968, 674970, 674978, 677001, 648027, 142449, 142494, 663642, 140540, 140545, 142429, 145604, 660756, 660762, 660763, 660778, 660818, 674976, 674980, 674987, 674988, 142668, 143594, 143832, 143838, 143974, 145200, 145372, 145415, 145416, 145417, 145420, 145422, 145441, 145443, 145466, 145477, 145530, 145531, 145532, 145538, 145562, 145569, 145579, 145590, 145597, 645978, 657664, 660685, 660698, 660737, 660761, 663628, 663631, 663633, 663650, 663674, 665246, 668144, 673938, 674280, 674345, 674402, 674420, 674508, 674519, 674636, 674646, 674660, 674681, 674686, 674691, 674711, 674713, 674714, 674719, 674720, 674723, 674724, 674729, 674730, 674735, 674739, 674754, 674766, 674775, 674782, 674791, 674802, 674808, 674811, 674820, 674821, 674823, 674824, 674825, 674827, 674829, 674830, 674834, 674840, 674841, 674845, 674847, 674853, 674855, 674881, 674896, 674904, 674915, 674923, 674928, 674932, 674938, 674945, 674951, 674985, 674995, 674996, 674998, 674999, 675002, 675005, 675006, 675007, 675009, 675010, 675013, 675014, 675015, 681831, 683216, 683221, 765585, 144826, 145389, 672034, 672072, 674732, 674737, 674749, 687932, 765536],
        "start_point": [15.0339242, 49.340751],
        "end_point": [15.0677249, 49.3256828]
    }

    # "start_point": [15.1321449, 49.4054798],
    # "start_point": [15.017469, 49.433281]
    # "source" IN (3609, 6932, 726, 6305, 712, 5028, 5841, 5788)

    grades = '0, 1, 2, 3, 4, 5, 6'
    # print(grades)
    graph_data_input = prepare_data_for_graph(config, config['sectors'], grades)
    graph = build_graph(graph_data_input, [])
    nodes_with_degree_one = [node for node, degree in dict(graph.degree()).items() if degree == 1]
    # print("Uzly, které mají spojení pouze na jeden další uzel:", nodes_with_degree_one)

    points_to_use = find_points(config, nodes_with_degree_one)
    start_point = points_to_use[0]
    end_points = points_to_use[1]
    solutions = []
    solved_graphs = []
    for i in range(len(end_points)):
        pos_end_points = 0
        for end_point in end_points[i]:
            solution_results = solve_one_part(str(start_point[0]), str(end_point['id']), config, graph_data_input)
            if solution_results is not None:
                solutions.append(solution_results[0])
                solved_graphs.append(solution_results[1])
                # Serializace do JSON
                data = nx.node_link_data(solution_results[1])  # Převede graf do formátu pro serializaci
                with open(str(end_point['id']) + '_graph.json', 'w') as f:
                    json.dump(data, f)
                # break
            pos_end_points += 1
            if pos_end_points > 10:
                break

    for solution in solutions:
        print(solution)

    print(len(solved_graphs))
    print(len(solutions))
    for i in range(len(solved_graphs)):
        for j in range(len(solved_graphs)):
            if i != j:
                # Tak tyto testy evidentně nefungují
                # if nx.is_isomorphic(solved_graph, solved_graph_2):
                #     print("Graf G1 je stejný jako graf G2")
                #     print(solutions[pos][0]['id'] + " " + solutions[pos2][0]['id'])
                # GM = nx.isomorphism.GraphMatcher(solved_graph, solved_graph_2)
                # if GM.subgraph_is_isomorphic():
                #     print("Graf G1 je podgrafem grafu G2")
                #     print(solutions[pos][0]['id'] + " " + solutions[pos2][0]['id'])
                # GM = nx.isomorphism.GraphMatcher(solved_graph_2, solved_graph)
                # if GM.subgraph_is_isomorphic():
                #     print("Graf G2 je podgrafem grafu G1")
                #     print(solutions[pos][0]['id'] + " " + solutions[pos2][0]['id'])
                if are_graphs_identical(solved_graphs[i], solved_graphs[j]):
                    print("Graf " + solutions[i][0]['id'] + " je stejný jako graf " + solutions[j][0]['id'])
                else:
                    if is_subgraph(solved_graphs[i], solved_graphs[j]):
                        print("Graf " + solutions[i][0]['id'] + " je podgrafem grafu " + solutions[j][0]['id'])

                # if is_subgraph(solved_graphs[j], solved_graphs[i]):
                #     print("Graf G2 je podgrafem grafu G1")
                #     print(solutions[j][0]['id'] + " " + solutions[i][0]['id'])


    # with open('g.json', 'w') as go:
    #     go.write(json.dumps(graph_data_input))

    # solve_one_part('1138', '3908', config, graph_data_input)
    # solve_one_part('1138', '6465', config, graph_data_input)
    # solve_one_part('1138', '1112', config, graph_data_input)
    # solve_one_part('1138', '6489', config, graph_data_input)
    # solve_one_part('1138', '1134', config, graph_data_input)
    # solve_one_part('1138', '1132', config, graph_data_input)

    # solve_one_part('1138', '5915', config, graph_data_input)
    # solve_one_part('1138', '3756', config, graph_data_input)
    # solve_one_part('1138', '3498', config, graph_data_input)
    # solve_one_part('1138', '4022', config, graph_data_input)
    # solve_one_part('1138', '1126', config, graph_data_input)
    # solve_one_part('1138', '6466', config, graph_data_input)
    # solve_one_part('1138', '771', config, graph_data_input)
    # solve_one_part('1138', '4018', config, graph_data_input)

    # nx.shortest_path(graph, source, target, weight)
    # components = graph_components(graph)
    # for component in components:
    #     print(component)
    #     for item in component:
    #         print(dir(item))

    # edges = graph.edges(data=True)
    # for edge in edges:
    #     print(edge)
    #
    # nodes = list(graph.nodes)
    # random_nodes = random.sample(nodes, 2)

    # Odstranění hran, které tvoří nalezenou trasu, z grafu
    # Toto je část, kde vycházíme z toho, že z endpointu vede ještě jedna cesta, ale asi je to blbost.
    # for i in range(len(shortest_path) - 1):
    #     graph.remove_edge(shortest_path[i], shortest_path[i + 1])
    #
    # # Výpočet nejkratší trasy mezi těmito uzly
    # start_node = '6465'
    # end_node = '1138'
    # shortest_path = nx.shortest_path(graph, source=start_node, target=end_node, weight='weight')
    # shortest_path_length = nx.shortest_path_length(graph, source=start_node, target=end_node, weight='weight')
    #
    # # Výpis výsledků
    # print(f'Náhodně vybrané uzly: {start_node} a {end_node}')
    # print(f'Nejkratší trasa mezi {start_node} a {end_node} je: {shortest_path}')
    # print(f'Délka nejkratší trasy je: {shortest_path_length}')

    # New endpoint
    # graph = build_graph(graph_data_input, [])
    #
    # # Výpočet nejkratší trasy mezi těmito uzly
    # start_node = '1138'
    # end_node = '1112'
    # shortest_path = nx.shortest_path(graph, source=start_node, target=end_node, weight='weight')
    # shortest_path_length = nx.shortest_path_length(graph, source=start_node, target=end_node, weight='weight')
    #
    # # Výpis výsledků
    # print(f'Náhodně vybrané uzly: {start_node} a {end_node}')
    # print(f'Nejkratší trasa mezi {start_node} a {end_node} je: {shortest_path}')
    # print(f'Délka nejkratší trasy je: {shortest_path_length}')
    #
    # # Odstranění hran, které tvoří nalezenou trasu, z grafu
    # for i in range(len(shortest_path) - 1):
    #     graph.remove_edge(shortest_path[i], shortest_path[i + 1])
    #
    # # Výpočet nejkratší trasy mezi těmito uzly
    # start_node = '1112'
    # end_node = '1138'
    # shortest_path = nx.shortest_path(graph, source=start_node, target=end_node, weight='weight')
    # shortest_path_length = nx.shortest_path_length(graph, source=start_node, target=end_node, weight='weight')
    #
    # # Výpis výsledků
    # print(f'Náhodně vybrané uzly: {start_node} a {end_node}')
    # print(f'Nejkratší trasa mezi {start_node} a {end_node} je: {shortest_path}')
    # print(f'Délka nejkratší trasy je: {shortest_path_length}')

# test_me()
# test_approach_based_on_shortest_path()
# export_linies_into_xy_csv("/tmp/test_6642_0.shp")
