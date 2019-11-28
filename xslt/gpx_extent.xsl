<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="2.0"
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:gpx="http://www.topografix.com/GPX/1/1"
xmlns:gpxx="http://www.garmin.com/xmlschemas/GpxExtensions/v3"
xmlns:gpxtpx="http://www.garmin.com/xmlschemas/TrackPointExtension/v1"
>
<xsl:output method="text"/>
<xsl:param name="filename"/>
<xsl:template match="/">
		<xsl:value-of select="//gpx:trkpt[1]/gpx:time"/>
		<xsl:text>;</xsl:text>
		<xsl:value-of select="//gpx:trkpt[last()]/gpx:time"/>
		<xsl:text>&#xa;</xsl:text>
</xsl:template>
</xsl:stylesheet>
