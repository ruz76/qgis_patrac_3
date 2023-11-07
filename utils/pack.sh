#!/usr/bin/env bash
if [[ "$#" -eq 0 ]]; then
  echo "You have to specify new version id"
  echo "pack.sh 16"
  exit 1
fi

RELEASE_PATH=/home/jencek/Documents/Projekty/PCR/qgis/verze3/release
PLUGIN_PATH=/home/jencek/qgis3_profiles/profiles/default/python/plugins/qgis_patrac
PREFIX="3.26"
ID=$1

echo $PREFIX"."$ID

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

mkdir qgis_patrac
cd qgis_patrac
mkdir config
mkdir connect
mkdir doc
mkdir grass
mkdir i18n
mkdir icons
mkdir main
mkdir styles
mkdir templates
mkdir ui

echo "placeholder" > config/.placeholder

cp $PLUGIN_PATH/connect/*.py connect/

cp -r $PLUGIN_PATH/doc/* doc/

cp $PLUGIN_PATH/grass/* grass/

cp $PLUGIN_PATH/i18n/* i18n/

cp $PLUGIN_PATH/icons/* icons/

cp $PLUGIN_PATH/main/*.py main/

cp $PLUGIN_PATH/styles/* styles/

cp $PLUGIN_PATH/main/*.py main/

cp $PLUGIN_PATH/ui/*.py ui/
cp $PLUGIN_PATH/ui/*.ui ui/
cp $PLUGIN_PATH/ui/*.csv ui/
cp $PLUGIN_PATH/ui/*.png ui/
cp $PLUGIN_PATH/ui/*.svg ui/

cp $PLUGIN_PATH/*.py ./
cp $PLUGIN_PATH/*.md ./
cp $PLUGIN_PATH/metadata.txt ./
cp $PLUGIN_PATH/RELEASE ./
cp $PLUGIN_PATH/settings.db ./

cp -r $PLUGIN_PATH/templates/* templates/

cd ..

rm qgis_patrac.$PREFIX"."$ID.zip
zip -r qgis_patrac.$PREFIX"."$ID.zip qgis_patrac
rm -r qgis_patrac

#sed -i "s/$PREFIX.$PREVID/$PREFIX.$ID/g" plugins.xml
#sed -i "s/$PREFIX.$PREVID/$PREFIX.$ID/g" plugins-dev.xml
#sed -i "s/$PREFIX.$PREVID/$PREFIX.$ID/g" ../sarops.info/plugins.xml
