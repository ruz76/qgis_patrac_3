#!/usr/bin/env python

import os
import sys
import subprocess
from grass_config import *

# DATA
# define GRASS DATABASE
# add your path to grassdata (GRASS GIS database) directory
DATAPATH=str(sys.argv[1]) 
gisdb = DATAPATH + "/grassdata"
# the following path is the default path on MS Windows
# gisdb = os.path.join(os.path.expanduser("~"), "Documents/grassdata")

# specify (existing) location and mapset
location = "jtsk"
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
    # gisbase = out.strip('\n\r')
    gisbase = out.decode('utf-8').strip('\n\r')
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

PLUGIN_PATH=str(sys.argv[2]) 
XMIN=float(sys.argv[3])
YMIN=float(sys.argv[4])
XMAX=float(sys.argv[5])
YMAX=float(sys.argv[6])
DATAINPUTPATH=str(sys.argv[7])

#Sets the region for export
#g.region e=-641060.857143 w=-658275.142857 n=-1036549.0 s=-1046549.0
print(gscript.read_command('g.region', e=XMAX, w=XMIN, n=YMAX, s=YMIN, res='5'))

#Imports landuse
print(gscript.read_command('r.in.bin', flags="h", bytes=2, output='landuse', input=DATAPATH+'/grassdata/landuse.bin', overwrite=True))
# Delete the file
os.remove(DATAPATH+'/grassdata/landuse.bin')

#Imports friction_slope
print(gscript.read_command('r.in.bin', flags="hf", anull=-99, output='friction_slope', input=DATAPATH+'/grassdata/friction_slope.bin', overwrite=True))
# Delete the file
os.remove(DATAPATH+'/grassdata/friction_slope.bin')

#Imports friction
print(gscript.read_command('r.in.bin', flags="h", bytes=2, anull=100, output='friction', input=DATAPATH+'/grassdata/friction.bin', overwrite=True))
# Delete the file
os.remove(DATAPATH+'/grassdata/friction.bin')

#Imports dem
print(gscript.read_command('r.in.bin', flags="hf", output='dem', input=DATAPATH+'/grassdata/dem.bin', overwrite=True))
# Delete the file
os.remove(DATAPATH+'/grassdata/dem.bin')

#If the data are from ZABAGED
if os.path.isfile(DATAINPUTPATH+'/vektor/ZABAGED/line_x/merged_polygons_groupped.shp'):
    print(gscript.read_command('v.in.ogr', output='sectors_group_to_append', input=DATAINPUTPATH+'/vektor/ZABAGED/line_x', layer='merged_polygons_groupped', snap=0.01, spatial=str(XMIN)+','+str(YMIN)+','+str(XMAX)+','+str(YMAX), overwrite=True, flags="o"))
    print(gscript.read_command('r.reclass', input='landuse', output='landuse_type', rules=PLUGIN_PATH+'/grass/landuse_type_zbg.rules', overwrite=True))

#If the data are from OSM
if os.path.isfile(DATAINPUTPATH+'/vektor/OSM/line_x/merged_polygons_groupped.shp'):
    print(gscript.read_command('v.in.ogr', output='sectors_group_to_append', input=DATAINPUTPATH+'/vektor/OSM/line_x', layer='merged_polygons_groupped', snap=0.01, spatial=str(XMIN)+','+str(YMIN)+','+str(XMAX)+','+str(YMAX), overwrite=True, flags="o"))
    print(gscript.read_command('r.reclass', input='landuse', output='landuse_type', rules=PLUGIN_PATH+'/grass/landuse_type_osm.rules', overwrite=True))


#Adds progress columns
print(gscript.read_command('v.db.addcolumn', map='sectors_group_to_append', layer='1', columns='stav INTEGER', overwrite=True))
print(gscript.read_command('v.db.addcolumn', map='sectors_group_to_append', layer='1', columns='prostredky VARCHAR(254)', overwrite=True))

#Computes areas
print(gscript.read_command('v.db.addcolumn', map='sectors_group_to_append', layer='1', columns='area_ha DOUBLE PRECISION', overwrite=True))
print(gscript.read_command('v.to.db', map='sectors_group_to_append', layer='1', option='area', units='hectares', columns='area_ha', overwrite=True))
#Adds label column
print(gscript.read_command('v.db.addcolumn', map='sectors_group_to_append', layer='1', columns='label VARCHAR(50)', overwrite=True))
print(gscript.read_command('v.db.addcolumn', map='sectors_group_to_append', layer='1', columns='poznamka VARCHAR(254)', overwrite=True))
print(gscript.read_command('v.db.addcolumn', map='sectors_group_to_append', layer='1', columns='cas_od VARCHAR(50)', overwrite=True))
print(gscript.read_command('v.db.addcolumn', map='sectors_group_to_append', layer='1', columns='cas_do VARCHAR(50)', overwrite=True))
#Exports sectors with comuted areas
print(gscript.read_command('v.out.ogr', format='ESRI_Shapefile', input='sectors_group_to_append', output=DATAPATH +'/pracovni/sektory_group_to_append.shp', overwrite=True))
