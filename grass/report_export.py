# -*- coding: utf-8 -*-
# !/usr/bin/env python

import os
import sys
import subprocess
import math
import io
import csv
from grass_config import *
from os import path
import time

# DATA
# define GRASS DATABASE
# add your path to grassdata (GRASS GIS database) directory
DATAPATH = str(sys.argv[1])
gisdb = DATAPATH + "/grassdata"
# the following path is the default path on MS Windows
# gisdb = os.path.join(os.path.expanduser("~"), "Documents/grassdata")

# specify (existing) location and mapset
location = "jtsk"
mapset = "PERMANENT"

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

# from grass.pygrass.modules.shortcuts import raster as r

###########
# launch session
gsetup.init(gisbase,
            gisdb, location, mapset)

PLUGIN_PATH = str(sys.argv[2])
COUNT = int(sys.argv[3])
LABELS = str(sys.argv[4])
LABELS = LABELS.split('!')

# Imports sektory_group_selected.shp to grass layer sektory_group_selected_modified (may be modified by user)
print(gscript.read_command('v.import', input=DATAPATH + '/pracovni/sektory_group_selected.shp',
                           layer='sektory_group_selected', output='sektory_group_selected_modified', overwrite=True))


# Sets area of areas to zero
SUM_P1 = 0
SUM_P2 = 0
SUM_P3 = 0
SUM_P4 = 0
SUM_P5 = 0
SUM_P6 = 0
SUM_P7 = 0
SUM_P8 = 0
SUM_P9 = 0
SUM_P10 = 0

print("COUNT: " + str(COUNT))
print("LABELS: " + str(LABELS))

