# -*- coding: utf-8 -*-
"""
Created on Wed May 11 15:55:22 2016

@author: Ross
"""

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