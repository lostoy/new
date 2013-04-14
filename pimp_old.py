#importing and stuff
from SimpleCV import *
import time
import pygame
import os

from pytesser import image_to_string
import numpy
import cv2
import cv

import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email import Encoders

#import logging
#logging.basicConfig(level=logging.DEBUG)  #logging.ERROR
#logging.debug("Inside f!")

#constants
#display
FULLSCREEN_WIDTH = 1366
FULLSCREEN_HEIGHT = 768
IMG_MAXWIDTH = 1024
IMG_MAXHEIGHT = 768
SCANPAGE_START = 7
ENDPAGENO = 15
NOPAGENO_LIMIT = 20 #no of loops of not seeing a page no before we switch off the projected image

#scanning
BG_VARIANCE_THRESHOLD = 800
MOTION_THRESHOLD = 2.0
NOMOTIONFRAMES_THRESHOLD = 20
REC_TOLERANCE = 0.15

#camera
CAM_WIDTH = 1920
CAM_HEIGHT = 1080

#pageno read
PAGENO_BINARIZE_THRESHOLD = 100

#filesave, fileread
FILEDIR = "Photos"
SCANDIR = "ScanPhotos"

#common data for all files
cam = Camera(0)

cv.SetCaptureProperty( cam.capture, cv.CV_CAP_PROP_FRAME_WIDTH, CAM_WIDTH );
cv.SetCaptureProperty( cam.capture, cv.CV_CAP_PROP_FRAME_HEIGHT, CAM_HEIGHT );

disp = Display(resolution=(FULLSCREEN_WIDTH,FULLSCREEN_HEIGHT), flags=pygame.FULLSCREEN)
filelist = os.listdir(FILEDIR)
read_list = [0]*(SCANPAGE_START-1);

#move to constants after calibration
#SCAN_BOUNDARY = (341, 172, 765, 685)
SCAN_TRANSFORMMATRIX =  numpy.array([[ -67.1059559,   111.739701,  -15603.6881], [ -55.3248063,  -15.2620155,   20317.5582],  [ -578.981747,  -196.935921e-02,   1.00000000]],numpy.float32)
PAGENO_BOUNDARY = (42, 82, 151, 195)#(75, 101, 207, 208)
PROJECTION_CORNERPOINTS = ((1146, 767), (168, 709), (192, 0), (1233, 47))#((0, 0), (1365, 0), (1365, 767), (0, 767))


#define functions

def filelist_refresh():
    filelist = os.listdir(FILEDIR)
    filelist = ((time.ctime(os.path.getctime("Photos/"+picture)),picture) for picture in filelist if picture != "desktop.ini")
    filelist = sorted(filelist, reverse=True)
    filelist = [picture for ctime,picture in filelist]
    print "Download folder read, no of photos: ",len(filelist)

def drawblankscreen():
    img = Image((FULLSCREEN_WIDTH,FULLSCREEN_HEIGHT))
    img.drawRectangle(1,1,FULLSCREEN_WIDTH,FULLSCREEN_HEIGHT,color=Color.BLACK,width=0)
    img.save(disp)

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
    img = img.applyLayers()
    img = img.embiggen((FULLSCREEN_WIDTH,FULLSCREEN_HEIGHT),color=Color.BLACK)
    img = img.warp(PROJECTION_CORNERPOINTS)
    img = img.embiggen((FULLSCREEN_WIDTH,FULLSCREEN_HEIGHT),color=Color.BLACK)
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

#calibrate - get area from camera to be cropped for scanning; for page no
def calibrate():
    #calibrate page no area
    while(True):
        img = cam.getImage()
        img.drawText(text="Page Number Area calibration", x=0.4*CAM_WIDTH, y=0.1*CAM_HEIGHT, color=(0, 255, 0), fontsize=54)
        img.save(disp)
        disp.checkEvents()
        dwn=disp.leftButtonDownPosition()
        if dwn!=None:
#            print "TopLeft: ",dwn
            break
    while(True):
        img = cam.getImage()
        img.save(disp)
        disp.checkEvents()
        up=disp.leftButtonDownPosition()
        if up!=None:
