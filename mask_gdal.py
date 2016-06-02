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
from os import walk, makedirs 
from os.path import join, basename, exists
#import datetime

def rasterCalc(workedOn, bandsList):
    sortList = sorted(workedOn)
    ind = 0
    while ind < len(sortList) - 1:
        for band in bandsList:
            nex = ind + 1
            print '\ncomparing band %s of: '%band + basename(sortList[ind]) + ' and ' + basename(sortList[nex]) + '\n'
            
            band_1_gdal = gdal.Open(join(sortList[ind],basename(sortList[ind]) + '_B%s_mask_align.tif'%band))
            band_1 = band_1_gdal.GetRasterBand(1)
            band_1_array = band_1.ReadAsArray()
            gt1 = band_1_gdal.GetGeoTransform()
            proj1 = band_1_gdal.GetProjectionRef()
            
            
            band_2_gdal = gdal.Open(join(sortList[nex],basename(sortList[nex]) + '_B%s_mask_align.tif'%band))
            band_2 = band_2_gdal.GetRasterBand(1)
            band_2_array = band_2.ReadAsArray()
            
            out = join(sortList[ind], str(basename(sortList[ind]))[13:16] + '-' + str(basename(sortList[nex]))[13:16] + '_B%s.tif'%band)
            
            array1 = band_1_array > -9999
            print array1.shape
            array2 = band_2_array > -9999
            print array2.shape
            
            mask = np.logical_and(array1, array2)
            
            maskedData = np.where(mask == True, np.absolute((band_1_array - band_2_array) / band_1_array), -9999)
        
            writeGeotiff(out, maskedData, gt1, proj1)
        ind+=1
        
def deltaNBR(workedOn):
    sortList = sorted(workedOn)
    ind = 0
    while ind < len(sortList) - 1:
        for rstr in sortList:
            nex = ind + 1
            print '\nDeltaing NBR1s of: ' + basename(sortList[ind]) + ' and ' + basename(sortList[nex]) + '\n'
            
            nbr1 = gdal.Open(join(sortList[ind],basename(sortList[ind]) + '_NBR1.tif'))
            nbr1Arr = nbr1.ReadAsArray()
            gt = nbr1.GetGeoTransform()
            proj = nbr1.GetProjectionRef()
            
            nbr2 = gdal.Open(join(sortList[nex],basename(sortList[nex]) + '_NBR1.tif'))
            nbr2Arr = nbr2.ReadAsArray()
            
            filtered1 = nbr1Arr > -9999
            filtered2 = nbr2Arr > -9999
            
            mask = np.logical_and(filtered1, filtered2)
            
            maskedData = np.where(mask == True, nbr1Arr - nbr2Arr, -9999)
            
            outName = join(sortList[ind], str(basename(sortList[ind]))[13:16] + '-' + str(basename(sortList[nex]))[13:16] + 'dnbr1.tif')
            
            writeGeotiff(outName, maskedData, gt, proj)
        ind+=1
        
def nbr(workedOn):
    for rstr in workedOn:
        ds5 = gdal.Open(join(rstr, basename(rstr) + '_B5_mask_align.tif'))
        band5Arr = ds5.ReadAsArray()
        
        gt = ds5.GetGeoTransform()
        proj = ds5.GetProjectionRef()
        
        ds6 = gdal.Open(join(rstr, basename(rstr) + '_B6_mask_align.tif'))
        band6Arr = ds6.ReadAsArray()
        
        ds7 = gdal.Open(join(rstr, basename(rstr) + '_B7_mask_align.tif'))
        band7Arr = ds7.ReadAsArray()
        
        filter5 = band5Arr > -9999
        filter6 = band6Arr > -9999
        filter7 = band7Arr > -9999
        mask = np.logical_and(filter5, filter6, filter7)
        
        nbr1 = np.where(mask == True, (band5Arr - band7Arr)/(band5Arr + band7Arr), -9999)
        
        nbr2 = np.where(mask == True, (band6Arr - band7Arr)/(band6Arr + band7Arr), -9999)
        
        out1 = join(rstr, basename(rstr) + '_NBR1.tif')
        out2 = join(rstr, basename(rstr) + '_NBR2.tif')
        
        writeGeotiff(out1, nbr1, gt, proj)
        writeGeotiff(out2, nbr2, gt, proj)

