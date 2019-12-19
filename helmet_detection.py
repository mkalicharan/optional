import cv2
import numpy as np

face_cascade = cv2.CascadeClassifier('haar_cascade_face.xml')


cap = cv2.VideoCapture(0)


while True:
   
	_, img = cap.read()
	ORIG=  img
	gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

	faces = face_cascade.detectMultiScale(gray, 1.1, 4)
	(height, width) = gray.shape[:2]
	X1,Y1,X2,Y2 =0,0,0,0
	for (x, y, w, h) in faces:
		y_min = 0
		
		if y> 150:
			y_min = y-150
		
		#cv2.rectangle(img, (x, y), (x+w, y_min), (255, 0, 0), 2)
		temp = img[y_min:y, x:x+w]
		X1,X2,Y1,Y2 =x, x+w, y_min, y
		cv2.imwrite("temp.jpg", temp)
	
	#print (X1,Y1,X2,Y2)
	
	IMG_TEMP = cv2.imread("temp.jpg")
#################################
	hsv = cv2.cvtColor(IMG_TEMP, cv2.COLOR_BGR2HSV)
		
	#defining the range of Yellow color
	yellow_lower = np.array([22,60,200],np.uint8)
	yellow_upper = np.array([60,255,255],np.uint8)

	#finding the range yellow colour in the image
	yellow = cv2.inRange(hsv, yellow_lower, yellow_upper)

	#Morphological transformation, Dilation         
	kernal = np.ones((5 ,5), "uint8")

	blue=cv2.dilate(yellow, kernal)

	res=cv2.bitwise_and(IMG_TEMP, IMG_TEMP, mask = yellow)

	#Tracking Colour (Yellow) 
	(_,contours,hierarchy)=cv2.findContours(yellow,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
	
	for pic, contour in enumerate(contours):
			area = cv2.contourArea(contour)
			if(area>300):
					
					x,y,w,h = cv2.boundingRect(contour)     
					IMG_TEMP = cv2.rectangle(IMG_TEMP,(x,y),(x+w,y+h),(255,0,0),3)
					cv2.putText(img, "helmet", (X2, Y2), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 4)
					temp_img = cv2.rectangle(img,(X1,Y1),(X2,Y2),(255,0,0),3)
	cv2.imshow("Color Tracking",img)
	IMG_TEMP = cv2.flip(IMG_TEMP,1)
	cv2.imshow("Yellow",res)

	k = cv2.waitKey(30) & 0xff
	if k==27:
		break
	
cap.release()
