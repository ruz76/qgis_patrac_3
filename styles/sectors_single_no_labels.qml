<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis version="2.18.17" simplifyAlgorithm="0" minimumScale="0" maximumScale="1e+08" simplifyDrawingHints="1" minLabelScale="0" maxLabelScale="1e+08" simplifyDrawingTol="1" readOnly="0" simplifyMaxScale="1" hasScaleBasedVisibilityFlag="0" simplifyLocal="1" scaleBasedLabelVisibilityFlag="0">
  <edittypes>
    <edittype widgetv2type="TextEdit" name="cat">
      <widgetv2config IsMultiline="0" fieldEditable="1" constraint="" UseHtml="0" labelOnTop="0" constraintDescription="" notNull="0"/>
    </edittype>
    <edittype widgetv2type="TextEdit" name="id">
      <widgetv2config IsMultiline="0" fieldEditable="1" constraint="" UseHtml="0" labelOnTop="0" constraintDescription="" notNull="0"/>
    </edittype>
    <edittype widgetv2type="TextEdit" name="typ">
      <widgetv2config IsMultiline="0" fieldEditable="1" constraint="" UseHtml="0" labelOnTop="0" constraintDescription="" notNull="0"/>
    </edittype>
    <edittype widgetv2type="TextEdit" name="area_ha">
      <widgetv2config IsMultiline="0" fieldEditable="1" constraint="" UseHtml="0" labelOnTop="0" constraintDescription="" notNull="0"/>
    </edittype>
    <edittype widgetv2type="TextEdit" name="label">
      <widgetv2config IsMultiline="0" fieldEditable="1" constraint="" UseHtml="0" labelOnTop="0" constraintDescription="" notNull="0"/>
    </edittype>
  </edittypes>
  <renderer-v2 forceraster="0" symbollevels="0" type="singleSymbol" enableorderby="0">
    <symbols>
      <symbol alpha="1" clip_to_extent="1" type="fill" name="0">
        <layer pass="0" class="SimpleFill" locked="0">
          <prop k="border_width_map_unit_scale" v="0,0,0,0,0,0"/>
          <prop k="color" v="183,140,0,0"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="0,0,0,255"/>
          <prop k="outline_style" v="solid"/>
          <prop k="outline_width" v="0.26"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="style" v="solid"/>
        </layer>
      </symbol>
    </symbols>
    <rotation/>
    <sizescale scalemethod="diameter"/>
  </renderer-v2>
  <labeling type="simple"/>
  <customproperties>
    <property key="embeddedWidgets/count" value="0"/>
    <property key="labeling" value="pal"/>
    <property key="labeling/addDirectionSymbol" value="false"/>
    <property key="labeling/angleOffset" value="0"/>
    <property key="labeling/blendMode" value="0"/>
    <property key="labeling/bufferBlendMode" value="0"/>
    <property key="labeling/bufferColorA" value="255"/>
    <property key="labeling/bufferColorB" value="255"/>
    <property key="labeling/bufferColorG" value="255"/>
    <property key="labeling/bufferColorR" value="255"/>
    <property key="labeling/bufferDraw" value="false"/>
    <property key="labeling/bufferJoinStyle" value="64"/>
    <property key="labeling/bufferNoFill" value="false"/>
    <property key="labeling/bufferSize" value="1"/>
    <property key="labeling/bufferSizeInMapUnits" value="false"/>
    <property key="labeling/bufferSizeMapUnitScale" value="0,0,0,0,0,0"/>
    <property key="labeling/bufferTransp" value="0"/>
    <property key="labeling/centroidInside" value="false"/>
    <property key="labeling/centroidWhole" value="false"/>
    <property key="labeling/decimals" value="3"/>
    <property key="labeling/displayAll" value="false"/>
    <property key="labeling/dist" value="0"/>
    <property key="labeling/distInMapUnits" value="false"/>
    <property key="labeling/distMapUnitScale" value="0,0,0,0,0,0"/>
    <property key="labeling/drawLabels" value="false"/>
    <property key="labeling/enabled" value="false"/>
    <property key="labeling/fieldName" value=" concat(  &quot;label&quot; , ' (',  &quot;area_ha&quot; , ' ha)') "/>
    <property key="labeling/fitInPolygonOnly" value="false"/>
    <property key="labeling/fontCapitals" value="0"/>
    <property key="labeling/fontFamily" value="Ubuntu"/>
    <property key="labeling/fontItalic" value="true"/>
    <property key="labeling/fontLetterSpacing" value="0"/>
    <property key="labeling/fontLimitPixelSize" value="false"/>
    <property key="labeling/fontMaxPixelSize" value="10000"/>
    <property key="labeling/fontMinPixelSize" value="3"/>
    <property key="labeling/fontSize" value="11"/>
    <property key="labeling/fontSizeInMapUnits" value="false"/>
    <property key="labeling/fontSizeMapUnitScale" value="0,0,0,0,0,0"/>
    <property key="labeling/fontStrikeout" value="false"/>
    <property key="labeling/fontUnderline" value="false"/>
    <property key="labeling/fontWeight" value="63"/>
    <property key="labeling/fontWordSpacing" value="0"/>
    <property key="labeling/formatNumbers" value="false"/>
    <property key="labeling/isExpression" value="true"/>
    <property key="labeling/labelOffsetInMapUnits" value="true"/>
    <property key="labeling/labelOffsetMapUnitScale" value="0,0,0,0,0,0"/>
    <property key="labeling/labelPerPart" value="false"/>
    <property key="labeling/leftDirectionSymbol" value="&lt;"/>
    <property key="labeling/limitNumLabels" value="false"/>
    <property key="labeling/maxCurvedCharAngleIn" value="20"/>
    <property key="labeling/maxCurvedCharAngleOut" value="-20"/>
    <property key="labeling/maxNumLabels" value="2000"/>
    <property key="labeling/mergeLines" value="false"/>
    <property key="labeling/minFeatureSize" value="0"/>
    <property key="labeling/multilineAlign" value="0"/>
    <property key="labeling/multilineHeight" value="1"/>
    <property key="labeling/namedStyle" value="Italic"/>
    <property key="labeling/obstacle" value="true"/>
    <property key="labeling/obstacleFactor" value="1"/>
    <property key="labeling/obstacleType" value="0"/>
    <property key="labeling/offsetType" value="0"/>
    <property key="labeling/placeDirectionSymbol" value="0"/>
    <property key="labeling/placement" value="1"/>
    <property key="labeling/placementFlags" value="10"/>
    <property key="labeling/plussign" value="false"/>
    <property key="labeling/predefinedPositionOrder" value="TR,TL,BR,BL,R,L,TSR,BSR"/>
    <property key="labeling/preserveRotation" value="true"/>
    <property key="labeling/previewBkgrdColor" value="#ffffff"/>
    <property key="labeling/priority" value="5"/>
    <property key="labeling/quadOffset" value="4"/>
    <property key="labeling/repeatDistance" value="0"/>
    <property key="labeling/repeatDistanceMapUnitScale" value="0,0,0,0,0,0"/>
    <property key="labeling/repeatDistanceUnit" value="1"/>
    <property key="labeling/reverseDirectionSymbol" value="false"/>
    <property key="labeling/rightDirectionSymbol" value=">"/>
    <property key="labeling/scaleMax" value="10000000"/>
    <property key="labeling/scaleMin" value="1"/>
    <property key="labeling/scaleVisibility" value="false"/>
    <property key="labeling/shadowBlendMode" value="6"/>
    <property key="labeling/shadowColorB" value="0"/>
    <property key="labeling/shadowColorG" value="0"/>
    <property key="labeling/shadowColorR" value="0"/>
    <property key="labeling/shadowDraw" value="false"/>
    <property key="labeling/shadowOffsetAngle" value="135"/>
    <property key="labeling/shadowOffsetDist" value="1"/>
    <property key="labeling/shadowOffsetGlobal" value="true"/>
    <property key="labeling/shadowOffsetMapUnitScale" value="0,0,0,0,0,0"/>
    <property key="labeling/shadowOffsetUnits" value="1"/>
    <property key="labeling/shadowRadius" value="1.5"/>
    <property key="labeling/shadowRadiusAlphaOnly" value="false"/>
    <property key="labeling/shadowRadiusMapUnitScale" value="0,0,0,0,0,0"/>
    <property key="labeling/shadowRadiusUnits" value="1"/>
    <property key="labeling/shadowScale" value="100"/>
    <property key="labeling/shadowTransparency" value="30"/>
    <property key="labeling/shadowUnder" value="0"/>
    <property key="labeling/shapeBlendMode" value="0"/>
    <property key="labeling/shapeBorderColorA" value="255"/>
    <property key="labeling/shapeBorderColorB" value="128"/>
    <property key="labeling/shapeBorderColorG" value="128"/>
    <property key="labeling/shapeBorderColorR" value="128"/>
    <property key="labeling/shapeBorderWidth" value="0"/>
    <property key="labeling/shapeBorderWidthMapUnitScale" value="0,0,0,0,0,0"/>
    <property key="labeling/shapeBorderWidthUnits" value="1"/>
    <property key="labeling/shapeDraw" value="false"/>
    <property key="labeling/shapeFillColorA" value="255"/>
    <property key="labeling/shapeFillColorB" value="255"/>
    <property key="labeling/shapeFillColorG" value="255"/>
    <property key="labeling/shapeFillColorR" value="255"/>
    <property key="labeling/shapeJoinStyle" value="64"/>
    <property key="labeling/shapeOffsetMapUnitScale" value="0,0,0,0,0,0"/>
    <property key="labeling/shapeOffsetUnits" value="1"/>
    <property key="labeling/shapeOffsetX" value="0"/>
    <property key="labeling/shapeOffsetY" value="0"/>
    <property key="labeling/shapeRadiiMapUnitScale" value="0,0,0,0,0,0"/>
    <property key="labeling/shapeRadiiUnits" value="1"/>
    <property key="labeling/shapeRadiiX" value="0"/>
    <property key="labeling/shapeRadiiY" value="0"/>
    <property key="labeling/shapeRotation" value="0"/>
    <property key="labeling/shapeRotationType" value="0"/>
    <property key="labeling/shapeSVGFile" value=""/>
    <property key="labeling/shapeSizeMapUnitScale" value="0,0,0,0,0,0"/>
    <property key="labeling/shapeSizeType" value="0"/>
    <property key="labeling/shapeSizeUnits" value="1"/>
    <property key="labeling/shapeSizeX" value="0"/>
    <property key="labeling/shapeSizeY" value="0"/>
    <property key="labeling/shapeTransparency" value="0"/>
    <property key="labeling/shapeType" value="0"/>
    <property key="labeling/substitutions" value="&lt;substitutions/>"/>
    <property key="labeling/textColorA" value="255"/>
    <property key="labeling/textColorB" value="0"/>
    <property key="labeling/textColorG" value="0"/>
    <property key="labeling/textColorR" value="0"/>
    <property key="labeling/textTransp" value="0"/>
    <property key="labeling/upsidedownLabels" value="0"/>
    <property key="labeling/useSubstitutions" value="false"/>
    <property key="labeling/wrapChar" value=""/>
    <property key="labeling/xOffset" value="0"/>
    <property key="labeling/yOffset" value="0"/>
    <property key="labeling/zIndex" value="0"/>
    <property key="variableNames"/>
    <property key="variableValues"/>
  </customproperties>
  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <layerTransparency>0</layerTransparency>
  <displayfield>cat</displayfield>
  <label>0</label>
  <labelattributes>
    <label fieldname="" text="Label"/>
    <family fieldname="" name="Ubuntu"/>
    <size fieldname="" units="pt" value="12"/>
    <bold fieldname="" on="0"/>
    <italic fieldname="" on="0"/>
    <underline fieldname="" on="0"/>
    <strikeout fieldname="" on="0"/>
    <color fieldname="" red="0" blue="0" green="0"/>
    <x fieldname=""/>
    <y fieldname=""/>
    <offset x="0" y="0" units="pt" yfieldname="" xfieldname=""/>
    <angle fieldname="" value="0" auto="0"/>
    <alignment fieldname="" value="center"/>
    <buffercolor fieldname="" red="255" blue="255" green="255"/>
    <buffersize fieldname="" units="pt" value="1"/>
    <bufferenabled fieldname="" on=""/>
    <multilineenabled fieldname="" on=""/>
    <selectedonly on=""/>
  </labelattributes>
  <SingleCategoryDiagramRenderer diagramType="Pie" sizeLegend="0" attributeLegend="1">
    <DiagramCategory penColor="#000000" labelPlacementMethod="XHeight" penWidth="0" diagramOrientation="Up" sizeScale="0,0,0,0,0,0" minimumSize="0" barWidth="5" penAlpha="255" maxScaleDenominator="1e+08" backgroundColor="#ffffff" transparency="0" width="15" scaleDependency="Area" backgroundAlpha="255" angleOffset="1440" scaleBasedVisibility="0" enabled="0" height="15" lineSizeScale="0,0,0,0,0,0" sizeType="MM" lineSizeType="MM" minScaleDenominator="inf">
      <fontProperties description="Ubuntu,11,-1,5,50,0,0,0,0,0" style=""/>
      <attribute field="" color="#000000" label=""/>
    </DiagramCategory>
    <symbol alpha="1" clip_to_extent="1" type="marker" name="sizeSymbol">
      <layer pass="0" class="SimpleMarker" locked="0">
        <prop k="angle" v="0"/>
        <prop k="color" v="255,0,0,255"/>
        <prop k="horizontal_anchor_point" v="1"/>
        <prop k="joinstyle" v="bevel"/>
        <prop k="name" v="circle"/>
        <prop k="offset" v="0,0"/>
        <prop k="offset_map_unit_scale" v="0,0,0,0,0,0"/>
        <prop k="offset_unit" v="MM"/>
        <prop k="outline_color" v="0,0,0,255"/>
        <prop k="outline_style" v="solid"/>
        <prop k="outline_width" v="0"/>
        <prop k="outline_width_map_unit_scale" v="0,0,0,0,0,0"/>
        <prop k="outline_width_unit" v="MM"/>
        <prop k="scale_method" v="diameter"/>
        <prop k="size" v="2"/>
        <prop k="size_map_unit_scale" v="0,0,0,0,0,0"/>
        <prop k="size_unit" v="MM"/>
        <prop k="vertical_anchor_point" v="1"/>
      </layer>
    </symbol>
  </SingleCategoryDiagramRenderer>
  <DiagramLayerSettings yPosColumn="-1" showColumn="0" linePlacementFlags="10" placement="0" dist="0" xPosColumn="-1" priority="0" obstacle="0" zIndex="0" showAll="1"/>
  <annotationform>.</annotationform>
  <aliases>
    <alias field="cat" index="0" name=""/>
    <alias field="id" index="1" name=""/>
    <alias field="typ" index="2" name=""/>
    <alias field="area_ha" index="3" name=""/>
    <alias field="label" index="4" name=""/>
  </aliases>
  <excludeAttributesWMS/>
  <excludeAttributesWFS/>
  <attributeactions default="-1"/>
  <attributetableconfig actionWidgetStyle="dropDown" sortExpression="" sortOrder="0">
    <columns>
      <column width="-1" hidden="0" type="field" name="label"/>
      <column width="-1" hidden="0" type="field" name="area_ha"/>
      <column width="-1" hidden="1" type="actions"/>
      <column width="-1" hidden="0" type="field" name="cat"/>
      <column width="-1" hidden="0" type="field" name="id"/>
      <column width="-1" hidden="0" type="field" name="typ"/>
    </columns>
  </attributetableconfig>
  <editform>.</editform>
  <editforminit/>
  <editforminitcodesource>0</editforminitcodesource>
  <editforminitfilepath>.</editforminitfilepath>
  <editforminitcode><![CDATA[# -*- coding: utf-8 -*-
"""
QGIS forms can have a Python function that is called when the form is
opened.

Use this function to add extra logic to your forms.

Enter the name of the function in the "Python Init function"
field.
An example follows:
"""
from PyQt4.QtGui import QWidget

def my_form_open(dialog, layer, feature):
	geom = feature.geometry()
	control = dialog.findChild(QWidget, "MyLineEdit")
]]></editforminitcode>
  <featformsuppress>0</featformsuppress>
  <editorlayout>generatedlayout</editorlayout>
  <widgets>
    <widget name="cat_">
      <config/>
    </widget>
  </widgets>
  <conditionalstyles>
    <rowstyles/>
    <fieldstyles/>
  </conditionalstyles>
  <defaults>
    <default field="cat" expression=""/>
    <default field="id" expression=""/>
    <default field="typ" expression=""/>
    <default field="area_ha" expression=""/>
    <default field="label" expression=""/>
  </defaults>
  <previewExpression>COALESCE("cat", '&lt;NULL>')</previewExpression>
    <mapTip>[% "id" %]&lt;/br>
    [% "typ" %]&lt;/br>
    [% CASE WHEN "stav" = 1 THEN 'Pátrání: &lt;span style="background-color:#f6f372">Zahájeno&lt;/span>' END %]
    [% CASE WHEN "stav" = 2 THEN 'Pátrání: &lt;span style="background-color:#AAFFAA">Dokončeno&lt;/span>' END %]
    [% CASE WHEN "stav" = 0 THEN '&lt;span style="background-color:#d36450">Rizikový sektor&lt;/span>' END %]
    [% CASE WHEN "stav" IS NULL THEN 'Pátrání: Nezahájeno' END %]&lt;/br>
    [% CASE WHEN "prostredky" = 0 THEN 'Prostředky: Psovod&lt;/br/>
    &lt;svg version="1.0" xmlns="http://www.w3.org/2000/svg"
     width="20pt" height="20pt" viewBox="0 0 1280.000000 1254.000000"
     preserveAspectRatio="xMidYMid meet">
    &lt;metadata>
    Created by potrace 1.15, written by Peter Selinger 2001-2017
    &lt;/metadata>
    &lt;g transform="translate(0.000000,1254.000000) scale(0.100000,-0.100000)"
    fill="#000000" stroke="none">
    &lt;path d="M4269 12526 c-178 -51 -302 -126 -434 -260 -225 -228 -364 -546 -411
    -941 -34 -290 2 -542 111 -772 53 -113 91 -170 169 -251 141 -147 296 -222
    463 -222 93 0 159 18 263 70 363 182 619 590 686 1090 27 204 9 503 -42 677
    -82 283 -281 510 -521 594 -74 26 -220 34 -284 15z"/>
    &lt;path d="M1880 12492 c-243 -80 -444 -319 -520 -618 -11 -41 -25 -142 -32
    -224 -40 -492 129 -992 441 -1300 124 -123 300 -229 441 -266 202 -53 468 64
    614 270 140 197 206 427 206 721 0 174 -18 312 -60 473 -123 471 -392 802
    -760 932 -90 32 -251 38 -330 12z"/>
    &lt;path d="M5740 10584 c-232 -49 -469 -211 -630 -428 -160 -218 -257 -463 -300
    -758 -24 -167 -25 -233 -5 -358 32 -197 112 -366 230 -485 82 -83 160 -131
    258 -156 222 -59 511 39 740 251 148 136 306 390 377 607 66 199 98 454 80
    629 -16 156 -78 330 -159 448 -28 41 -113 127 -161 164 -114 88 -274 120 -430
    86z"/>
    &lt;path d="M565 10463 c-255 -39 -448 -205 -515 -443 -50 -180 -62 -371 -34
    -559 49 -332 194 -631 414 -852 151 -151 290 -238 480 -301 225 -73 424 -20
    586 155 138 149 191 302 201 582 4 125 2 171 -16 274 -55 323 -194 594 -420
    822 -152 153 -328 268 -464 303 -60 16 -187 26 -232 19z"/>
    &lt;path d="M3152 9180 c-471 -60 -930 -332 -1219 -725 -245 -332 -434 -677 -557
    -1019 -83 -229 -156 -533 -156 -652 0 -270 173 -538 410 -635 91 -37 204 -53
    310 -44 191 15 321 50 665 180 368 139 463 165 683 191 301 36 502 -6 942
    -194 389 -166 477 -192 640 -192 305 0 549 160 623 408 26 90 28 314 3 417
    -63 260 -178 521 -354 805 -395 637 -700 990 -1067 1235 -163 109 -318 175
    -496 210 -92 19 -330 27 -427 15z"/>
    &lt;path d="M10565 6435 c-399 -108 -703 -492 -810 -1023 -93 -461 -20 -863 208
    -1151 158 -199 414 -307 615 -260 75 18 222 93 308 157 233 175 408 451 490
    772 45 176 57 297 51 500 -8 275 -37 412 -124 582 -86 168 -202 292 -342 366
    -130 68 -277 89 -396 57z"/>
    &lt;path d="M8234 6415 c-227 -41 -445 -256 -542 -535 -81 -232 -86 -609 -13
    -897 123 -480 401 -827 776 -968 81 -31 195 -37 285 -16 281 67 491 325 571
    704 26 120 31 384 10 527 -81 562 -365 987 -765 1146 -65 26 -211 58 -244 53
    -4 0 -39 -7 -78 -14z"/>
    &lt;path d="M12115 4509 c-449 -60 -832 -463 -969 -1019 -38 -157 -57 -345 -46
    -463 21 -222 99 -412 225 -545 151 -160 307 -214 515 -178 425 74 799 495 919
    1033 28 125 45 319 37 429 -20 288 -168 558 -371 675 -93 54 -216 81 -310 68z"/>
    &lt;path d="M6810 4364 c-167 -35 -326 -155 -403 -302 -101 -192 -130 -507 -72
    -788 42 -203 152 -448 271 -607 247 -328 640 -529 914 -466 91 21 171 70 260
    159 159 158 220 336 222 640 1 321 -101 628 -300 900 -74 101 -230 253 -326
    317 -213 144 -380 187 -566 147z"/>
    &lt;path d="M9435 3089 c-327 -44 -641 -188 -920 -421 -121 -101 -212 -205 -342
    -391 -304 -433 -484 -819 -600 -1287 -41 -162 -47 -199 -47 -295 0 -88 4 -125
    23 -185 73 -235 227 -400 434 -465 65 -21 98 -25 201 -25 211 0 333 30 745
    185 375 140 454 162 676 186 296 32 498 -12 962 -210 387 -164 475 -188 653
    -177 186 11 321 67 436 181 127 125 171 258 161 480 -15 319 -176 683 -551
    1245 -302 454 -575 749 -882 953 -166 110 -311 173 -487 212 -87 19 -363 28
    -462 14z"/>
    &lt;/g>
    &lt;/svg>' END %]
    [% CASE WHEN "prostredky" = 1 THEN 'Prostředky: Rojnice&lt;br/>&lt;svg
       xmlns:dc="http://purl.org/dc/elements/1.1/"
       xmlns:cc="http://creativecommons.org/ns#"
       xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
       xmlns:svg="http://www.w3.org/2000/svg"
       xmlns="http://www.w3.org/2000/svg"
       id="svg4746"
       version="1.1"
       viewBox="0 0 210 210"
       height="30pt"
       width="30pt">
      &lt;defs
         id="defs4740" />
      &lt;metadata
         id="metadata4743">
        &lt;rdf:RDF>
          &lt;cc:Work
             rdf:about="">
            &lt;dc:format>image/svg+xml&lt;/dc:format>
            &lt;dc:type
               rdf:resource="http://purl.org/dc/dcmitype/StillImage" />
            &lt;dc:title>&lt;/dc:title>
          &lt;/cc:Work>
        &lt;/rdf:RDF>
      &lt;/metadata>
      &lt;g
         id="layer1">
        &lt;rect
           y="24.857143"
           x="30.994047"
           height="10.583333"
           width="89.958336"
           id="rect5291"
           style="fill:#909000;fill-opacity:1;stroke:#000000;stroke-width:0.2;stroke-miterlimit:4;stroke-dasharray:none;stroke-opacity:1" />
        &lt;rect
           y="61.898811"
           x="70.681549"
           height="10.583333"
           width="89.958336"
           id="rect5291-2"
           style="fill:#909000;fill-opacity:1;stroke:#000000;stroke-width:0.2;stroke-miterlimit:4;stroke-dasharray:none;stroke-opacity:1" />
        &lt;rect
           y="61.898811"
           x="70.681549"
           height="10.583333"
           width="89.958336"
           id="rect5291-0"
           style="fill:#909000;fill-opacity:1;stroke:#000000;stroke-width:0.2;stroke-miterlimit:4;stroke-dasharray:none;stroke-opacity:1" />
        &lt;rect
           y="96.672623"
           x="30.616066"
           height="10.583333"
           width="89.958336"
           id="rect5291-0-8"
           style="fill:#909000;fill-opacity:1;stroke:#000000;stroke-width:0.2;stroke-miterlimit:4;stroke-dasharray:none;stroke-opacity:1" />
      &lt;/g>
    &lt;/svg>' END %]
    [% CASE WHEN "prostredky" = 2 THEN 'Prostředky: Dron' END %]
    [% CASE WHEN "prostredky" = 3 THEN 'Prostředky: Jiný' END %]
    [% CASE WHEN "prostredky" IS NULL THEN 'Prostředky: Neuvedeny' END %]&lt;/br>
    Od: [% "od_cas" %]&lt;/br>
    Do: [% "do_cas" %]
    </mapTip>
  <layerGeometryType>2</layerGeometryType>
</qgis>
