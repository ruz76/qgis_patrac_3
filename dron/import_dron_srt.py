import sys, os

def get_gpx_header(name):
    gpx_header = '<gpx xmlns="http://www.topografix.com/GPX/1/1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:wptx1="http://www.garmin.com/xmlschemas/WaypointExtension/v1" xmlns:gpxtrx="http://www.garmin.com/xmlschemas/GpxExtensions/v3" xmlns:gpxtpx="http://www.garmin.com/xmlschemas/TrackPointExtension/v1" xmlns:gpxx="http://www.garmin.com/xmlschemas/GpxExtensions/v3" xmlns:trp="http://www.garmin.com/xmlschemas/TripExtensions/v1" xmlns:adv="http://www.garmin.com/xmlschemas/AdventuresExtensions/v1" xmlns:prs="http://www.garmin.com/xmlschemas/PressureExtension/v1" xmlns:tmd="http://www.garmin.com/xmlschemas/TripMetaDataExtensions/v1" xmlns:vptm="http://www.garmin.com/xmlschemas/ViaPointTransportationModeExtensions/v1" xmlns:ctx="http://www.garmin.com/xmlschemas/CreationTimeExtension/v1" xmlns:gpxacc="http://www.garmin.com/xmlschemas/AccelerationExtension/v1" xmlns:gpxpx="http://www.garmin.com/xmlschemas/PowerExtension/v1" xmlns:vidx1="http://www.garmin.com/xmlschemas/VideoExtension/v1" version="1.1" creator="DogTrace GPS" xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd http://www.garmin.com/xmlschemas/WaypointExtension/v1 http://www8.garmin.com/xmlschemas/WaypointExtensionv1.xsd http://www.garmin.com/xmlschemas/TrackPointExtension/v1 http://www.garmin.com/xmlschemas/TrackPointExtensionv1.xsd http://www.garmin.com/xmlschemas/GpxExtensions/v3 http://www8.garmin.com/xmlschemas/GpxExtensionsv3.xsd http://www.garmin.com/xmlschemas/ActivityExtension/v1 http://www8.garmin.com/xmlschemas/ActivityExtensionv1.xsd http://www.garmin.com/xmlschemas/AdventuresExtensions/v1 http://www8.garmin.com/xmlschemas/AdventuresExtensionv1.xsd http://www.garmin.com/xmlschemas/PressureExtension/v1 http://www.garmin.com/xmlschemas/PressureExtensionv1.xsd http://www.garmin.com/xmlschemas/TripExtensions/v1 http://www.garmin.com/xmlschemas/TripExtensionsv1.xsd http://www.garmin.com/xmlschemas/TripMetaDataExtensions/v1 http://www.garmin.com/xmlschemas/TripMetaDataExtensionsv1.xsd http://www.garmin.com/xmlschemas/ViaPointTransportationModeExtensions/v1 http://www.garmin.com/xmlschemas/ViaPointTransportationModeExtensionsv1.xsd http://www.garmin.com/xmlschemas/CreationTimeExtension/v1 http://www.garmin.com/xmlschemas/CreationTimeExtensionsv1.xsd http://www.garmin.com/xmlschemas/AccelerationExtension/v1 http://www.garmin.com/xmlschemas/AccelerationExtensionv1.xsd http://www.garmin.com/xmlschemas/PowerExtension/v1 http://www.garmin.com/xmlschemas/PowerExtensionv1.xsd http://www.garmin.com/xmlschemas/VideoExtension/v1 http://www.garmin.com/xmlschemas/VideoExtensionv1.xsd">'
    gpx_header += '<metadata>'
    gpx_header += '<name>' + name + '</name>'
    gpx_header += '</metadata>'
    gpx_header += '<trk>'
    gpx_header += '<name>' + name + '</name>'
    gpx_header += '<extensions>'
    gpx_header += '<gpxx:TrackExtension>'
    gpx_header += '<gpxx:DisplayColor>Black</gpxx:DisplayColor>'
    gpx_header += '</gpxx:TrackExtension>'
    gpx_header += '</extensions>'
    return gpx_header

def get_outputs(input):
    with open(input) as f:
        lines = f.readlines()
        timest = ''
        lon = ''
        lat = ''
        csv_output = ''
        gpx_output = '<trkseg>'
        for line in lines:
            if len(line) > 10 and line[:4].isnumeric():
                timest = line.strip()
                lon = ''
                lat = ''
            if line.startswith('[latitude:'):
                # print(line.strip())
                items = line.strip().split(']')
                # print(items[0][11:])
                lat = items[0][11:]
                lon = items[1][13:]
                items2 = items[2].split('abs_alt: ')
                ele = items2[1][:-1]
            if len(lon) > 0:
                csv_output += timest + ';' + lon + ';' + lat + ';' + ele + '\n'
                gpx_output += '<trkpt lat="' + str(lat) + '" lon="' + str(lon) + '">\n'
                gpx_output += '<ele>' + str(ele) + '</ele>\n'
                gpx_output += '<time>' + timest.replace(' ', 'T') + 'Z</time>\n'
                gpx_output += '</trkpt>\n'
        gpx_output += '</trkseg>\n'
        return [csv_output, gpx_output]

def process_single_file():
    gpx_output = get_gpx_header('test name')
    outputs = get_outputs(sys.argv[1])
    print(len(outputs[1]))
    gpx_output += outputs[1]
    gpx_output += '</trk>\n'
    gpx_output += '</gpx>\n'
    with open(sys.argv[1] + '.gpx', 'w') as gpx_o:
        gpx_o.write(gpx_output)
    with open(sys.argv[1] + '.csv', 'w') as csv_o:
        csv_o.write(outputs[0])

def process_list_of_files(list_of_files, output_dir):
    gpx_output = get_gpx_header('test name')
    csv_output = ''
    for file_name in list_of_files:
        outputs = get_outputs(file_name)
        csv_output += outputs[0]
        gpx_output += outputs[1]
    gpx_output += '</trk>\n'
    gpx_output += '</gpx>\n'
    with open(os.path.join(output_dir, 'track.gpx'), 'w') as gpx_o:
        gpx_o.write(gpx_output)
    with open(os.path.join(output_dir, 'track.csv'), 'w') as csv_o:
        csv_o.write(csv_output)


process_single_file()
