<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis version="2.14.18-Essen" minimumScale="0" maximumScale="1e+08" hasScaleBasedVisibilityFlag="0">
  <pipe>
    <rasterrenderer gradient="BlackToWhite" opacity="1" alphaBand="-1" type="singlebandgray" grayBand="1">
      <rasterTransparency>
        <singleValuePixelList>
          <pixelListEntry min="88" max="100" percentTransparent="100"/>
        </singleValuePixelList>
      </rasterTransparency>
      <contrastEnhancement>
        <minValue>0</minValue>
        <maxValue>100</maxValue>
        <algorithm>StretchToMinimumMaximum</algorithm>
      </contrastEnhancement>
    </rasterrenderer>
    <brightnesscontrast brightness="0" contrast="0"/>
    <huesaturation colorizeGreen="128" colorizeOn="0" colorizeRed="255" colorizeBlue="128" grayscaleMode="0" saturation="0" colorizeStrength="100"/>
    <rasterresampler maxOversampling="2"/>
  </pipe>
  <blendMode>0</blendMode>
</qgis>