def alignMasks(workedOn,bandsList):
    #code adapted from http://sciience.tumblr.com/post/101722591382/finding-the-georeferenced-intersection-between-two

    # prep some lists we will need
    sortList = sorted(workedOn)
    ltrbs = []
    
    #scan all of our input rasters and grab their geotransform, convert that to a bounding box
    for rstr in sortList:
        for bnd in bandsList:
            ds = gdal.Open(join(rstr, basename(rstr) + '_B%s_mask.tif'%bnd), gdal.GA_ReadOnly)
            band = ds.GetRasterBand(1)
            gt = ds.GetGeoTransform()
            ltrb = [gt[0], gt[3], gt[0] + (gt[1] * ds.RasterXSize), gt[3] + (gt[5] * ds.RasterYSize), gt[1], gt[5], ds.RasterXSize, ds.RasterYSize]
            ltrbs.append(ltrb)
            ds = None
            
    #intitalize the intersections with some plausible values (the first raster)
    intersect = [ltrbs[0][0],ltrbs[0][1],ltrbs[0][2],ltrbs[0][3]]
    
    #update our intersects with all of the geotransforms we collected earlier
    for ltrb in ltrbs:
        if ltrb[0] > intersect[0]:
            intersect[0] = ltrb[0]
        if ltrb[3] > intersect[3]:
            intersect[3] = ltrb[3]
        if ltrb[1] < intersect[1]:
            intersect[1] = ltrb[1]
        if ltrb[2] < intersect[2]:
            intersect[2] = ltrb[2]
    
    #time to come up with an offset for each raster based on intersect. We will clip to the intersection bounding box.
    for rstr in sortList:
        print str(rstr)
        for bnd in bandsList:
            ds = gdal.Open(join(rstr, basename(rstr) + '_B%s_mask.tif'%bnd), gdal.GA_ReadOnly)
            band = ds.GetRasterBand(1)
            gt = ds.GetGeoTransform()
            proj = ds.GetProjection()
            offsetX = int(round((intersect[0]-gt[0])/gt[1])) # difference divided by pixel dimension
            offsetY = int(round((intersect[1]-gt[3])/gt[5]))
            col = int(round((intersect[2]-gt[0])/gt[1])) - offsetX # difference minus offset left
            row = int(round((intersect[3]-gt[3])/gt[5])) - offsetY
        
            bandArray = band.ReadAsArray(offsetX, offsetY, col, row)
            intersectGt = (intersect[0], gt[1], 0, intersect[1], 0, gt[5])
            outName = join(rstr, basename(rstr) + '_B%s_mask_align.tif'%bnd)
            
            writeGeotiff(outName, bandArray, intersectGt, proj)

def writeGeotiff(fname, data, geo_transform, projection):
    """Create a GeoTIFF file with the given data."""
    print '\nwrite_geotiff writing ' + fname +'\n'

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
        outName = join(inPath, basename(inPath)+'_B%s_mask.tif'%bd)
        
        writeGeotiff(outName, maskedData, geo_transform, proj)
        
            
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


inputDir = r'G:\Guam_Fire_Mapping\Imagery\Landsat'
#outDir = r'G:\Guam_Fire_Mapping\firePrep'
bandsList = [5,6,7]
workedOn = []

'''
#make a prep folder to hold outputs:
if exists(outDir):
    print 'outputs to: ' + outDir
else:
    print 'making ' + outDir
    makedirs(outDir)
'''    

#start the main program
for root, dirs, files in walk(inputDir):
    for di in dirs:
        curPath = join(root, di)
        print 'MAIN:\n' + curPath + '\n'
        #Prep one at a time. But lets keep a running tally of all the directories we have worked on. After prep we are going need to compare all images at once.
        workedOn.append(curPath)
        '''
        #grab the current cloudarray, make a NaN array
        cloudArr = cloudArray(curPath)
        for band in bandsList:
            maskClouds(curPath, band, cloudArr)
        '''
#alignMasks(workedOn, bandsList)
nbr(workedOn)
deltaNBR(workedOn)


        