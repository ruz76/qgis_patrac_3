# -*- coding: utf-8 -*-

# ******************************************************************************
#
# Patrac
# ---------------------------------------------------------
# Podpora pátrání po pohřešované osobě
#
# Copyright (C) 2017-2019 Jan Růžička (jan.ruzicka.vsb@gmail.com)
#
# This source is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# This code is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# A copy of the GNU General Public License is available on the World Wide Web
# at <http://www.gnu.org/copyleft/gpl.html>. You can also obtain it by writing
# to the Free Software Foundation, Inc., 59 Temple Place - Suite 330, Boston,
# MA 02111-1307, USA.
#
# The sliders and layer transparency are based on https://github.com/alexbruy/raster-transparency
# ******************************************************************************

import io, os, sys
import lxml.etree as ET

class Transform():
    def __init__(self):
        self.none = None

    def transform_xslt_time(self, pluginpath, xml_filename, output, start, end):
        dom = ET.parse(xml_filename)
        xslt = ET.parse(os.path.join(pluginpath, '/xslt/gpx.xsl'))
        transform = ET.XSLT(xslt)
        newdom = transform(dom, start = ET.XSLT.strparam(start), end = ET.XSLT.strparam(end))
        print((ET.tostring(newdom, pretty_print=True)))