import numpy as np
import cv2
import picamera
import io
print('cv2 imported')
############################### Initialization #################################################### 
samples = np.loadtxt(r'/home/pi/Desktop/Documents/Capstone-local/generalsamples.data',np.float32)
responses = np.loadtxt(r'/home/pi/Desktop/Documents/Capstone-local/generalresponses.data',np.float32)
responses = responses.reshape((responses.size,1))
model = cv2.ml.KNearest_create()
model.train(samples,cv2.ml.ROW_SAMPLE,responses)
speedCascade = cv2.CascadeClassifier(r"/home/pi/Desktop/Documents/Capstone-local/Classifier/haar/speedLimitStage17.xml")
stream = io.BytesIO() 
camera = picamera.PiCamera()
camera.framerate = 60
camera.resolution = (800,480)
camera.awb_mode = 'auto'
counter = 0
scaleVal = 1.2 
neig = 0
###################################################################################################


##################################### Main Loop ###################################################
################################ Speed limit is stored in "speedLimit" variable ###################
while True:
    # get a picture and specify parameters
    camera.capture(stream, format = 'jpeg')
    # Convert the picture into a numpy array    
    buff = np.frombuffer(stream.getvalue(), dtype=np.uint8)
    stream.seek(0)
    # Create an OpenCV image
    img = cv2.imdecode(buff,1)
    imgGray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY) #Convert to greyscale 
    
    objects = speedCascade.detectMultiScale(img,scaleVal,neig) #run object detection algorithm
    for (x,y,w,h) in objects:
        cv2.rectangle(img,(x,y),(x+w,y+h),(255,0,0),2)
        speedSignCropped = img[int(np.floor((2*y+h)/2)):int(np.floor((2*y+h)/2+y+h-((2*y+h)/2))),int(np.floor(x+w*0.15)):int(np.floor(x+w*0.95))]
        gray = cv2.cvtColor(speedSignCropped,cv2.COLOR_BGR2GRAY)
        thresh = cv2.adaptiveThreshold(gray,255,1,1,25,2)
        temp_name,contours,hierarchy = cv2.findContours(thresh,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    
        speedLimitArray = []
        for  cnt in contours:
            if cv2.contourArea(cnt)>1:
                [x,y,w,h] = cv2.boundingRect(cnt)
                if h>15 and not(h/w>1.5) and (h/w>1):
                    cv2.rectangle(speedSignCropped,(x,y),(x+w,y+h),(0,255,0),2)
                    roi = thresh[y:y+h,x:x+w]
                    roismall = cv2.resize(roi,(10,10))
                    roismall = roismall.reshape((1,100))
                    roismall = np.float32(roismall)
                    retval, results, neigh_resp, dists = model.findNearest(roismall, k = 1) 
                    speedLimitArray = np.append(speedLimitArray,results[0][0])

        if len(speedLimitArray) == 2:
            counter = counter+1
            if counter > 1:
                detected = max(speedLimitArray)*10+min(speedLimitArray)
                if detected == 20 or detected == 30 or detected == 40 or detected == 50 or detected == 55 or \
                   detected == 60 or detected == 65 or detected == 70 or detected == 75 or detected == 80:
                       speedLimit = detected 
                       print(speedLimit)
                counter = 0;
###################################################################################################