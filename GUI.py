import tkinter
import cv2
import PIL.Image, PIL.ImageTk
import time
import numpy as np
import RPi.GPIO as GPIO
import mpv
import sys
import os
import serial
from time import sleep
import picamera
import io

#Initialization

#webcam/blindspot
capleft = ""
capright = ""
all_Cam_Off = 1
left_Camera_On = 0
right_Camera_On = 2
disp_camera = all_Cam_Off

#mpv for soft horn
player=mpv.MPV(start_event_thread=False)
player.audio_channels=1

serial_com = serial.Serial('/dev/ttyAMA0', 9600, timeout=4, parity=serial.PARITY_NONE,
                           stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS) #9600 8N1

#Determines which GPIO to use for right and left detection
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
right_Camera_GPIO = 2
left_Camera_GPIO = 3
GPIO.setup(right_Camera_GPIO, GPIO.IN)
GPIO.setup(left_Camera_GPIO, GPIO.IN)

def LCamOn():
    global disp_camera
    disp_camera = left_Camera_On

def CamOff():
    global disp_camera
    disp_camera = all_Cam_Off

def RCamOn():
    global disp_camera
    disp_camera = right_Camera_On

def SoftHorn():
    print("Horn Fired")
    player.play('/home/pi/car_horn.ogg')
    
def readPins():
    global disp_camera
    if(GPIO.input(right_Camera_GPIO) == GPIO.LOW):
        RCamOn()
    elif(GPIO.input(left_Camera_GPIO) == GPIO.LOW):
        LCamOn()
    else:
        CamOff()

def ser_read():
    data = ""
    buf = ""
    while(buf != '\r'):
        data += buf
        try:
            tmp = serial_com.read().decode('UTF-8')
            if(tmp == '>' or tmp == ' ' or tmp == '\n'): #ignore '>' characters
                buf = ""
            else:
                buf = tmp
        except:
            break
    return data

def serialIn():
    global serial_com
    global cur_speed
    while True:
        if(serial_com.is_open == False):
            print("Serial Thread Closed")
            quit()
        echo = ser_read()
        print("\nEcho: ")
        print(echo)
        if(echo == "010D"): #double check that next data is for correct command
            data = ser_read()
            print("\nData: ")
            print(data)
            #try:
            data = data[-2:] #get last two characters
            data = int(data[-2], 16)*16 + int(data[-1], 16) #convert hex ascii to int
            #except:
            #   data = 0 #default to 0 on failure
            print(data)
            
            cur_speed = round(int(data)/1.6)
            file = open('/tmp/cur_speed.txt', 'w')
            file.write(str(cur_speed) + " MPH")
            file.close()
            print(cur_speed)
        else:
            pass #just started or off by one

