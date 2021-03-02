#!/usr/bin/env python

import os
import sys
import subprocess
from grass_config import *
import time

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
 
#gscript.message('Current GRASS GIS 7 environment:')
#print gscript.gisenv()

MIN=str(sys.argv[3])
MAX=str(sys.argv[4])
print("MIN/MAX:" +  MIN + " " + MAX)

print(gscript.read_command('v.in.ogr', output='sectors_group_modified', input=DATAPATH +'/pracovni', layer='sektory_group', snap=0.01, overwrite=True, flags="o"))
print(gscript.read_command('r.mapcalc', expression='distances_costed_cum_selected = if(distances_costed_cum<='+MIN+'||distances_costed_cum>='+MAX+', null(), 1)', overwrite=True))
print(gscript.read_command('r.to.vect', input='distances_costed_cum_selected',  output='distances_costed_cum_selected', type='area', overwrite=True))
print(gscript.read_command('v.select', ainput='sectors_group_modified', binput='distances_costed_cum_selected', output='sektory_group_selected', overwrite=True))
#Linux
#print gscript.read_command('v.out.ogr', input='sektory_group_selected', output=DATAPATH +'/pracovni/', overwrite=True)
#Windows
print(gscript.read_command('v.out.ogr', format='ESRI_Shapefile', input='sektory_group_selected', output=DATAPATH +'/pracovni/sektory_group_selected.shp', overwrite=True))
print(gscript.read_command('v.out.ogr', format='CSV', input='sektory_group_selected', output=DATAPATH +'/pracovni/sektory_group_selected.csv', overwrite=True))

# time.sleep(30)