#            print "BottomRight: ",up
            break
    PAGENO_BOUNDARY=disp.pointsToBoundingBox(up,dwn)
    print "Page No Boundary: ",PAGENO_BOUNDARY
    time.sleep(0.2)

    #calibrate scan area
##    while(True):
##        img = cam.getImage()
##        img.save(disp)
##        disp.checkEvents()
##        dwn=disp.leftButtonDownPosition()
##        if dwn!=None:
###            print "TopLeft: ",dwn
##            break
##    while(True):
##        img = cam.getImage()
##        img.save(disp)
##        disp.checkEvents()
##        up=disp.leftButtonDownPosition()
##        if up!=None:
###            print "BottomRight: ",up
##            break
##    SCAN_BOUNDARY=disp.pointsToBoundingBox(up,dwn)
##    print "Scan Area Boundary: ",SCAN_BOUNDARY
##    time.sleep(0.2)
    pt1 = None
    pt2 = None
    pt3 = None
    pt4 = None
    while not disp.isDone():
        img = cam.getImage()
        img.drawText(text="Scan Area calibration", x=0.4*CAM_WIDTH, y=0.1*CAM_HEIGHT, color=(0, 255, 0), fontsize=54)
        img.save(disp)
        if disp.mouseLeft:
            if(pt1 is None):
                pt1 = ((int) (disp.mouseRawX*CAM_WIDTH/FULLSCREEN_WIDTH),(int) (disp.mouseRawY*CAM_HEIGHT/FULLSCREEN_HEIGHT))
            elif(pt2 is None):
                temp = ((int) (disp.mouseRawX*CAM_WIDTH/FULLSCREEN_WIDTH),(int) (disp.mouseRawY*CAM_HEIGHT/FULLSCREEN_HEIGHT))
                if pt1 != temp:
                    pt2 = temp
            elif(pt3 is None):
                temp = ((int) (disp.mouseRawX*CAM_WIDTH/FULLSCREEN_WIDTH),(int) (disp.mouseRawY*CAM_HEIGHT/FULLSCREEN_HEIGHT))
                if pt2 != temp:
                    pt3 = temp
            elif(pt4 is None):
                temp = ((int) (disp.mouseRawX*CAM_WIDTH/FULLSCREEN_WIDTH),(int) (disp.mouseRawY*CAM_HEIGHT/FULLSCREEN_HEIGHT))
                if pt3 != temp:
                    pt4 = temp
            else:
                break
    
    print "Scan corner positions: ", (pt1,pt2,pt3,pt4)
    src = numpy.array([pt1,pt2,pt3,pt4],numpy.float32) #source points
    dst = numpy.array([[0,0],[1280,0],[1280,720],[0,720]],numpy.float32) #destination points 
    SCAN_TRANSFORMMATRIX = cv2.getPerspectiveTransform(src,dst) #calculate transform matrix
    print "Scan transform matrix: ", SCAN_TRANSFORMMATRIX
    time.sleep(0.2)
##    cam_img = cam.getImage()
##    cam_img = cam_img.transformPerspective(SCAN_TRANSFORMMATRIX)
##    cam_img = cam_img.crop(0,0,1280,720)
##    cam_img.save(disp)
##    time.sleep(10)
    
    #calibrate projection area
    drawblankscreen()
    img.drawText(text="Projection Area calibration", x=0.4*CAM_WIDTH, y=0.1*CAM_HEIGHT, color=(0, 255, 0), fontsize=54)
    pt1 = None
    pt2 = None
    pt3 = None
    pt4 = None
    while not disp.isDone():
        if disp.mouseLeft:
            if(pt1 is None):
                pt1 = (disp.mouseRawX,disp.mouseRawY)
            elif(pt2 is None):
                temp = (disp.mouseRawX,disp.mouseRawY)
                if pt1 != temp:
                    pt2 = temp
            elif(pt3 is None):
                temp = (disp.mouseRawX,disp.mouseRawY)
                if pt2 != temp:
                    pt3 = temp
            elif(pt4 is None):
                temp = (disp.mouseRawX,disp.mouseRawY)
                if pt3 != temp:
                    pt4 = temp
            else:
                break

    PROJECTION_CORNERPOINTS = (pt1,pt2,pt3,pt4)
    print "Projection corner positions: ", PROJECTION_CORNERPOINTS

       
