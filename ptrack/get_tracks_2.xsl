<?xml version="1.0"?>

<xsl:stylesheet version="1.0"
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:ns1="http://www.opengis.net/kml/2.2"
xmlns:ns4="http://www.google.com/kml/ext/2.2"
>

<xsl:output method="text"/>
<xsl:template match="/">
  
      <xsl:for-each select="//ns4:Track">
				<xsl:text>--ID--</xsl:text>
				<xsl:value-of select="../../../../ns1:name"/>
				<xsl:text>&#xa;</xsl:text>

				<xsl:for-each select="ns1:when">
					<xsl:value-of select="."/>
					<xsl:text>&#xa;</xsl:text>
				</xsl:for-each>

				<xsl:for-each select="ns4:coord">
					<xsl:value-of select="."/>
					<xsl:text>&#xa;</xsl:text>
				</xsl:for-each>

      </xsl:for-each>
  
</xsl:template>

</xsl:stylesheet>
