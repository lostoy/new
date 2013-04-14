#importing and stuff
from SimpleCV import *
import time
import pygame
import os
import cv2

FULLSCREEN_WIDTH = 1366
FULLSCREEN_HEIGHT = 768
IMG_MAXWIDTH = 1024
IMG_MAXHEIGHT = 768

PROJECTION_CORNERPOINTS = ((0, 0), (1365, 0), (1365, 767), (0, 767))

FILEDIR = "Photos_old"

disp = Display(resolution=(FULLSCREEN_WIDTH,FULLSCREEN_HEIGHT), flags=pygame.FULLSCREEN)

def drawblankscreen():
    img = Image((FULLSCREEN_WIDTH,FULLSCREEN_HEIGHT))
    img.drawRectangle(1,1,FULLSCREEN_WIDTH,FULLSCREEN_HEIGHT,color=Color.BLACK,width=0)
    img.save(disp)

def drawimage(image):
    img = image
    if(img.width > IMG_MAXWIDTH):
        img = img.resize(w = IMG_MAXWIDTH)
    if(img.height > IMG_MAXHEIGHT):
        img = img.resize(h = IMG_MAXHEIGHT)
    img = img.embiggen((FULLSCREEN_WIDTH,FULLSCREEN_HEIGHT),color=Color.BLACK)
    img = img.warp(PROJECTION_CORNERPOINTS)
    img = img.embiggen((FULLSCREEN_WIDTH,FULLSCREEN_HEIGHT),color=Color.BLACK)
    img.save(disp)    


choice = -1;
print "starting"
while not disp.isDone():
    #disp.checkEvents()
    up = disp.leftButtonDownPosition()
    if up!=None:
        print up
        choice = int(13.5*up[0]/FULLSCREEN_WIDTH)
        print choice
    if choice == -1:
        print "blankscreen"
        drawblankscreen()
    else:
        disp_img = Image(FILEDIR+"/"+str(choice)+".jpg")
        drawimage(disp_img)
    time.sleep(0.01)
    