def sendemail(to, subject, text, attach):
    gmail_user = "familyalbumme310@gmail.com"
    gmail_pwd = "microsoftme310"

    msg = MIMEMultipart()

    msg['From'] = gmail_user
    msg['To'] = to
    msg['Subject'] = subject

    msg.attach(MIMEText(text))

    part = MIMEBase('application', 'octet-stream')
    part.set_payload(open(attach, 'rb').read())
    Encoders.encode_base64(part)
    part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(attach))
    msg.attach(part)

    mailServer = smtplib.SMTP("smtp.gmail.com", 587)
    mailServer.ehlo()
    mailServer.starttls()
    mailServer.ehlo()
    mailServer.login(gmail_user, gmail_pwd)
    mailServer.sendmail(gmail_user, to, msg.as_string())
    # Should be mailServer.quit(), but that crashes...
    mailServer.close()
    
def readpageno(image):
    img = image.crop(PAGENO_BOUNDARY).copy()
    
##    img.save(disp)
##    time.sleep(1)
    
##    return (int) ((time.time()/4)% 6)
    return 8

    img = img.binarize(PAGENO_BINARIZE_THRESHOLD)
    img = img.invert()
    
##    img.save(disp)
##    time.sleep(1)
   
    corners = img.findCorners() #Finding 4 vertices
    
    cornerxy = corners.coordinates()
    try:
        xmin = min([item[0] for item in cornerxy]) 
        xmax = max([item[0] for item in cornerxy]) 
        ymin = min([item[1] for item in cornerxy]) 
        ymax = max([item[1] for item in cornerxy])
    except ValueError:
        print "No corners detected"
        return -1
    
    
    top = [item for item in cornerxy if item[1]  == ymin][0]
    bottom = [item for item in cornerxy if item[1] == ymax][0]
    left = [item for item in cornerxy if item[0] == xmin][0]
    right = [item for item in cornerxy if item[0] == xmax][0]

##    corners.draw()    
##    img.dl().circle(top,10)
##    img.dl().circle(bottom,10)
##    img.dl().circle(left,10)
##    img.dl().circle(right,10)
##    img.save(disp)
##    time.sleep(1)
    
    src = numpy.array([right,bottom,left,top],numpy.float32) #source points        
    cube_l = min(PAGENO_BOUNDARY[2],PAGENO_BOUNDARY[3])  
    dst = numpy.array([[0,0],[cube_l,0],[cube_l,cube_l],[0,cube_l]],numpy.float32) #destination points     
    T = cv2.getPerspectiveTransform(src,dst) #calculate transform matrix    
    img = img.transformPerspective(T)  
    Linewidth = cube_l/6
    img = img.crop(0,0,cube_l,cube_l) #get rid of the frame
    img = img.rotate(-137)
    img = img.crop(0.9*Linewidth,1.2*Linewidth,cube_l-2.1*Linewidth,cube_l-2.2*Linewidth)

##    img.save(disp)
##    time.sleep(1)
    
    text = image_to_string(img) #detect the number
    print text
    try:
        int(text)
        if (int(text) >= 0) and (int(text) <= ENDPAGENO):
            return int(text)
        else:
            return -1
    except ValueError:
        return -1
                #Improvement - if D,O,0, change it to 0, L,l to 1 etc

   
#initial empty screen
drawblankscreen()

#read files
filelist_refresh()

#calibrate - we can remove this and hardcode constants later
#calibrate()

#loopcount
count = 0; #count of iterations to refresh the folder data
nonecount = 0; #count of times no 
nomotioncount = 0; #while scanning, no of frames without motion
cam_img0 = cam.getImage().transformPerspective(SCAN_TRANSFORMMATRIX) #while scanning, save older image to check motion
cam_img0 = cam_img0.crop(0,0,1280,720)
#time.sleep(2) #is this enough time for the cam to automatically adjust focus and brightness?