# Loops via all selected search sectors based on number of sectors
for i in range(1, COUNT + 1):
    print(i, LABELS[i-1])
    f = io.open(DATAPATH + '/pracovni/report.html.' + str(i), encoding='utf-8', mode='w')
    # vybrani jednoho sektoru dle poradi
    # Selects one sector based on order (attribute cats is from 1 to number of items)
    # print gscript.read_command('v.extract', input='sektory_group_selected_modified', output='sektory_group_selected_modified_' + str(i), where="cat='"+str(i)+"'", overwrite=True)
    # ziskani atributu plocha a label
    # Gets attribute plocha (area) and label
    # VALUES=gscript.read_command('v.db.select', map='sektory_group_selected_modified_' + str(i), columns='label,area_ha', flags="c")
    # Pipe is delimiter of v.db.select output
    # VALUESITEMS=VALUES.split('|')

    # zamaskovani rastru s vyuzitim polygonu sektoru
    # Mask working area based on are of current sector
    REPORT = ""
    #print(DATAPATH + "/../../vektor/ZABAGED/line_x/" + LABELS[i-1] + ".stats")
    if path.exists(DATAPATH + "/../../vektor/ZABAGED/line_x/" + LABELS[i] + ".stats"):
        REPORT = open(DATAPATH + "/../../vektor/ZABAGED/line_x/" + LABELS[i] + ".stats", 'r').read()
        print(REPORT)
    else:
        print(gscript.read_command('r.mask', vector='sektory_group_selected_modified', where="cat='" + str(i) + "'",
                               overwrite=True))

        # ziskani reportu - procenta ploch v sektoru
        # Gets stats for landuse areas in masked region
        REPORT = gscript.read_command('r.stats', input='landuse_type', separator='pipe', flags='plna')
        #print(REPORT)

    if REPORT == "":
        # Some problem occured
        f.write(u'<div id="a' + str(i) + 's">\n')
        f.write(u'Při zpracování sektoru nastala chyba.')
        f.write(u'</div>\n')
        f.close()
        continue

    # Sets areas of types of areas to zero
    # TODO - vyjasnit zarazeni typu + mozna pouzit i letecke snimky - nejaká jednoduchá automaticka rizena klasifikace
    P1 = 0  # volny schudny bez porostu (louky, pole ) - nejsem schopen zatim z dat identifikovat, mozna dle data patrani, v zime bude pole bez porostu a louka asi taky
    P2 = 0  # volny schudny s porostem (louky, pole ) - zatim tedy bude vse s porostem
    P3 = 0  # volny obtizne schudny (hory, skaly, lomy) - v prostoru mam lomy, skaly asi taky nejsem zatim schopen identifikovat
    P4 = 0  # porost lehce pruchozi (les bez prekazek) - asi vsechn les, kde neni krovi
    P5 = 0  # porost obtizne pruchozi (houstiny, skaly) - asi les s krovinami
    P6 = 0  # zastavene uzemi mest a obci
    P7 = 0  # mestske parky a hriste s pohybem osob - pohyb osob nejsem schopen posoudit, tedy asi co je zahrada bude bez pohybu a co je park bude s pohybem
    P8 = 0  # mestske parky a hriste bez osob
    P9 = 0  # vodni plocha
    P10 = 0  # ostatni

    REPORTITEMS = REPORT.splitlines(False)

    # Decides for each type of area from REPORT in which category belongs
    try:
        for REPORTITEM in REPORTITEMS:
            REPORTITEMVALUES = REPORTITEM.split('|')
            if REPORTITEMVALUES[0] == '1':
                P1 = P1 + float(REPORTITEMVALUES[3].split('%')[0])
                SUM_P1 = SUM_P1 + float(REPORTITEMVALUES[2])
            if REPORTITEMVALUES[0] == '2':
                P2 = P2 + float(REPORTITEMVALUES[3].split('%')[0])
                SUM_P2 = SUM_P2 + float(REPORTITEMVALUES[2])
            if REPORTITEMVALUES[0] == '3':
                P3 = P3 + float(REPORTITEMVALUES[3].split('%')[0])
                SUM_P3 = SUM_P3 + float(REPORTITEMVALUES[2])
            if REPORTITEMVALUES[0] == '4':
                P4 = P4 + float(REPORTITEMVALUES[3].split('%')[0])
                SUM_P4 = SUM_P4 + float(REPORTITEMVALUES[2])
            if REPORTITEMVALUES[0] == '5':
                P5 = P5 + float(REPORTITEMVALUES[3].split('%')[0])
                SUM_P5 = SUM_P5 + float(REPORTITEMVALUES[2])
            if REPORTITEMVALUES[0] == '6':
                P6 = P6 + float(REPORTITEMVALUES[3].split('%')[0])
                SUM_P6 = SUM_P6 + float(REPORTITEMVALUES[2])
            if REPORTITEMVALUES[0] == '7':
                P7 = P7 + float(REPORTITEMVALUES[3].split('%')[0])
                SUM_P7 = SUM_P7 + float(REPORTITEMVALUES[2])
            if REPORTITEMVALUES[0] == '8':
                P8 = P8 + float(REPORTITEMVALUES[3].split('%')[0])
                SUM_P8 = SUM_P8 + float(REPORTITEMVALUES[2])
            if REPORTITEMVALUES[0] == '9':
                P9 = P9 + float(REPORTITEMVALUES[3].split('%')[0])
                SUM_P9 = SUM_P9 + float(REPORTITEMVALUES[2])
            if REPORTITEMVALUES[0] == '10':
                P10 = P10 + float(REPORTITEMVALUES[3].split('%')[0])
                SUM_P10 = SUM_P10 + float(REPORTITEMVALUES[2])
    except ValueError:
        print("The statistic for current sector is invalid, can not compute.")

    # Corect 100%
    if P1 > 100:
        P1 = 100
    if P2 > 100:
        P2 = 100
    if P3 > 100:
        P3 = 100
    if P4 > 100:
        P4 = 100
    if P5 > 100:
        P5 = 100
    if P6 > 100:
        P6 = 100
    if P7 > 100:
        P7 = 100
    if P8 > 100:
        P8 = 100
    if P9 > 100:
        P9 = 100
    if P10 > 100:
        P10 = 100

    # Writes output to the report
    f.write(u'<div id="a' + str(i) + 's">\n')
    f.write(u"<ul>\n")
    f.write(u"<li>volný schůdný bez porostu: " + str(P1) + u" %</li>\n")
    f.write(u"<li>volný schůdný s porostem: " + str(P2) + u" %</li>\n")
    f.write(u"<li>volný obtížně schůdný: " + str(P3) + u" %</li>\n")
    f.write(u"<li>porost lehce průchozí: " + str(P4) + u" %</li>\n")
    f.write(u"<li>porost obtížně průchozí: " + str(P5) + u" %</li>\n")
    f.write(u"<li>zastavěné území měst a obcí: " + str(P6) + u" %</li>\n")
    f.write(u"<li>městské parky a hřiště s pohybem osob: " + str(P7) + u" %</li>\n")
    f.write(u"<li>městské parky a hřiště bez osob: " + str(P8) + u" %</li>\n")
    f.write(u"<li>vodní plocha: " + str(P9) + u" %</li>\n")
    f.write(u"<li>ostatní plochy: " + str(P10) + u" %</li>\n")
    f.write(u"</ul>\n")
    f.write(u"</div>\n")

    f.close()

