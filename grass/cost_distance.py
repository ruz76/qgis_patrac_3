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

try:
    print(gscript.read_command('r.mask', flags="r"))
except:
    print("NO MASK")

#Removes reclass rules
rules_percentage_path = PLUGIN_PATH + '/grass/rules_percentage.txt'
if os.path.exists(rules_percentage_path):
    os.remove(rules_percentage_path)

#Reads coords from coords.txt written by patracdockwidget.getArea
print(gscript.read_command('g.remove', type='vector', name='coords'))
print(gscript.read_command('g.remove', type='raster', name='coords'))
print(gscript.read_command('v.in.ascii', input=PLUGIN_PATH + '/grass/coords.txt', output='coords', separator='comma' , overwrite=True))
#Converts to the raster
print(gscript.read_command('v.to.rast', input='coords', output='coords', use='cat' , overwrite=True))

#Tests if the coord is not in null area
print(gscript.read_command('r.mapcalc', expression='coords_friction=friction * coords', overwrite=True))
stats = gscript.parse_command('r.univar', map='coords_friction', flags='g')

def move_from_null():
    print("Moving from null")
    # if the min value is null
    print(gscript.read_command('r.mapcalc', expression='friction_null_rec=if(isnull(friction), 1, null())',
                               overwrite=True))
    print(gscript.read_command('r.buffer', input='friction_null_rec', output='friction_null_rec_buf_10', distances='10',
                               overwrite=True))
    print(gscript.read_command('r.null', map='friction_null_rec_buf_10', setnull='1', overwrite=True))
    print(gscript.read_command('r.mapcalc', expression='friction_flat=1', overwrite=True))
    print(gscript.read_command('r.cost', input='friction_flat', output='friction_flat_cost', start_points='coords',
                               overwrite=True))
    print(gscript.read_command('r.mapcalc',
                               expression='friction_flat_cost_buf=friction_flat_cost*friction_null_rec_buf_10',
                               overwrite=True))
    stats2 = gscript.parse_command('r.univar', map='friction_flat_cost_buf', flags='g')
    try:
        # Reads min value
        MIN = float(stats2['min'])
        f = open(PLUGIN_PATH + '/grass/move.rules', 'w')
        f.write(str(MIN) + ' = 1\n')
        f.write('* = null\n')
        f.write('end')
        f.close()
        print(gscript.read_command('r.reclass', input='friction_flat_cost_buf', output='coords',
                                   rules=PLUGIN_PATH + '/grass/move.rules', overwrite=True))
        print(gscript.read_command('r.to.vect', input='coords', output='coords', type='point', overwrite=True))
    except:
        print("Problem with moving of the point from null area")

try:
    # Reads min value
    MIN = float(stats['min'])
    print("MINIMUM: " + str(MIN))
    if str(MIN) == "nan":
        move_from_null()
except:
    move_from_null()


#Reads radial CSV with WKT of triangles writtent by patracdockwidget.generateRadialOnPoint
print(gscript.read_command('v.in.ogr', input=PLUGIN_PATH + '/grass/radial.csv', output='radial', flags='o' , overwrite=True))
#Converts triangles to raster
print(gscript.read_command('v.to.rast', input='radial', output='radial', use='cat', overwrite=True))
#Reclass triangles according to rules created by patracdockwidget.writeAzimuthReclass
print(gscript.read_command('r.reclass', input='radial', output='radial' + PLACE_ID, rules=PLUGIN_PATH + '/grass/azimuth_reclass.rules', overwrite=True))
#Combines friction_slope with radial (direction)
print(gscript.read_command('r.mapcalc', expression='friction_radial' + PLACE_ID + ' = friction + radial' + PLACE_ID, overwrite=True))

#Reads distances from distances selected (or defined) by user
distances_f=open(PLUGIN_PATH + "/grass/distances.txt")
lines=distances_f.readlines()
DISTANCES=lines[TYPE-1]

#Distances methodology
print(gscript.read_command('r.buffer', input='coords', output='distances' + PLACE_ID, distances=DISTANCES , overwrite=True))
#Friction methodology
print(gscript.read_command('r.walk', friction='friction_radial' + PLACE_ID, elevation='dem', output='cost' + PLACE_ID, start_points='coords' , overwrite=True))

#Creates new reclass rules
rules_percentage_f = open(rules_percentage_path, 'w')
#Creates empty raster with zero values
print(gscript.read_command('r.mapcalc', expression='distances' + PLACE_ID + '_costed = 0', overwrite=True))

# we have to start on cat 3, so on min of the ring for 20%
cat=3
#Percentage for distances
variables = [10, 20, 30, 40, 50, 60, 70, 80]
PREVMIN = 0
for i in variables:
    print(i)
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
        print(str(MIN))
        #Reads max value
        MAX = float(stats['max'])
        print(str(MAX))
        #Minimum value and maximum value is used as extent for relass of the whole cost layer
        #rules_percentage_f.write(str(MIN) + ' thru ' + str(MAX) + ' = ' + str(i) + '\n')
        if str(PREVMIN) != 'nan' and str(MIN) != 'nan':
            rules_percentage_f.write(str(PREVMIN) + ' thru ' + str(MIN) + ' = ' + str(i) + '\n')
        PREVMIN = MIN
    except:
        print("Problem with category " + str(cat) + " " + str(i) + "%")
    cat = cat + 1

#Add 95% category
if str(PREVMIN) != 'nan' and str(MAX) != 'nan':
    rules_percentage_f.write(str(PREVMIN) + ' thru ' + str(MAX) + ' = 95\n')

#Finish reclass rules
rules_percentage_f.write('end')
rules_percentage_f.close()

#Finaly reclass whole cost layer based on min and max values for each ring
print(gscript.read_command('r.reclass', input='cost' + PLACE_ID, output='distances' + PLACE_ID + '_costed', rules=PLUGIN_PATH + '/grass/rules_percentage.txt', overwrite=True))


