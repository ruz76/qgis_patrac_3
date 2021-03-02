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
PLACE_ID=sys.argv[3]
TYPE=int(sys.argv[4])

#Tests if the coord is not in null area
print(gscript.read_command('r.mapcalc', expression='friction_slope_radial' + PLACE_ID + ' = friction_slope + radial' + PLACE_ID, overwrite=True))
# r.mapcalc expression='coords_friction_slope=friction_slope * coords'
#Reads coords from coords.txt written by patracdockwidget.getArea
print(gscript.read_command('v.in.ascii', input=PLUGIN_PATH + '/grass/coords.txt', output='coords', separator='comma' , overwrite=True))
#Converts to the raster
print(gscript.read_command('v.to.rast', input='coords', output='coords', use='cat' , overwrite=True))
#Reads radial CSV with WKT of triangles writtent by patracdockwidget.generateRadialOnPoint
print(gscript.read_command('v.in.ogr', input=PLUGIN_PATH + '/grass/radial.csv', output='radial', flags='o' , overwrite=True))
#Converts triangles to raster
print(gscript.read_command('v.to.rast', input='radial', output='radial', use='cat', overwrite=True))
#Reclass triangles according to rules created by patracdockwidget.writeAzimuthReclass
print(gscript.read_command('r.reclass', input='radial', output='radial' + PLACE_ID, rules=PLUGIN_PATH + '/grass/azimuth_reclass.rules', overwrite=True))
#Combines friction_slope with radial (direction)
print(gscript.read_command('r.mapcalc', expression='friction_slope_radial' + PLACE_ID + ' = friction_slope + radial' + PLACE_ID, overwrite=True))

#Reads distances from distances selected (or defined) by user
distances_f=open(PLUGIN_PATH + "/grass/distances.txt")
lines=distances_f.readlines()
DISTANCES=lines[TYPE-1]

#Distances methodology
print(gscript.read_command('r.buffer', input='coords', output='distances' + PLACE_ID, distances=DISTANCES , overwrite=True))
#Friction methodology
print(gscript.read_command('r.cost', input='friction_slope_radial' + PLACE_ID, output='cost' + PLACE_ID, start_points='coords' , overwrite=True))

#Removes reclass rules
os.remove(PLUGIN_PATH + '/grass/rules_percentage.txt')
#Creates new reclass rules
rules_percentage_f = open(PLUGIN_PATH + '/grass/rules_percentage.txt', 'w')
#Creates empty raster with zero values
print(gscript.read_command('r.mapcalc', expression='distances' + PLACE_ID + '_costed = 0', overwrite=True))

#Have no idea why cat=2
#Maybe the cat=1 is the point from the search is done
cat=2
#Percentage for distances
variables = [10, 20, 30, 40, 50, 60, 70, 80, 95]
for i in variables:
    #Writes rules for the category so we have only one ring in the output
    f = open(PLUGIN_PATH + '/grass/rules.txt', 'w')
    f.write(str(cat) + ' = 1\n')
    f.write('end')
    f.close()
    #Gets only one ring
    print(gscript.read_command('r.reclass', input='distances' + PLACE_ID, output='distances' + PLACE_ID + '_' + str(i), rules=PLUGIN_PATH + '/grass/rules.txt', overwrite=True))
    #Combines ring with friction (cost algorithm result)
    print(gscript.read_command('r.mapcalc', expression='cost' + PLACE_ID + '_distances_' + str(i) + ' = distances' + PLACE_ID + '_' + str(i) + ' * cost' + PLACE_ID, overwrite=True))
    #Gets basic statistics for cost values in ring
    stats = gscript.parse_command('r.univar', map='cost' + PLACE_ID + '_distances_' + str(i), flags='g')
    #print stats
    try:
        #Reads min value
        MIN = float(stats['min'])
        #Reads max value
        MAX = float(stats['max'])
        #Minimum value and maximum value is used as extent for relass of the whole cost layer
        rules_percentage_f.write(str(MIN) + ' thru ' + str(MAX) + ' = ' + str(i) + '\n')
    except:
        print "Problem with category " + str(cat) + " " + str(i) + "%"
    cat = cat + 1

#Finish reclass rules
rules_percentage_f.write('end')
rules_percentage_f.close()

#Finaly reclass whole cost layer based on min and max values for each ring
print(gscript.read_command('r.reclass', input='cost' + PLACE_ID, output='distances' + PLACE_ID + '_costed', rules=PLUGIN_PATH + '/grass/rules_percentage.txt', overwrite=True))


