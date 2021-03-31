import tkinter
import cv2
import PIL.Image, PIL.ImageTk
import time
import numpy as np
import mpv

#Initialization

capleft = cv2.VideoCapture(1)
capleft.set(3,800)
capleft.set(4,800)
capleft.set(cv2.CAP_PROP_FPS, 60)

capright = cv2.VideoCapture(3)
capright.set(3,200)
capright.set(4,200)
capright.set(cv2.CAP_PROP_FPS, 60)

speed = 65
all_Cam_Off = 1
left_Camera_On = 0
right_Camera_On = 2
disp_camera = all_Cam_Off

player=mpv.MPV()
player.audio_channels=1

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
         LcamOn = tkinter.Button(window, text="CAM L On", width=27, height = 1, command=LCamOn, fg='white', bg='black')
         LcamOn.pack(side=tkinter.LEFT, expand=True)
         RcamOn = tkinter.Button(window, text="CAM R On", width=27, command=RCamOn, fg='white', bg='black')
         RcamOn.pack(side=tkinter.RIGHT, expand=True)
         camOff = tkinter.Button(window, text="CAM Off", width=27, command=CamOff, fg='white', bg='black')
         camOff.pack(side=tkinter.RIGHT, expand=True)


         # After it is called once, the update method will be automatically called every delay milliseconds

         self.update()
         self.window.mainloop()

      def update(self):
             # Get a frame from the video source
             if disp_camera==left_Camera_On:
                 ret, frame = capleft.read()
                 frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                 frame = cv2.resize(frame,(800,480))
             elif disp_camera==right_Camera_On:
                 ret, frame = capright.read()
                 frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                 frame = cv2.resize(frame,(800,480))
             elif disp_camera==1:
                 frame = np.full((480,800),240)
                 frame = cv2.putText(frame,"Current Speed",(50,50),cv2.FONT_HERSHEY_SIMPLEX,1,(0,0,0),4)
                 #frame = cv2.imread("SL30_resized.png")

             self.photo = PIL.ImageTk.PhotoImage(image = PIL.Image.fromarray(frame))
             self.canvas.create_image(0, 0, image = self.photo, anchor = tkinter.NW)
             self.window.after(60, self.update)

"""
class MyVideoCapture:
     def __init__(self, video_source=0):
         # Open the video source
         self.vid1 = cv2.VideoCapture(1)
         self.vid1.set(3,800)
         self.vid1.set(4,480)

     def get_frame(self):
         if disp_camera==0:
             ret, frame = self.vid1.read()
             return (ret, cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
         elif disp_camera==1:
             return(True,np.zeros((480,800)))


     # Release the video source when the object is destroyed
     def __del__(self):
         if self.vid1.isOpened():
             self.vid1.release()
"""


 # Create a window and pass it to the Application object

App(tkinter.Tk(), "Main")
print(disp_camera)
