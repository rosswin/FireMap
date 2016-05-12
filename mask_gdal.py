# -*- coding: utf-8 -*-
"""
Created on Fri Apr 29 07:47:48 2016

@author: Ross.Winans
"""
#TODO
#
#

from osgeo import gdal, gdal_array
import numpy as np

import sys
from os import walk 
from os.path import join, basename, exists
#import datetime

def alignMasks(workedOn,bandsList):
    #code adapted from http://sciience.tumblr.com/post/101722591382/finding-the-georeferenced-intersection-between-two
    # load data
    sortList = sorted(workedOn)
    anchorDs = gdal.Open(join(sortList[0], basename(sortList[0])+'_B%s.tif'%bandsList[0]))
    anchorBand = anchorDs.GetRasterBand(1)
    anchorGt = anchorDs.GetGeoTransform()
    anchorProj = anchorDs.GetProjectionRef()
    for rstr in sortList:
        for bnd in bandsList:
            ds = gdal.Open(join(rstr, basename(rstr)+'_B%s_mask.tif'%bnd))
            band = ds.GetRasterBand(1)
            gt = ds.GetGeoTransform()
            proj = ds.GetProjectionRef()
            # r1 has left, top, right, bottom of dataset's bounds in geospatial coordinates.
            anchorR = [anchorGt[0], anchorGt[3], anchorGt[0] + (anchorGt[1] * anchorDs.RasterXSize), anchorGt[3] + (anchorGt[5] * anchorDs.RasterYSize)]
            r = [gt[0], gt[3], gt[0] + (gt[1] * ds.RasterXSize), gt[3] + (gt[5] * ds.RasterYSize)]
            print '\t1 bounding box: %s' % str(anchorR)
            print '\t2 bounding box: %s' % str(r)
            
            # find intersection between bounding boxes
            intersection = [max(anchorR[0], r[0]), min(anchorR[1], r[1]), min(anchorR[2], r[2]), max(anchorR[3], r[3])]
            if anchorR != r:
                print '\t** different bounding boxes **'
                # check for any overlap at all...
                if (intersection[2] < intersection[0]) or (intersection[1] < intersection[3]):
                    intersection = None
                    print '\t***no overlap***'
                    return
                else:
                    print '\tintersection:',intersection
                    left1 = int(round((intersection[0]-anchorR[0])/anchorGt[1])) # difference divided by pixel dimension
                    top1 = int(round((intersection[1]-anchorR[1])/anchorGt[5]))
                    col1 = int(round((intersection[2]-anchorR[0])/anchorGt[1])) - left1 # difference minus offset left
                    row1 = int(round((intersection[3]-anchorR[1])/anchorGt[5])) - top1
                    
                    left2 = int(round((intersection[0]-r[0])/gt[1])) # difference divided by pixel dimension
                    top2 = int(round((intersection[1]-r[1])/gt[5]))
                    col2 = int(round((intersection[2]-r[0])/gt[1])) - left2 # difference minus new left offset
                    row2 = int(round((intersection[3]-r[1])/gt[5])) - top2
                    
                    #print '\tcol1:',col1,'row1:',row1,'col2:',col2,'row2:',row2
                    if col1 != col2 or row1 != row2:
                        print "*** MEGA ERROR *** COLS and ROWS DO NOT MATCH ***"
                    # these arrays should now have the same spatial geometry though NaNs may differ
                    anchorArray = anchorBand.ReadAsArray()
                    #bandArray = band.ReadAsArray(left2,top2,col2,row2)
                    bandArray = band.ReadAsArray(int(anchorR[0]),int(anchorR[1]),int(anchorR[2]),int(anchorR[3]))
                    
            else: # same dimensions from the get go
                col1 = anchorDs.RasterXSize # = col2
                row1 = anchorDs.RasterYSize # = row2
                anchorArray = anchorBand.ReadAsArray()
                bandArray = band.ReadAsArray()
                
            #Time to test if the aligned arrays are the same size.
            fillVal = -9999
            if anchorArray.shape[0] > bandArray.shape[0]:
                print 'array1 has more rows... Padding array2 with -9999.'
                pad = anchorArray.shape[0] - bandArray.shape[0]
                temp = np.ones((pad, anchorArray.shape[1])) * fillVal
                print 'temp shape: ' + str(temp.shape)
                bandArray = np.append(bandArray, temp, axis=0)
            elif anchorArray.shape[0] < bandArray.shape[0]:
                print 'array2 has more rows... Padding array1 with -9999.'
                pad = bandArray.shape[0] - anchorArray.shape[0]
                temp = np.ones((pad, bandArray.shape[1])) * fillVal
                anchorArray = np.append(anchorArray, temp, axis=0)
            elif anchorArray.shape[1] > bandArray.shape[1]:
                #this one works!!!
                print 'array1 has more cols... Padding array2 with -9999'
                pad = anchorArray.shape[1] - bandArray.shape[1]
                temp = np.ones((anchorArray.shape[0], pad)) * fillVal
                bandArray = np.append(bandArray, temp, axis=1)
            elif anchorArray.shape[1] < bandArray.shape[1]:
                print 'array2 has more cols... Padding array1 with -9999.'
                pad = bandArray.shape[1] - anchorArray.shape[1]
                temp = np.ones((bandArray.shape[0], pad)) * fillVal
                anchorArray = np.append(anchorArray, temp, axis=1)
            else:
                print 'arrays are equal. No padding required.'
                
            outName = join(rstr, basename(rstr) + '_B%s_mask_align.tif'%bnd)
            
            print 'Testing array sizes...'
            print 'array1: ' + str(anchorArray.shape)
            print 'array2: ' + str(bandArray.shape)
            if anchorArray.shape != bandArray.shape:
                print 'im not going to WRITE ' + outName + ' because arrays still dont match. tell ross to fix the janky array size comparisson code block.'
            else:
                writeGeotiff(outName, bandArray, anchorGt, anchorProj)



