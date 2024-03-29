import numpy as np
import cv2
from picamera import PiCamera
print('cv2 imported')

############# Digit Training ###############################
samples = np.loadtxt('generalsamples.data',np.float32)
responses = np.loadtxt('generalresponses.data',np.float32)
responses = responses.reshape((responses.size,1))

model = cv2.ml.KNearest_create()
model.train(samples,cv2.ml.ROW_SAMPLE,responses)
#############################################################

def empty(a):
    pass

############# Track bar setup ###############################
trackBarName = "Track bar"
cv2.namedWindow(trackBarName)
cv2.resizeWindow(trackBarName,640,640)
cv2.createTrackbar("Scale",trackBarName,100,1000,empty)
cv2.createTrackbar("Neig",trackBarName,0,20,empty)
cv2.createTrackbar("Min Area", trackBarName, 0,100000,empty)
#############################################################

############# Load Camera & Classifier ######################
speedCascade = cv2.CascadeClassifier(r"/home/pi/Documents/Capstone-main/Classifier/haar/speedLimitStage17.xml")
# cap = cv2.VideoCapture(0) # For Webcam
# Use cap.set() as needed
#############################################################



############ For PiCamera ###################################
import picamera
import io

# memory stream so that photos don't need to be saved in a file
stream = io.BytesIO() 
camera = picamera.PiCamera()
camera.framerate = 60
camera.resolution = (800,480)
camera.awb_mode = 'auto'
#camera.image_effect = 'denoise'
#############################################################

counter = 0

####################### MAIN ################################
while True:

    # get a picture and specify parameters
    camera.capture(stream, format = 'jpeg')
    # Convert the picture into a numpy array    
    buff = np.frombuffer(stream.getvalue(), dtype=np.uint8)
    stream.seek(0)
    # Create an OpenCV image
    img = cv2.imdecode(buff,1)
    
    
    imgGray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY) #Convert to greyscale 
    scaleVal = 1 + cv2.getTrackbarPos("Scale",trackBarName)/1000 #parameter scaling
    neig = cv2.getTrackbarPos("Neig",trackBarName) #parameter scaling
    
    objects = speedCascade.detectMultiScale(img,scaleVal,neig) #run object detection algorithm
    for (x,y,w,h) in objects:
        area = w*h
        minArea = cv2.getTrackbarPos("Min Area",trackBarName)
        if area > minArea:
            cv2.rectangle(img,(x,y),(x+w,y+h),(255,0,0),2)
            speedSignCropped = img[int(np.floor((2*y+h)/2)):int(np.floor((2*y+h)/2+y+h-((2*y+h)/2))),int(np.floor(x+w*0.15)):int(np.floor(x+w*0.95))]
            speedSignCroppedBigger = cv2.resize(speedSignCropped,(480,300))
            cv2.imshow("Cropped", speedSignCroppedBigger)
            
            gray = cv2.cvtColor(speedSignCropped,cv2.COLOR_BGR2GRAY)
            thresh = cv2.adaptiveThreshold(gray,255,1,1,25,2)
            temp_name,contours,hierarchy = cv2.findContours(thresh,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)

            speedLimit = []

            for  cnt in contours:
                if cv2.contourArea(cnt)>15:
                    [x,y,w,h] = cv2.boundingRect(cnt)
                    if h>15 and not(h/w>1.5) and (h/w>1):
                        cv2.rectangle(speedSignCropped,(x,y),(x+w,y+h),(0,255,0),2)
                        roi = thresh[y:y+h,x:x+w]
                        roismall = cv2.resize(roi,(10,10))
                        roismall = roismall.reshape((1,100))
                        roismall = np.float32(roismall)
                        retval, results, neigh_resp, dists = model.findNearest(roismall, k = 1) 
                        speedLimit = np.append(speedLimit,results[0][0])
                        if len(speedLimit) == 2:
                            print(speedLimit)

                    
    window_name = "frontCamera"
    cv2.namedWindow(window_name,cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)                                
    cv2.imshow("frontCamera", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
#############################################################