#loop until Esc is pressed
while not disp.isDone():
    cam_img = cam.getImage()
    pgno = readpageno(cam_img)
    print pgno
    if pgno != -1: #page detected
        if pgno <= SCANPAGE_START:
            if pgno == 0: #contents page
                drawcontentspage()
            elif pgno <= len(filelist): #photo exists for this page
                filename = filelist[pgno-1]
                if os.path.isfile(FILEDIR+"/"+filename): #file exists
                    disp_img = Image(FILEDIR+"/"+filename)
                    drawimage(disp_img)
                    read_list[pgno-1] = 1; #marked as read
                else:
                    print "Major error! File "+FILEDIR+"/"+filename+" is missing!"
            else:
                drawblankscreen() #no picture for this page yet
        else: #now we are on the scan pages
            if os.path.isfile(SCANDIR+"/"+str(pgno)+".png"): #file exists, so already scanned
                disp_img = Image(SCANDIR+"/"+str(pgno)+".png")
                drawimage(disp_img)
            else: #no file, ready to be scanned
                cam_img = cam_img.transformPerspective(SCAN_TRANSFORMMATRIX)
                cam_img = cam_img.crop(0,0,1280,720)
                bg_variance = cam_img.getNumpy().var()
##                print "Variance: ", bg_variance
                if bg_variance > BG_VARIANCE_THRESHOLD: #page is not empty
                    diff = (cam_img - cam_img0)
                    mean_diff = diff.getNumpy().mean()
##                    print "Mean difference with previous image: ",mean_diff
                    if mean_diff < MOTION_THRESHOLD: #no motion
                        nomotioncount = nomotioncount + 1
                    else:
                        nomotioncount = 0
                    if nomotioncount >= NOMOTIONFRAMES_THRESHOLD:
###################### -- begin unclean code -- ##########################
                        
                        fs = cam_img.smartFindBlobs(mask=None, rect=(10,10,cam_img.width-20,cam_img.height-20), thresh_level=2, appx_level=3) #selected rectangle with just the outer 10 pixels on each side removed
                        if( fs is not None ):
##                            fs.draw()
                            if fs[-1].isRectangle(REC_TOLERANCE):
##                                vertices = fs[-1].minRect() # (now I need to get these vertices to normal shape)
##                                img = cam_img.rotate(angle=fs[-1].angle(),point=(vertices[0][0],vertices[0][1])) #rotate - We need to find the vertex in the top left corner!!!########################
##                                img = img.crop(vertices[0][0]+2,vertices[0][1]+2,fs[-1].minRectWidth()-4,fs[-1].minRectHeight()-4) #haven't been checked yet. I have shaved off 2 pixels on each side, dont know how well it will work
                                img = cam_img.rotate(angle=fs[-1].angle())
                                fs = img.smartFindBlobs(mask=None, rect=(10,10,cam_img.width-20,cam_img.height-20), thresh_level=2, appx_level=3)
                                rect = fs[-1].minRect()

                                minX = min(rect[0][0], rect[1][0],rect[2][0], rect[3][0])
                                maxX = max(rect[0][0], rect[1][0],rect[2][0], rect[3][0])
                                minY = min(rect[0][1], rect[1][1],rect[2][1], rect[3][1])
                                maxY = max(rect[0][1], rect[1][1],rect[2][1], rect[3][1])

                                W = maxX - minX #width
                                H = maxY - minY #height

                                img = img.crop(minX,minY,W,H)
                                img = img.scale(3.0)
                                
####################### -- end unclean code -- ##########################
                                img.save(SCANDIR+"/"+str(pgno)+".png")
                                sendemail("misheljohns@gmail.com", "Photo Scanned by Mrs. G Randma", "Mrs. G Randma has scanned this photo using the family album.", SCANDIR+"/"+str(pgno)+".png")

                else: #page is empty
                    nomotioncount = 0
                cam_img0 = cam_img
    else: #no page detected - either the page no is covered or the book is closed
        print "No page no detected"
        nonecount = nonecount + 1
        if nonecount >= NOPAGENO_LIMIT:
            drawblankscreen()
            nonecount = 19
    time.sleep(0.01)    
    if disp.isDone():
        exit(0)
    count = count + 1
    if count >= 500:
        filelist_refresh()
        count = 0
