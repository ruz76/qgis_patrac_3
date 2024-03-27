import math
import random

# Deprecated
def get_cluster_based_on_neighbors(clusters, sectors, sectors_neighbors):
    for sector in sectors:
        # The sector is not used yet
        if sector not in clusters:
            not_neighbor = True
            for neighbor in sectors_neighbors[sector]:
                # One of the sector neighbors is already a cluster
                if neighbor in clusters:
                    not_neighbor = False
            # If the sector is not a direct neighbor of the
            # TODO maybe exted to the neighbor-neighbor relation - to make them even more far away from each other
            if not_neighbor:
                return sector
    return -1


def get_cluster(clusters, sectors, placement, grid):
    distance = 1000000
    sector_id = -1
    for sector in sectors:
        # The sector is not used yet
        if sector not in clusters:
            curdistance = math.sqrt(math.pow(sectors[sector]['x'] - grid[placement][0], 2) + math.pow(sectors[sector]['y'] - grid[placement][1], 2))
            if curdistance < distance:
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
                if sector_in_neighbors in sectors:
                    clusters[cluster_id]['sectors'].append(sector_in_neighbors)
                    clusters[cluster_id]['length'] += sectors[sector_in_neighbors]['length']
                    return

def fix_not_assigned(sectors_not_assigned, clusters, sectors_neighbors, sectors, covers, iteration):
    print(sectors_not_assigned)
    items_to_remove = []
    for not_assigned_sector in sectors_not_assigned:
        print('Processing: ' + str(not_assigned_sector))
        cluster_candidates = {}
        for cluster_id in clusters:
            for sector_id in clusters[cluster_id]['sectors']:
                if not_assigned_sector in sectors_neighbors[sector_id]:
                    if iteration > 5:
                        cluster_candidates[cluster_id] = clusters[cluster_id]['length']
                    else:
                        if clusters[cluster_id]['length'] < covers[clusters[cluster_id]['unit']] * 1000:
                            cluster_candidates[cluster_id] = clusters[cluster_id]['length']
        print('Len cluster_candidates: ' + str(len(cluster_candidates)))
        if len(cluster_candidates) < 1:
            print("We have a problem with: " + str(not_assigned_sector))
        if len(cluster_candidates) > 0:
            cluster_id_candidate = - 1
            max_diff_length_candidate = -10000000
            for cluster_id in cluster_candidates:
                if (covers[clusters[cluster_id]['unit']] * 1000 - clusters[cluster_id]['length']) > max_diff_length_candidate:
                    cluster_id_candidate = cluster_id
                    max_diff_length_candidate = covers[clusters[cluster_id]['unit']] * 1000 - clusters[cluster_id]['length']
            clusters[cluster_id_candidate]['sectors'].append(not_assigned_sector)
            clusters[cluster_id_candidate]['length'] += sectors[not_assigned_sector]['length']
            print('Removing: ' + str(not_assigned_sector))
            items_to_remove.append(not_assigned_sector)

    # Remove the items
    for item in items_to_remove:
        sectors_not_assigned.remove(item)

def get_the_most_undersized_or_oversized_cluster(clusters, covers):
    cluster_id_candidate = - 1
    max_diff_length_candidate_in_percent = -10000000
    for cluster_id in clusters:
        print(str(cluster_id) + ': ' + str(clusters[cluster_id]['length']))
        difference = abs(covers[clusters[cluster_id]['unit']] * 1000 - clusters[cluster_id]['length'])
        current_max_diff_length_candidate_in_percent = difference / (covers[clusters[cluster_id]['unit']] * 1000 / 100)
        if current_max_diff_length_candidate_in_percent > max_diff_length_candidate_in_percent:
            cluster_id_candidate = cluster_id
            max_diff_length_candidate_in_percent = current_max_diff_length_candidate_in_percent
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

def move_sector_between_clusters(current_cluster_id, clusters, sectors, sectors_neighbors, covers):
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

    current_cluster_optimize_type = get_type_of_optimized_cluster(current_cluster_id, clusters, covers)
    if current_cluster_optimize_type == 1:
        cluster_id_candidate = get_cluster_candidate(cluster_candidates, clusters, covers, True)
        sector_id_candidate = get_sector_candidate(current_cluster_id, cluster_id_candidate, cluster_candidates, clusters, sectors, covers, sectors_neighbors, True)
    else:
        cluster_id_candidate = get_cluster_candidate(cluster_candidates, clusters, covers, False)
        sector_id_candidate = get_sector_candidate(current_cluster_id, cluster_id_candidate, cluster_candidates, clusters, sectors, covers, sectors_neighbors, False)

    # We know the final candidate, so we move it from its cluster into current processed cluster
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
    print(current_cluster_id + ' ' + cluster_id_candidate)
    print('After: ' + str(clusters[current_cluster_id]['length']) + ' ' + str(clusters[cluster_id_candidate]['length']))

def optimize_clusters(clusters, sectors, sectors_neighbors, covers):
    for i in range(100):
        cluster_id_to_optimize = get_the_most_undersized_or_oversized_cluster(clusters, covers)
        if cluster_id_to_optimize != -1:
            move_sector_between_clusters(cluster_id_to_optimize, clusters, sectors, sectors_neighbors, covers)
        else:
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

