##This script extracts the number of timesteps at each GCM cell when conditions surpass the triple point of water
##Input obliquity to choose which simulation to use
##Jay Dickson - Brown U./USC - March 2014
##jdickson@brown.edu

import os
import arcpy
from arcpy import env
from arcpy.sa import *

arcpy.CheckOutExtension("Spatial")

##Set local variables
obliquity = 35
workspace = "C:/Users/jdickson/Documents/Projects/Mars/GCM-Geodatabase-Integration/"
JobName = "AllGullies" + str(obliquity)
fc = workspace + "GlobalGullyDatabase.gdb/PixelsWithGullies"
TempLayer = workspace + "temp_temp.shp"
PressLayer = workspace + "press_temp.shp"
prj = "C:/Users/Public/Documents/Mars_GIS/MarsEC0.prj"
cursor = arcpy.SearchCursor(fc)

##Create folder to store tempeorary data
arcpy.CreateFolder_management(workspace, JobName)

##Extract all temperature and pressure values from all points; iterate through bands in GCM simulation
count = 1

print "Extracting Temperature and Pressure values..."

while (count < 5353):

    print "Extracting: " + str(count)

    ##Extract values    
    arcpy.gp.ExtractValuesToPoints_sa(fc,workspace + "GCMs/" + str(obliquity) + "deg-tSurf_MarsEC.tif/Band_" + str(count),TempLayer)
    arcpy.gp.ExtractValuesToPoints_sa(fc,workspace + "GCMs/" + str(obliquity) + "deg-pSurf_MarsEC.tif/Band_" + str(count),PressLayer)

    ##Add field to temporary temperature feature class, set values to extracted temperature values   
    arcpy.AddField_management(TempLayer, "TempK", "DOUBLE")
    arcpy.CalculateField_management(TempLayer, "TempK", "!RASTERVALU!", "PYTHON_9.3")
    arcpy.DeleteField_management(TempLayer, "RASTERVALU")

    ##Add field to temporary pressure feature class, set values to extracted pressure values
    arcpy.AddField_management(PressLayer, "Pressure", "DOUBLE")
    arcpy.CalculateField_management(PressLayer, "Pressure", "!RASTERVALU!", "PYTHON_9.3")
    arcpy.DeleteField_management(PressLayer, "RASTERVALU")

    ##Join temperature & pressure features by OBJECTID
    arcpy.JoinField_management(TempLayer, "OBJECTID", PressLayer, “OBJECTID”,”Pressure”)

    ##Make joined feature class permanent; delete temporary feature classes
    arcpy.CopyFeatures_management(TempLayer,workspace + "/" + JobName + "/" + JobName + "_" + str(count) + ".shp")
    count = count + 1

arcpy.Delete_management(TempLayer)
arcpy.Delete_management(PressLayer)

##Set more local variables
arcpy.env.workspace = workspace + JobName + "/"
featureclasses = arcpy.ListFeatureClasses()

##Set count to last functional value from above; needed for importing spatial reference of subsequent feature class
count = count - 1

##Create feature class that will compile features that surpass triple point; set conditional statement
arcpy.CreateFeatureclass_management(workspace + JobName, JobName + "_all.shp", "POINT", workspace + "/" + JobName + "/" + JobName + "_" + str(count) + ".shp", "DISABLED", "DISABLED", prj)
whereClause = "TempK > 273.16 and Pressure > 611.73"

##Iterate through all feature classes and extract all locations that surpass triple point; append those to new feature class
count = 1

print "Extracting water locations..."
for feature in featureclasses:
    print "Extracting: " + str(count)
    arcpy.MakeFeatureLayer_management(feature, "temp_lyr" + str(count), whereClause)
    arcpy.Append_management("temp_lyr" + str(count), workspace + JobName + "/" + JobName + "_all.shp")
    count = count + 1
    
##Create final feature class that includes the OBJECTID and N (total instances for each feature)
arcpy.CreateFeatureclass_management(workspace + JobName, JobName + "_count.shp", "POINT", "#", "DISABLED", "DISABLED", prj)
arcpy.AddField_management(JobName + "_count.shp","OBJECTID","TEXT")
arcpy.AddField_management(JobName + "_count.shp","N","TEXT")

##Count instances for each separate feature by OBJECTID; insert new row with OBJECTID and N
print "Counting instances at each point..."
count = 1

while count < 446:
    print "Counting: " + str(count)
    arcpy.MakeFeatureLayer_management(workspace + "/" + JobName + "/" + JobName + "_all.shp", "temp" + str(count), "\"OBJECTID\"=" + str(count))
    n = arcpy.GetCount_management("temp" + str(count))
    arcpy.Delete_management("temp" + str(count))
    cursor = arcpy.da.InsertCursor(JobName + "_count.shp",("OBJECTID","N"))
    cursor.insertRow((str(count), str(n)))                                  
    count = count + 1

##Prepare final feature class with properly assigned fields
finalshape = workspace + "GlobalGullyDatabase.gdb/" + JobName

##Join count data with original point using "ET_ID" and "FID" (subsequent iterations of OBJECTID)           
arcpy.CopyFeatures_management(fc, finalshape)
arcpy.JoinField_management(finalshape,"ET_ID",workspace + JobName + "/" + JobName + "_count.shp","FID","N")
arcpy.Delete_management(workspace + "/" + JobName + "/" + JobName + "_all.shp")
arcpy.Delete_management(workspace + "/" + JobName + "/" + JobName + "_count.shp")

##Convert field "N" from TEXT to SHORT
arcpy.AddField_management(finalshape, "MeltNumber", "SHORT")
arcpy.CalculateField_management(finalshape, "MeltNumber", "!N!", "PYTHON_9.3")
arcpy.DeleteField_management(finalshape, "N")

print "Process Completed"