def speedlimit():
    # samples and responses include training data for number recognition
    samples = np.loadtxt(r'/home/pi/Desktop/Documents/Capstone-local/generalsamples.data',np.float32)
    responses = np.loadtxt(r'/home/pi/Desktop/Documents/Capstone-local/generalresponses.data',np.float32)
    responses = responses.reshape((responses.size,1))
    # train the classifier for number recognition - K-nearest neighbors model
    model = cv2.ml.KNearest_create()
    model.train(samples,cv2.ml.ROW_SAMPLE,responses)
    # load the pre-trained Haar Cascade classifier for speed limit detection
    speedCascade = cv2.CascadeClassifier(r"/home/pi/Desktop/Documents/Capstone-local/Classifier/haar/speedLimitStage17.xml")
    stream = io.BytesIO()
    camera = picamera.PiCamera()
    camera.framerate = 60
    camera.resolution = (800,480)
    camera.awb_mode = 'auto'
    counter = 0
    # scaleVal and neig are parameters for speed limit sign detection
    scaleVal = 1.2
    neig = 0
    #main loop
    while True:
        # the following block of code is needed to convert the image format used by the PiCamera library to the format required by the OpenCV library
        # get a picture and specify parameters
        camera.capture(stream, format = 'jpeg')
        # Convert the picture into a numpy array    
        buff = np.frombuffer(stream.getvalue(), dtype=np.uint8)
        stream.seek(0)
        # Create an OpenCV image
        img = cv2.imdecode(buff,1)
        # Convert to greyscale 
        imgGray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    
        # run object detection algorithm
        objects = speedCascade.detectMultiScale(img,scaleVal,neig) 
        for (x,y,w,h) in objects:
            # crop the image to get rid of the backround and leave only the number portion of the speedlimit sign
            speedSignCropped = img[int(np.floor((2*y+h)/2)):int(np.floor((2*y+h)/2+y+h-((2*y+h)/2))),int(np.floor(x+w*0.15)):int(np.floor(x+w*0.95))]
            # adaptive thresholding to clean up the image
            thresh = cv2.adaptiveThreshold(speedSignCropped,255,1,1,25,2)
            #Find contours within the cropped image
            temp_name,contours,hierarchy = cv2.findContours(thresh,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    
            # detected digits will be stored in this array
            speedLimitArray = []
            # For each detected contour, run the digit recognition algorithm to extract the number
            for  cnt in contours:
                # ignore contours that are too small to be a digit, contours of area less then 10 is most likely to be just a noise
                if cv2.contourArea(cnt)>10:
                    # dimwension of numbers on a speed limit sign have a certain ratio. If the detected contour is outside of this ratio, reject it. 
                    if h>15 and not(h/w>1.5) and (h/w>1):
                        cv2.rectangle(speedSignCropped,(x,y),(x+w,y+h),(0,255,0),2)
                        # specify the region of interest to which the digit recognition algorithm will be applied
                        roi = thresh[y:y+h,x:x+w]
                        roismall = cv2.resize(roi,(10,10))
                        roismall = roismall.reshape((1,100))
                        roismall = np.float32(roismall)
                        # perform digit recognition
                        retval, results, neigh_resp, dists = model.findNearest(roismall, k = 1) 
                        # store the number in the array 
                        speedLimitArray = np.append(speedLimitArray,results[0][0])

                # if more than two digits are detected, it must be an error. 
                if len(speedLimitArray) == 2:
                    counter = counter+1
                # return the speed limit only if the same speed limit has been detected three consecutive times
                if counter > 2:
                    detected = max(speedLimitArray)*10+min(speedLimitArray)
                    speedLimit = int(detected) 
                    file = open('/tmp/speedLimit.txt', 'w')
                    file.write(str(speedLimit) + " MPH")
                    file.close()
                    counter = 0;

class App:
    def __init__(self, window, window_title, video_source=0):
        self.window = window
        self.window.title(window_title)
        self.window.configure(background="white")
        self.window.attributes('-fullscreen',True)
        self.video_source = video_source

        # Create a canvas that can fit the above video source size
        self.canvas = tkinter.Canvas(window, width = 800, height = 450)
        self.canvas.pack()

        softHorn = tkinter.Button(window, text="Soft Horn", width=27, command=SoftHorn, fg='white', bg='black')
        softHorn.pack(side=tkinter.LEFT, expand=True)
        
        # After it is called once, the update method will be automatically called every delay milliseconds
        try:
            self.update()
            self.window.mainloop()
        except KeyboardInterrupt: #don't get stuck on keyboard interrupt
            pass
        
    def update(self):
        global cur_speed
        #Read GPIO here and set disp_camera
        readPins()
        
        # Get a frame from the video source
        if disp_camera==left_Camera_On:
            ret, frame = capleft.read()
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame,(800,480))
        elif disp_camera==right_Camera_On:
            ret, frame = capright.read()
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame,(800,480))
        elif disp_camera==all_Cam_Off:
            file = open('/tmp/cur_speed.txt', 'r')
            cur_speed = file.read()
            file.close()
            file = open('/tmp/speedLimit.txt', 'r')
            speedLimit = file.read()
            file.close()
            frame = np.full((480,800),240)
            frame = cv2.putText(frame,"Vehicle Speed",(150,180),cv2.FONT_HERSHEY_SIMPLEX,1,(0,0,0),4)
            frame = cv2.putText(frame,"Speed Limit",(450,180),cv2.FONT_HERSHEY_SIMPLEX,1,(0,0,0),4)
            frame = cv2.putText(frame,cur_speed,(150,300),cv2.FONT_HERSHEY_SIMPLEX,1,(0,0,0),4)
            frame = cv2.putText(frame,speedLimit,(450,300),cv2.FONT_HERSHEY_SIMPLEX,1,(0,0,0),4)

        self.photo = PIL.ImageTk.PhotoImage(image = PIL.Image.fromarray(frame))
        self.canvas.create_image(0, 0, image = self.photo, anchor = tkinter.NW)
        self.window.after(60, self.update)

# "main" function
def init():
    global capleft
    global capright
    global serial_com
    
    file = open('/tmp/cur_speed.txt', 'w')
    file.write("0 MPH")
    file.close()
    file = open('/tmp/speedLimit.txt', 'w')
    file.write("Undetected")
    file.close()
    
    pid = os.fork()
    if pid: #parent
        
        capleft = cv2.VideoCapture(1)
        capleft.set(3,800)
        capleft.set(4,800)
        capleft.set(cv2.CAP_PROP_FPS, 60)

        capright = cv2.VideoCapture(3)
        capright.set(3,200)
        capright.set(4,200)
        capright.set(cv2.CAP_PROP_FPS, 60)
        
        # Create a window and pass it to the Application object
        def check():
            root.after(50, check)
            
        root = tkinter.Tk()
        root.after(50, check) #prevent tk from getting stuck on a keyboard interrupt

        App(root, "Main")
        print(disp_camera)
        
        root.destroy() #exit the application
        capleft.release() #cleanly release the cameras
        capright.release()
        serial_com.close()
        cur_speed.close()
        print("Done") 
    else: #child
        pid = os.fork() #fork again and run both threads
        if pid:
            serialIn()
        else:
            speedlimit()

init()
