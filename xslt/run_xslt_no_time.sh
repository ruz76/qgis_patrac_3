cd $1/xslt/
java -jar saxon9he.jar $2 gpx_no_time.xsl > $3
echo "GPX: " $2
echo "CSV: " $3
