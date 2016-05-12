# -*- coding: utf-8 -*-
"""
Created on Wed May 11 16:02:26 2016

@author: Ross
"""

def DmCheck(Invalue):
    #This formats months/days
    if Invalue < 10:
        Outvalue = '0' +\
                   str(Invalue)
    else:
        Outvalue = str(Invalue)
    return Outvalue


def getImageInfo(imgPath):
    #this reads in the name of Landsat images and returns information
    if imgPath == 'None':
        return 'None', 'None', 'None', 'None'
    elif imgPath== '':
        return 'None', 'None', 'None', 'None'
    else:
        img = basename(imgPath)
        
        #Get Sensor Information
        imgSensor = img[1]
        
        #Get Sat Information
        imgSat = img[2]
        
        #Get Date Information
        imgYear = img[9:13]
        imgJDay = img[13:16]
        
        imgDate = (datetime.datetime.strptime(imgYear + ' ' + imgJDay, '%Y %j')).strftime('%m/%d/%Y')
        
        imgSplit = imgDate.split('/')
        imgMonth = DmCheck(int(imgSplit[0]))
        imgDay = DmCheck(int(imgSplit[1]))
        
        return imgSensor, imgSat, imgYear, imgJDay, imgDate, imgMonth, imgDay