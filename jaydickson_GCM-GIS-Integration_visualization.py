##This script generates a map for each timestep in a 5352 band GCM simulation
##Input obliquity to choose which simulation to run; default temp/pressure values are set to the triple point of water
##Jay Dickson - Brown U./USC - March, 2014
##jdickson@brown.edu

import os
import arcpy
from arcpy import env
from arcpy.sa import *

arcpy.CheckOutExtension("Spatial")

##Set local variables
obliquity = 25
workspace = "C:/Users/jdickson/Projects/Mars/GCM-Geodatabase-Integration/" + str(obliquity) + "deg/"
slloc="C:/Users/jdickson/Documents/Projects/Mars/GCM-Geodatabase-Integration/MarsPressureStretch612-1200.lyr"
flloc="C:/Users/jdickson/Documents/Projects/Mars/GCM-Geodatabase-Integration/MarsTempContour273-293.lyr"
mxdPath = "C:/Users/jdickson/Documents/Projects/Mars/GCM-Basemap/GCMBasemap7.mxd"

count = 1

##Generate map for each band within GCM simulation
while (count < 5353):
    ##Set in-loop variables
    count_string = "0000" + str(count)
    count_label = count_string[-5:]
    inRasterPressure = workspace + str(obliquity) + "deg-pSurf_MarsEC.tif/Band_" + str(count)
    inRasterTemp = workspace + str(obliquity) + "deg-tSurf_MarsEC.tif/Band_" + str(count)

    ##Create pressure raster nulled below 6.11 mb (611.73 pascals)
    print "Extracting: Band" + count_label
    arcpy.CopyRaster_management(inRasterPressure, workspace + "Band" + count_label + ".tif","#","#","#","NONE","NONE","#")
    print "Nulling all negative values: Band" + count_label
    arcpy.Resample_management(workspace + "Band" + count_label + ".tif",workspace + "Band" + count_label + "_resample.tif","22227.965994 22227.965994","CUBIC")
    outSetNull = SetNull(workspace + "Band" + count_label + "_resample.tif",workspace + "Band" + count_label + "_resample.tif", "VALUE < 611.73")
    outSetNull.save(workspace + "Band" + count_label + "_nulled.tif")

    ##Create temperature contour map nulled below 273 K
    arcpy.CopyRaster_management(inRasterTemp, workspace + "Temp_Band" + count_label + ".tif","#","#","#","NONE","NONE","#")
    print "Nulling all negative values: Band" + count_label
    arcpy.Resample_management(workspace + "Temp_Band" + count_label + ".tif",workspace + "Temp_Band" + count_label + "_resample.tif","22227.965994 22227.965994","CUBIC")
    arcpy.gp.Con_sa(workspace + "Temp_Band" + count_label + "_resample.tif",workspace + "Temp_Band" + count_label + "_resample.tif",workspace + "Temp_Band" + count_label + "_nulled.tif","#",""""VALUE" > 272""")
    arcpy.gp.Contour_sa(workspace + "Temp_Band" + count_label + "_nulled.tif",workspace + "Temp_Band" + count_label + "_ctr_05.shp","5","273","1")

    ##Delete temporary rasters
    arcpy.Delete_management(workspace + "Band" + count_label + ".tif")
    arcpy.Delete_management(workspace + "Band" + count_label + "_resample.tif")
    arcpy.Delete_management(workspace + "Temp_Band" + count_label + ".tif")
    arcpy.Delete_management(workspace + "Temp_Band" + count_label + "_resample.tif")
    arcpy.Delete_management(workspace + "Temp_Band" + count_label + "_nulled.tif")
    
    ##Set variables for generating map
    rasterPath = workspace + "Band" + count_label + "_nulled.tif"
    featurePath = workspace + "Temp_Band" + count_label + "_ctr_05.shp"
    featureLayerName = "ftemp" + count_label
    rasterLayerName = "temp"
       
    ##Add pressure raster to map, set symbology to slloc, blend at 70% opacity
    md = arcpy.mapping.MapDocument(mxdPath)
    df = arcpy.mapping.ListDataFrames(md)[0]
    result = arcpy.MakeRasterLayer_management(rasterPath, rasterLayerName)
    layer = result.getOutput(0)
    arcpy.mapping.AddLayer(df, layer, 'TOP')

    sl=arcpy.mapping.Layer(slloc)
    nl=arcpy.mapping.ListLayers(md)[0]
    arcpy.mapping.UpdateLayer(df,nl,sl,"True")
    nl.transparency = 70

    ##Add temperature contour to map, set symbology to flloc
    featureresult = arcpy.MakeFeatureLayer_management(featurePath, featureLayerName)
    featurelayer = featureresult.getOutput(0)
    arcpy.mapping.AddLayer(df, featurelayer, 'TOP')

    fl=arcpy.mapping.Layer(flloc)
    al=arcpy.mapping.ListLayers(md)[0]
    arcpy.mapping.UpdateLayer(df,al,fl,"True")

    ##Export map
    arcpy.mapping.ExportToJPEG(md, "Z:/Desktop/" + str(obliquity) + "/Band_" + count_label + ".jpg",resolution = 150)

    ##Delete pressure raster and temperature contour feature class
    arcpy.Delete_management(rasterPath)
    arcpy.Delete_management(featurePath)

    print "Completed Band " + count_label
    count = count + 1

print "Process completed"
