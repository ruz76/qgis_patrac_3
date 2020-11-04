#!/usr/bin/env bash
if [[ "$#" -eq 0 ]]; then
  echo "You have to specify new version id"
  echo "pack.sh 16"
  exit 1
fi

RELEASE_PATH=/home/jencek/Documents/Projekty/PCR/qgis/verze3/release
PLUGIN_PATH=/home/jencek/qgis3_profiles/profiles/default/python/plugins/qgis_patrac
PREFIX="3.12"
ID=$1
PREVID=$((ID-1))

echo $PREFIX"."$ID
echo $PREFIX"."$PREVID

COUNT=`cat $PLUGIN_PATH/metadata.txt | grep -c $PREFIX"."$ID`
if [[ "$COUNT" -eq 0 ]]; then
  echo "The version specified is not in metadata.txt"
  exit 1
fi

COUNT=`cat $PLUGIN_PATH/RELEASE | grep -c $PREFIX"."$ID`
if [[ "$COUNT" -eq 0 ]]; then
  echo "The version specified is not in RELEASE"
  exit 1
fi

cd $RELEASE_PATH
rm qgis_patrac.$PREFIX"."$ID.zip
cp qgis_patrac.$PREFIX"."$PREVID.zip qgis_patrac.$PREFIX"."$ID.zip
unzip qgis_patrac.$PREFIX"."$ID.zip

cp $PLUGIN_PATH/config/config.json qgis_patrac/config/
cp $PLUGIN_PATH/config/paths.txt qgis_patrac/config/
cp $PLUGIN_PATH/config/systemid.txt qgis_patrac/config/

cp $PLUGIN_PATH/connect/*.py qgis_patrac/connect/

cp -r $PLUGIN_PATH/doc qgis_patrac/

cp $PLUGIN_PATH/grass/* qgis_patrac/grass/

cp $PLUGIN_PATH/i18n/* qgis_patrac/i18n/

cp $PLUGIN_PATH/icons/* qgis_patrac/icons/

cp $PLUGIN_PATH/main/*.py qgis_patrac/main/

cp $PLUGIN_PATH/styles/* qgis_patrac/styles/

cp $PLUGIN_PATH/main/*.py qgis_patrac/main/

cp $PLUGIN_PATH/ui/*.py qgis_patrac/ui/
cp $PLUGIN_PATH/ui/*.ui qgis_patrac/ui/
cp $PLUGIN_PATH/ui/*.csv qgis_patrac/ui/
cp $PLUGIN_PATH/ui/*.png qgis_patrac/ui/
cp $PLUGIN_PATH/ui/*.svg qgis_patrac/ui/

cp $PLUGIN_PATH/*.py qgis_patrac/
cp $PLUGIN_PATH/*.md qgis_patrac/
cp $PLUGIN_PATH/metadata.txt qgis_patrac/
cp $PLUGIN_PATH/RELEASE qgis_patrac/
cp $PLUGIN_PATH/settings.db qgis_patrac/
cp $PLUGIN_PATH/templates/projekt/clean_v3.qgs qgis_patrac/templates/projekt/

rm qgis_patrac.$PREFIX"."$ID.zip
zip -r qgis_patrac.$PREFIX"."$ID.zip qgis_patrac
rm -r qgis_patrac

sed -i "s/$PREFIX.$PREVID/$PREFIX.$ID/g" plugins.xml
sed -i "s/$PREFIX.$PREVID/$PREFIX.$ID/g" plugins-dev.xml
sed -i "s/$PREFIX.$PREVID/$PREFIX.$ID/g" ../sarops.info/plugins.xml
