#importing and stuff
from SimpleCV import *
import time
import pygame
import os

#constants
#display
FULLSCREEN_WIDTH = 1366
FULLSCREEN_HEIGHT = 768
IMG_MAXWIDTH = 1024
IMG_MAXHEIGHT = 768
SCANPAGE_START = 70
ENDPAGENO = 15
NOPAGENO_LIMIT = 20 #no of loops of not seeing a page no before we switch off the projected image


#filesave, fileread
FILEDIR = "photos"
SCANDIR = "ScanPhotos"

disp = Display(resolution=(FULLSCREEN_WIDTH,FULLSCREEN_HEIGHT), flags=pygame.FULLSCREEN)
filelist = os.listdir(FILEDIR)
read_list = [0]*(SCANPAGE_START-1);

PROJECTION_CORNERPOINTS = ((0, 0), (1365, 0), (1365, 767), (0, 767))

def drawcontentspage():
    img = SimpleCV.Image((IMG_MAXWIDTH,IMG_MAXHEIGHT))
    i = 1
    img.drawText(text="Family Album", x=0.4*IMG_MAXWIDTH, y=0.1*IMG_MAXHEIGHT, color=(0, 255, 0), fontsize=54)
    for picture in filelist:
        if i >= (SCANPAGE_START):
            break
        #text="Page "+str(i)+" : "+os.path.splitext(picture)[0]
        img.drawText(text=str(i)+" : "+os.path.splitext(picture)[0], x=0.2*IMG_MAXWIDTH, y=0.2*IMG_MAXHEIGHT+i*0.05*IMG_MAXHEIGHT, color=(255, 255, 255), fontsize=42)
        if read_list[i-1] == 0:
            img.drawText(text="New!", x=0.1*IMG_MAXWIDTH, y=0.2*IMG_MAXHEIGHT+i*0.05*IMG_MAXHEIGHT, color=(255, 0, 0), fontsize=42)
        i = i + 1
    #return img
    img = img.applyLayers()
    img = img.embiggen((FULLSCREEN_WIDTH,FULLSCREEN_HEIGHT),color=Color.BLACK)
    img = img.warp(PROJECTION_CORNERPOINTS)
    img = img.embiggen((FULLSCREEN_WIDTH,FULLSCREEN_HEIGHT),color=Color.BLACK)
    img.save(disp)
    time.sleep(0.1)

def filelist_refresh():
    filelist = os.listdir(FILEDIR)
    filelist = ((time.ctime(os.path.getctime("photos/"+picture)),picture) for picture in filelist if picture != "desktop.ini")
    filelist = sorted(filelist, reverse=True)
    filelist = [picture for ctime,picture in filelist]
    print "Download folder read, no of photos: ",len(filelist)

#read files
filelist_refresh()
print filelist
while(True):
    drawcontentspage()
    

