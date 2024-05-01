import sys
import json

with open(sys.argv[1]) as f:
    lines = f.readlines()
    current_track = ''
    points = []
    point_pos = -1
    output = {}
    id_sec = 0
    for line in lines:
        if 'ID: ' in line:
            id_sec += 1
            # print(line.strip())
            current_track = line.strip().split(':')[1].split(']')[0].strip() + "_" + str(id_sec)
            point_pos = -1
            output[current_track] = {"ts": [], "lat": [], "lon": []}
        if line.startswith('2024-'):
            output[current_track]["ts"].append(line.strip())
        if line.startswith('15.'):
            items = line.strip().split(' ')
            output[current_track]["lon"].append(items[0])
            output[current_track]["lat"].append(items[1])
    for key in output:
        for i in range(len(output[key]['ts'])):
            if i < len(output[key]['lon']) and i < len(output[key]['lat']):
                print(key + ';' + output[key]['ts'][i] + ';' + output[key]['lon'][i] + ';' + output[key]['lat'][i])

    # print(json.dumps(output))