try:
    # Removes mask to be ready for another calculations for whole area
    print(gscript.read_command('r.mask', flags="r"))
except:
    print("MASK NOT USED")

# Sets area to ha
SUM_P1 = SUM_P1 / float(10000)
SUM_P2 = SUM_P2 / float(10000)
SUM_P3 = SUM_P3 / float(10000)
SUM_P4 = SUM_P4 / float(10000)
SUM_P5 = SUM_P5 / float(10000)
SUM_P6 = SUM_P6 / float(10000)
SUM_P7 = SUM_P7 / float(10000)
SUM_P8 = SUM_P8 / float(10000)
SUM_P9 = SUM_P9 / float(10000)
SUM_P10 = SUM_P10 / float(10000)

f = io.open(DATAPATH + '/pracovni/report.html.units', encoding='utf-8', mode='w')
# Reads numbers for existing search units from units.txt
CUR_KPT = 0
CUR_PT = 0
CUR_VPT = 0
with open(PLUGIN_PATH + "/grass/units.txt", mode="r") as fileInput:
    i = 0
    for row in csv.reader(fileInput, delimiter=';'):
        # unicode_row = [x.decode('utf8') for x in row]
        unicode_row = row
        cur_count = int(unicode_row[0])
        if i == 0:  # Pes
            CUR_KPT = cur_count
        if i == 1:  # Rpjnice
            CUR_PT = cur_count
        if i == 5:  # Potápěč
            CUR_VPT = cur_count
        i = i + 1

f.write(u'<div id="areas" class="fixed400">\n')
f.write(u"\n<h2>Typy povrchů</h2>\n");
f.write(u"<ul>\n")
f.write(u"<li>volný schůdný bez porostu: " + str(int(math.ceil(SUM_P1))) + u" ha</li>\n")
f.write(u"<li>volný schůdný s porostem: " + str(int(math.ceil(SUM_P2))) + u" ha</li>\n")
f.write(u"<li>volný obtížně schůdný: " + str(int(math.ceil(SUM_P3))) + u" ha</li>\n")
f.write(u"<li>porost lehce průchozí: " + str(int(math.ceil(SUM_P4))) + u" ha</li>\n")
f.write(u"<li>porost obtížně průchozí: " + str(int(math.ceil(SUM_P5))) + u" ha</li>\n")
f.write(u"<li>zastavěné území měst a obcí: " + str(int(math.ceil(SUM_P6))) + u" ha</li>\n")
f.write(u"<li>městské parky a hřiště s pohybem osob: " + str(int(math.ceil(SUM_P7))) + u" ha</li>\n")
f.write(u"<li>městské parky a hřiště bez osob: " + str(int(math.ceil(SUM_P8))) + u" ha</li>\n")
f.write(u"<li>vodní plocha: " + str(int(math.ceil(SUM_P9))) + u" ha</li>\n")
f.write(u"<li>ostatní plochy: " + str(int(math.ceil(SUM_P10))) + u" ha</li>\n")
f.write(u"</ul>\n")
f.write(u"</div>\n")

