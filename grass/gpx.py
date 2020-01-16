
#!/usr/bin/env python

import glob, os
import sys, os.path
import subprocess
import csv
import io
from shutil import copyfile
import fnmatch
from grass_config import *

# DATA
# define GRASS DATABASE
# add your path to grassdata (GRASS GIS database) directory
DATAPATH=str(sys.argv[1])
PLUGINPATH=str(sys.argv[2]) 
gisdb = DATAPATH + "/grassdata"
# the following path is the default path on MS Windows
# gisdb = os.path.join(os.path.expanduser("~"), "Documents/grassdata")

# specify (existing) location and mapset
location = "wgs84"
mapset   = "PERMANENT"


########### SOFTWARE
if sys.platform.startswith('linux'):
    # we assume that the GRASS GIS start script is available and in the PATH
    # query GRASS 7 itself for its GISBASE
    grass7bin = grass7bin_lin
    # query GRASS 7 itself for its GISBASE
    startcmd = [grass7bin, '--config', 'path']

    p = subprocess.Popen(startcmd, shell=False,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    if p.returncode != 0:
        print("ERROR: Cannot find GRASS GIS 7 start script (%s)" % startcmd)
        sys.exit(-1)
    # print(out)
    gisbase = out.strip('\n\r')
elif sys.platform.startswith('win'):
    grass7bin = grass7bin_win
    gisbase = 'C:/OSGEO4W64/apps/grass/grass78'
else:
    raise OSError('Platform not configured.')

# Set GISBASE environment variable
os.environ['GISBASE'] = gisbase
# the following not needed with trunk
os.environ['PATH'] += os.pathsep + os.path.join(gisbase, 'extrabin')
# add path to GRASS addons
home = os.path.expanduser("~")
os.environ['PATH'] += os.pathsep + os.path.join(home, '.grass7', 'addons', 'scripts')

# define GRASS-Python environment
gpydir = os.path.join(gisbase, "etc", "python")
sys.path.append(gpydir)

########### DATA
# Set GISDBASE environment variable
os.environ['GISDBASE'] = gisdb
 
# import GRASS Python bindings (see also pygrass)
import grass.script as gscript
import grass.script.setup as gsetup
#from grass.pygrass.modules.shortcuts import raster as r
 
###########
# launch session
gsetup.init(gisbase,
            gisdb, location, mapset)
 
#gscript.message('Current GRASS GIS 7 environment:')
#print gscript.gisenv()

SECTOR=str(sys.argv[3])
DATEFROM=str(sys.argv[4])
DATETO=str(sys.argv[5])
PATH=str(sys.argv[6])

#Creates output directory
if not os.path.exists(DATAPATH + '/search/gpx/' + SECTOR):
    os.makedirs(DATAPATH + '/search/gpx/' + SECTOR)

#Removes previously created output in WKT
if os.path.isfile(DATAPATH + '/search/temp/out.csv'):
    os.remove(DATAPATH + '/search/temp/out.csv')

#Path to GPX is send as parameter
print(DATAPATH + '/search/temp')
for root, dirnames, filenames in os.walk(DATAPATH + '/search/temp'):
    for f in fnmatch.filter(filenames, '*.gpx'):
        print(f)
        if os.path.isfile(os.path.join(root, f.decode('utf8'))):
            #Copy original files
            copyfile(os.path.join(root, f.decode('utf8')), DATAPATH + '/search/gpx/' + SECTOR + '/' + os.path.basename(f))
            #Extracts from file records in time extent
            #transformInstance.transform_xslt_time(PLUGINPATH, os.path.join(root, f.decode('utf8')), DATAPATH + '/search/temp/out.csv', DATEFROM, DATETO)
            if sys.platform.startswith('win'):
                p = subprocess.Popen((PLUGINPATH + '/xslt/run_xslt.bat', PLUGINPATH, os.path.join(root, f.decode('utf8')), DATAPATH + '/search/temp/out.csv', DATEFROM, DATETO))
                p.wait()
            else:
                p = subprocess.Popen(('bash', PLUGINPATH + '/xslt/run_xslt.sh', PLUGINPATH,
                                      os.path.join(root, f.decode('utf8')), DATAPATH + '/search/temp/out.csv', DATEFROM,
                                      DATETO))
                p.wait()

#Reads GML header
header = io.open(PLUGINPATH + '/xslt/gml_header.gml', encoding='utf-8', mode='r').read()
#Writes GML header
f = io.open(DATAPATH + '/search/temp/out_polyline.gml', encoding='utf-8', mode='w')
f.write(header)

#Reads CVS created by XSTL
with open(DATAPATH + '/search/temp/out.csv') as csvDataFile:
    csvReader = csv.reader(csvDataFile, delimiter='|')
    counterId = 0
    for row in csvReader:
        ##print(row)
        #For each row creates one point in polyline
        f.write(u'<gml:featureMember>\n')
        f.write(u'<ogr:sample fid="segment.' + str(counterId) + u'">\n')
        f.write(u'<ogr:geometryProperty><gml:LineString><gml:coordinates>\n')
        startTime = ""
        endTime = ""
        for item in row:
            if len(item) > 10:
                coords = item.split(";")
                f.write(coords[1] + u',' + coords[0] + u' ')
                if startTime == "":
                    startTime = coords[2]
                else:
                    endTime = coords[2]
        # Finished the polyline
        f.write(u'</gml:coordinates></gml:LineString></ogr:geometryProperty>\n')
        # Finishes the feature
        f.write(u'<ogr:startTime>' + startTime + u'</ogr:startTime>\n')
        f.write(u'<ogr:endTime>' + endTime + u'</ogr:endTime>\n')
        f.write(u'</ogr:sample>\n')
        f.write(u'</gml:featureMember>\n')
        counterId += 1
#Finished the GML
f.write(u'</ogr:FeatureCollection>')
f.close()

#TODO - make it faster without GRASSS
#Imports GML to GRASS
print(gscript.read_command('v.in.ogr', input=DATAPATH + '/search/temp/out_polyline.gml', output='out_polyline', flags='o', overwrite=True))
#Exports SHP from imported GML
print(gscript.read_command('v.out.ogr', format='ESRI_Shapefile', input='out_polyline', output=DATAPATH + '/search/shp/' + SECTOR + '.shp', overwrite=True))
