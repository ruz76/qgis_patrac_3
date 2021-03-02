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

# print(sys.path)

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
DATAOUTPUTPATH=str(sys.argv[7])
print(sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6])

#Sets the region for export
#g.region e=-641060.857143 w=-658275.142857 n=-1036549.0 s=-1046549.0
try:
    # Removes mask to be ready for another calculations for whole area
    print(gscript.read_command('r.mask', flags="r"))
except:
    print("MASK NOT USED")
print(gscript.read_command('g.region', e=XMAX, w=XMIN, n=YMAX, s=YMIN))
#Imports region polygon from GeoJSON
print(gscript.read_command('v.in.ogr', flags="o", input=DATAOUTPUTPATH+'/pracovni/cregion.geojson', output='cregion', overwrite=True))

def export_current(name):
    #Selects VODTOK according to cregion
    print(gscript.read_command('v.select', ainput=name, binput='cregion', output=name + '_cregion', overwrite=True))
    #Exports selected VODTOK
    print(gscript.read_command('v.out.ogr', format='ESRI_Shapefile', input=name + '_cregion', output=DATAOUTPUTPATH +'/pracovni/' + name.lower() + '.shp', overwrite=True))

# exports VODTOK
export_current('VODTOK')
# ecports CESTA
export_current('CESTA')
# exports LESPRU
export_current('LESPRU')