def get_used_searchers(searchers, total_length):
    covers = {
        "handler": 12,
        "pedestrian": 12,
        "rider": 16,
        "quad_bike": 20
    }

    used_searchers = {
        "handler": 0,
        "pedestrian": 0,
        "rider": 0,
        "quad_bike": 0
    }

    cover = searchers['handler'] * covers['handler']
    cover += searchers['pedestrian'] * covers['pedestrian']
    cover += searchers['rider'] * covers['rider']
    cover += searchers['quad_bike'] * covers['quad_bike']

    # We do not cover whole area
    if cover < total_length:
        diff = total_length - cover
        if diff < covers['pedestrian'] / 2:
            used_searchers = searchers
        else:
            used_searchers = searchers
            used_searchers['pedestrian'] += math.ceil(diff / covers['pedestrian'])

    # We cover perfectly the whole area - should not happen so often
    if cover == total_length:
        used_searchers = searchers

    # We do cover whole area and have more units
    if cover > total_length:
        diff = cover - total_length
        if diff < covers['pedestrian'] / 2:
            used_searchers = searchers
        else:
            cover = 0
            for i in range(searchers['handler']):
                cover += covers['handler']
                if cover <= total_length:
                    used_searchers['handler'] += 1
            for i in range(searchers['pedestrian']):
                cover += covers['pedestrian']
                if cover <= total_length:
                    used_searchers['pedestrian'] += 1
            for i in range(searchers['rider']):
                cover += covers['rider']
                if cover <= total_length:
                    used_searchers['rider'] += 1
            for i in range(searchers['quad_bike']):
                cover += covers['quad_bike']
                if cover <= total_length:
                    used_searchers['quad_bike'] += 1
            # TODO maybe necessary to add last unit once more

    return used_searchers

def make_clusters():
    total_length = 102
    max_area_length = 11
    searchers = {
        "handler": 1,
        "pedestrian": 1,
        "rider": 2,
        "quad_bike": 3
    }
    covers = {
        "handler": 12,
        "pedestrian": 12,
        "rider": 16,
        "quad_bike": 20
    }
    used_searchers = get_used_searchers(searchers, total_length)
    number_of_clusters = used_searchers['handler'] + used_searchers['pedestrian'] + used_searchers['rider'] + used_searchers['quad_bike']
    number_of_5_type_searchers = searchers['handler'] + searchers['pedestrian']
    clusters = {}
    sectors = {}
    sectors_neighbors = {}
    sectors_5_max_order = []
    bbox = []
    grid = []
    grid_size = math.ceil(math.sqrt(number_of_clusters))
    grid_rows = grid_size
    grid_cols = grid_size

    with open('/tmp/sectors_by_path_with_neighbors_agg.csv') as pri:
        lines = pri.readlines()
        for line in lines:
            sectors_5_max_order.append(line.strip().split(',')[0])

    with open('/tmp/sectors_with_paths_lengths.csv') as sec:
        lines = sec.readlines()
        for line in lines:
            items = line.strip().split(',')
            sectors[items[0]] = {"length": int(items[1]), "x": float(items[2]), "y": float(items[3])}

    with open('/tmp/sectors_neighbors.csv') as secn:
        lines = secn.readlines()
        for line in lines:
            items = line.strip().split(',')
            neighbors = items[1].split(';')
            sectors_neighbors[items[0]] = neighbors

    with open('/tmp/sectors_envelope.csv') as envelope:
        lines = envelope.readlines()
        bbox_str = lines[0].strip().split(',')
        bbox.append(float(bbox_str[0]))
        bbox.append(float(bbox_str[1]))
        bbox.append(float(bbox_str[2]))
        bbox.append(float(bbox_str[3]))

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

    # print(clusters)
    # print(sectors)
    # print(sectors_neighbors)
    # print(grid)

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
                    print(len(clusters))
                    break
    used_riders = 0
    used_quad_bike = 0
    for i in range(number_of_clusters):
        if grid_position_is_empty(i, clusters):
            cluster_id = get_cluster(clusters, sectors, i, grid)
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

    # print(clusters)

    # if len(lines) >= number_of_5_type_searchers:
    #     for i in range(number_of_5_type_searchers):
    #         clusters[lines[i].strip().split(',')[0]] = {
    #             "type": "5",
    #             "sectors": [lines[i].strip().split(',')[0]],
    #             "length": 0
    #         }


    # cluster_id = get_cluster(clusters, sectors, 6)

    # for i in range(number_of_clusters - number_of_5_type_searchers):
    #     print("New cluster")
    #     cluster_id = get_cluster(clusters, sectors, i)
    #     print(cluster_id)
    #     if cluster_id != -1:
    #         clusters[cluster_id] = {
    #             "type": "4",
    #             "sectors": [cluster_id],
    #             "length": 0
    #         }
    #     else:
    #         print("ERROR. Can not find enough clusters")
    #
    # for cluster_id in clusters:
    #     print(cluster_id)

    for it in range(100):
        print("Iteration: " + str(it))
        for cluster_id in clusters:
            print("Cluster: " + cluster_id)
            if clusters[cluster_id]['length'] < covers[clusters[cluster_id]['unit']] * 1000:
                print("Adding another sector into cluster.")
                append_sector_into_cluster(clusters, sectors, sectors_neighbors, cluster_id)
            else:
                print("Cluster is full. Skipping.")

    # print(clusters)
    print_clusters(clusters)

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
        print("Fix not assigned. Iteration: " + str(i))
        fix_not_assigned(sectors_not_assigned, clusters, sectors_neighbors, sectors, covers, i)

    # print(clusters)
    # print_clusters(clusters)
    # print_clusters_2(clusters)

    optimize_clusters(clusters, sectors, sectors_neighbors, covers)
    # print(clusters)
    print_clusters_2(clusters)
    print_clusters(clusters)

make_clusters()
