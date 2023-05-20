import numpy as np
import cv2


cap = cv2.VideoCapture(0)

while(True):
    ret, frame = cap.read()
    imgHSV = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV) 
 
    lower = np.array([160,100,20])
    upper = np.array([179,255,255])
    mask= cv2.inRange(imgHSV,lower,upper)
    kernel = np.ones((3,3)) 
    imgDial = cv2.dilate(mask, kernel, iterations=3) 
    imgErode = cv2.erode(imgDial, kernel, iterations=2) 
    
    contours, heirarchy = cv2.findContours(imgErode, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE) 
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area>1500:
            perimeter = cv2.arcLength(cnt, True)
            shape = cv2.approxPolyDP(cnt,perimeter/40, True) 
            corners = len(shape) 

            if corners==7:
              cv2.drawContours(image=frame, contours=contours, contourIdx=-1, color=(0, 255, 0), thickness=2, lineType=cv2.LINE_AA)
     
    cv2.imshow('frame',frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()