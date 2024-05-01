import sys
with open(sys.argv[1]) as f:
    lines = f.readlines()
    timest = ''
    lon = ''
    lat = ''
    for line in lines:
        if line.startswith('2024-'):
            timest = line.strip()
            lon = ''
            lat = ''
        if line.startswith('[latitude:'):
            # print(line.strip())
            items = line.strip().split(']')
            # print(items[0][11:])
            lat = items[0][11:]
            lon = items[1][13:]
        if len(lon) > 0:
            print(timest + ';' + lon + ';' + lat)