KPT = SUM_P2 + SUM_P3 + SUM_P5
KPT_PT = SUM_P1 + SUM_P4 + SUM_P8
f.write(u'<div id="teams" class="fixed400">\n')
f.write(u"<h2>KPT</h2>\n")
f.write(u"<p>Plocha pro pátrání vhodná pro KPT je " + str(int(math.ceil(KPT + KPT_PT))) + u" ha.\n")
f.write(u"<p>K dispozici je " + str(CUR_KPT) + u" KPT.\n")
P2_P3_P5_KPT = float(SUM_P2) / float(7) + float(SUM_P3) / float(4) + float(SUM_P5) / float(4)
P1_P4_P8_KPT = float(SUM_P1) / float(10) + float(SUM_P4) / float(7) + float(SUM_P8) / float(5)
if CUR_KPT > 0:
    f.write(u"<p>Oblast propátrají přibližně za " + str(
        int(math.ceil((P2_P3_P5_KPT + P1_P4_P8_KPT) / float(CUR_KPT)))) + u" h.\n")
if KPT_PT > 0:
    P1_P4_P8_PT = float(SUM_P1) / (float(7) / float(20)) + float(SUM_P4) / (float(7) / float(20)) + float(SUM_P8) / (
                float(5) / float(20))
    f.write(
        u"<p>Součástí je prostor, kde je možno KPT nahradit PT. Jedná se o " + str(int(math.ceil(KPT_PT))) + u" ha.\n")
if (SUM_P2 + SUM_P1) > 0:
    f.write(u"<p>Součástí je prostor vhodný pro APT (vrtulník, dron) o rozloze " + str(
        int(math.ceil(SUM_P2 + SUM_P1))) + u" ha.\n")

PT = SUM_P6 + SUM_P7 + SUM_P10
f.write(u"<h2>PT</h2>\n")
f.write(u"<p>Plocha pro pátrání vhodná pro PT je " + str(round(PT)) + u" ha.\n")
f.write(u"<p>K dispozici je " + str(CUR_PT) + u" osob pro PT.\n")
if CUR_PT > 0:
    P6_P7_P10_PT = float(SUM_P6) / (float(1) / float(20)) + float(SUM_P7) / (float(5) / float(20)) + float(SUM_P10) / (
                float(5) / float(20))
    f.write(u"<p>Oblast propátrají přibližně za " + str(int(math.ceil(P6_P7_P10_PT / float(CUR_PT)))) + u" h.\n")
else:
    f.write(u"<p>Nejsou k dispozici žádné PT. Je nutné nějaké zajistit.\n")

if SUM_P9 > 0:
    f.write(u"<h2>VPT</h2>\n")
    f.write(u"<p>Vodní plochy v oblasti mají " + str(int(math.ceil(SUM_P9))) + u" ha.\n")
    if CUR_VPT > 0:
        # TODO count time for divers
        A = 100  # placeholder
    else:
        f.write(u"<p>Nejsou k dispozici žádné VPT. Je nutné nějaké zajistit.\n")

f.write(u"</div>\n")

maxtime = 3
if os.path.isfile(PLUGIN_PATH + "/grass/maxtime.txt"):
    try:
        maxtime = int(open(PLUGIN_PATH + "/grass/maxtime.txt", 'r').read())
    except ValueError:
        maxtime = 3

if maxtime <= 0:
    maxtime = 3

f.write(u'<div id="time" class="fixed400">\n')
f.write(u"<h2>Propátrání do stanoveného času</h2>\n")
f.write(u"\n<p>K propátrání do " + str(int(maxtime)) + u" hodin potřebujete:</p>\n")
f.write(u"\n<ul>\n")
f.write(u"\n<li>" + str(int(math.ceil((P2_P3_P5_KPT + P1_P4_P8_KPT) / float(maxtime)))) + u" KPT</li>\n")
f.write(u"\n<li>" + str(int(math.ceil((P6_P7_P10_PT) / float(maxtime)))) + u" PT</li>\n")
if SUM_P9 > 0:
    f.write(u"\n<li>Minimálně jeden VPT</li>\n")
if (SUM_P2 + SUM_P1) > 0:
    f.write(u"\n<li>Minimálně jeden APT</li>\n")
f.write(u"\n</ul>\n")
f.write(u"</div>\n")

f.close()

time.sleep(10)
