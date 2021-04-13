import tkinter
import cv2
import PIL.Image, PIL.ImageTk
import time
import numpy as np
import RPi.GPIO as GPIO
import mpv
import sys
from os import fork
from collections import deque
import serial
from time import sleep

#Initialization

capleft = ""
capright = ""

cur_speed = 0
speed = deque(maxlen=1) #thread safe
all_Cam_Off = 1
left_Camera_On = 0
right_Camera_On = 2
disp_camera = all_Cam_Off

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
    while(buf != '\n'): #DEBUG needs to be '\r' for the actual OBD converter
        data += buf
        try:
            buf = serial_com.read().decode('UTF-8')
        except:
            break
    return data

def serialIn():
    global speed
    global serial_com
    while True:
        if(serial_com.is_open == False):
            print("Serial Thread Closed")
            quit()
        echo = ser_read()
        if(echo == "010D"): #double check that next data is for correct command
            data = ser_read()
            try:
                speed.append(round(int(data)/1.6)) #strip line of CRLF, interpret as int, convert kmh to mph, then round to nearest whole number and store in speed deque
            except ValueError:
                print("ValueError exception")
                pass #tried to convert 010D instead of actual data
        else:
            pass #just started or off by one
        
class App:
    def __init__(self, window, window_title, video_source=0):
        self.window = window
        self.window.title(window_title)
        self.window.configure(background="white")
        self.window.attributes('-fullscreen',True)
        self.video_source = video_source
        # open video source (by default this will try to open the computer webcam)
        #self.vid = MyVideoCapture(self.video_source)

        # Create a canvas that can fit the above video source size
        self.canvas = tkinter.Canvas(window, width = 800, height = 450)
        self.canvas.pack()

        softHorn = tkinter.Button(window, text="Soft Horn", width=27, command=SoftHorn, fg='white', bg='black')
        softHorn.pack(side=tkinter.LEFT, expand=True)
        #LcamOn = tkinter.Button(window, text="CAM L On", width=27, height = 1, command=LCamOn, fg='white', bg='black')
        #LcamOn.pack(side=tkinter.LEFT, expand=True)
        #RcamOn = tkinter.Button(window, text="CAM R On", width=27, command=RCamOn, fg='white', bg='black')
        #RcamOn.pack(side=tkinter.RIGHT, expand=True)
        #camOff = tkinter.Button(window, text="CAM Off", width=27, command=CamOff, fg='white', bg='black')
        #camOff.pack(side=tkinter.RIGHT, expand=True)

        # After it is called once, the update method will be automatically called every delay milliseconds
        try:
            self.update()
            self.window.mainloop()
        except KeyboardInterrupt: #don't get stuck on keyboard interrupt
            pass

    def update(self):
        global speed
        global cur_speed
        #Read GPIO here and set disp_camera
        readPins()
        
        #check if a new value for speed is available
        try:
            cur_speed = speed.pop()
            print("current speed " + cur_speed)
        except IndexError:
            pass #deque is empty, skip until there's new data
        
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
            frame = np.full((480,800),240)
            frame = cv2.putText(frame,str(cur_speed),(50,50),cv2.FONT_HERSHEY_SIMPLEX,1,(0,0,0),4)
            #frame = cv2.imread("SL30_resized.png")

        self.photo = PIL.ImageTk.PhotoImage(image = PIL.Image.fromarray(frame))
        self.canvas.create_image(0, 0, image = self.photo, anchor = tkinter.NW)
        self.window.after(60, self.update)



# "main" function
def init():
    global capleft
    global capright
    global serial_com
    
    pid = fork()
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
        print("Done") 
    else: #child
        serialIn()

init()