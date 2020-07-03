from osgeo import ogr

ds = ogr.Open("C:/Current.gpx")
layer = ds.GetLayer(2)
features_nr = layer.GetFeatureCount()
for i in range(features_nr):
    f = layer.GetNextFeature()
    print(f.GetField('name'))

layer = ds.GetLayer(4)
f = layer.GetFeature(0)
print(f.GetField('time'))

f = layer.GetFeature(layer.GetFeatureCount() - 1)
print(f.GetField('time'))

import os, ogr, osr

outputMergefn = 'merge.shp'
directory = "/Users/UserName/Downloads/"
fileStartsWith = 'test'
fileEndsWith = '.shp'
driverName = 'ESRI Shapefile'
geometryType = ogr.wkbPolygon

out_driver = ogr.GetDriverByName( driverName )
if os.path.exists(outputMergefn):
    out_driver.DeleteDataSource(outputMergefn)
out_ds = out_driver.CreateDataSource(outputMergefn)
out_layer = out_ds.CreateLayer(outputMergefn, geom_type=geometryType)

fileList = os.listdir(directory)

for file in fileList:
    if file.startswith(fileStartsWith) and file.endswith(fileEndsWith):
        print file
        ds = ogr.Open(directory+file)
        lyr = ds.GetLayer()
        for feat in lyr:
            out_feat = ogr.Feature(out_layer.GetLayerDefn())
            out_feat.SetGeometry(feat.GetGeometryRef().Clone())
            out_layer.CreateFeature(out_feat)
            out_feat = None
            out_layer.SyncToDisk()