def writeGeotiff(fname, data, geo_transform, projection):
    """Create a GeoTIFF file with the given data."""
    print 'write_geotiff writing ' + fname +'\n'

    driver = gdal.GetDriverByName('GTiff')
    rows, cols = data.shape
    
    ds = driver.Create(fname, cols, rows, 1, gdal_array.NumericTypeCodeToGDALTypeCode(data.dtype))
    
    ds.SetGeoTransform(geo_transform)
    ds.SetProjection(projection)
    
    band = ds.GetRasterBand(1)
    band.SetNoDataValue(-9999)
    band.WriteArray(data)
    band = None
    ds = None  # Close the file

def maskClouds(inPath, bd, maskArr):
    curBand = join(inPath, str(basename(inPath) + '_B%s_refToa32.tif'%bd))
    
    if exists(curBand):
        print 'maskClouds working on:\n' + curBand + '\n'
        
        ds = gdal.Open(curBand, gdal.GA_ReadOnly)
        band = ds.GetRasterBand(1)
        data = band.ReadAsArray()
        
        geo_transform = ds.GetGeoTransform()
        proj = ds.GetProjectionRef()
        
        rastBitType = gdal.GetDataTypeName(band.DataType)
        if rastBitType == 'Int8' or rastBitType == 'Byte':
            bitType = np.int8
        elif rastBitType == 'Int16':
            bitType = np.int16
        elif rastBitType == 'UInt16':
            bitType = np.uint16
        elif rastBitType == 'Int32':
            bitType= np.int32
        elif rastBitType == 'UInt32':
            bitType = np.uint32
        elif rastBitType == 'Float32':
            bitType = np.float32
        else:
            print '\n***Program needs to be updated to deal with ' + rastBitType + ' data...\n'
        
        
        maskedData = np.where((maskArr == 0), data, -9999).astype(bitType)
        
        return(maskedData, geo_transform, proj)
            
    else:
        print 'maskArray could not find:\n ' + curBand + '. This program requires TOARs to exist in Landsat folder. Exiting.\n'
        sys.exit(1)
        
def cloudArray(inPath):
    #this reads in a GDAL supported raster and returns a 2D numpy array named after the input raster with '_arr' appended
    mtlf = join(inPath,basename(inPath)+'_MTLFmask')
    if exists(mtlf):
        bitType = np.int16
        print 'cloudArray found:\n' + mtlf + '\n'
        
        ds = gdal.Open(mtlf, gdal.GA_ReadOnly)
        band = ds.GetRasterBand(1)
        
        rastBitType = gdal.GetDataTypeName(band.DataType)
        if rastBitType == 'Int8' or rastBitType == 'Byte':
            bitType = np.int8
        elif rastBitType == 'Int16':
            bitType = np.int16
        elif rastBitType == 'UInt16':
            bitType = np.uint16
        elif rastBitType == 'Int32':
            bitType= np.int32
        elif rastBitType == 'UInt32':
            bitType = np.uint32
        else:
            print '\n***Program needs to be updated to deal with ' + rastBitType + ' data...\n'
        
        data = band.ReadAsArray()
        
        nanArray = np.where((data == 0), 0, 1).astype(bitType)
        
        return nanArray
    else:
        print 'cloudArray could not find:\n ' + mtlf + '. This program requires that FMASK with default name already exist in the Landsat folders. Exiting.\n'
        sys.exit(1)
        
        
inputDir = r'F:\Guam_Fire_Mapping\Imagery\Landsat'
bandsList = [4,5,6,7]
workedOn = []
for root, dirs, files in walk(inputDir):
    for di in dirs:
        curPath = join(root, di)
        print 'MAIN working on:\n' + curPath + '\n'
        workedOn.append(curPath)
        
        cloudArr = cloudArray(curPath)
        for band in bandsList:
            maskLS, geo_transform, proj = maskClouds(curPath, band, cloudArr)
            outmask = join(curPath, basename(curPath)+'_B%s_mask.tif'%band)
            writeGeotiff(outmask, maskLS, geo_transform, proj)
        
        alignMasks(workedOn, bandsList)
        
            


        