import numpy as np
import cv2
import threading

# Initialize webcam capture with reduced resolution and frame rate
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 15)

# Function to handle nothing for trackbars
def nothing(x):
    pass

# Set up trackbars for dynamic HSV threshold adjustment
cv2.namedWindow("Trackbars")
cv2.createTrackbar("L-H", "Trackbars", 160, 179, nothing)
cv2.createTrackbar("L-S", "Trackbars", 100, 255, nothing)
cv2.createTrackbar("L-V", "Trackbars", 20, 255, nothing)
cv2.createTrackbar("U-H", "Trackbars", 179, 179, nothing)
cv2.createTrackbar("U-S", "Trackbars", 255, 255, nothing)
cv2.createTrackbar("U-V", "Trackbars", 255, 255, nothing)

# Process frames in a separate thread
def process_frame():
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Apply Gaussian Blur to smooth edges
        blurred_frame = cv2.GaussianBlur(frame, (5, 5), 0)
        imgHSV = cv2.cvtColor(blurred_frame, cv2.COLOR_BGR2HSV)
        
        # Get HSV values from trackbars
        l_h = cv2.getTrackbarPos("L-H", "Trackbars")
        l_s = cv2.getTrackbarPos("L-S", "Trackbars")
        l_v = cv2.getTrackbarPos("L-V", "Trackbars")
        u_h = cv2.getTrackbarPos("U-H", "Trackbars")
        u_s = cv2.getTrackbarPos("U-S", "Trackbars")
        u_v = cv2.getTrackbarPos("U-V", "Trackbars")
        
        # Define HSV range for mask
        lower = np.array([l_h, l_s, l_v])
        upper = np.array([u_h, u_s, u_v])
        mask = cv2.inRange(imgHSV, lower, upper)
        
        # Apply dilation and erosion based on contour size
        kernel_small = np.ones((3, 3))
        kernel_large = np.ones((5, 5))
        imgDial = cv2.dilate(mask, kernel_large, iterations=2)
        imgErode = cv2.erode(imgDial, kernel_small, iterations=1)
        
        # Detect contours
        contours, _ = cv2.findContours(imgErode, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > 1500:
                perimeter = cv2.arcLength(cnt, True)
                shape = cv2.approxPolyDP(cnt, 0.04 * perimeter, True)
                corners = len(shape)
                
                # If the shape has 7 corners, it may be a heptagon
                if corners == 7:
                    x, y, w, h = cv2.boundingRect(cnt)
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
                    cv2.drawContours(frame, [shape], -1, (0, 255, 0), 2, lineType=cv2.LINE_AA)
        
        # Display the frame
        cv2.imshow('Frame', frame)
        
        # Press 'q' to exit the loop
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release resources if loop exits
    cap.release()
    cv2.destroyAllWindows()

# Start processing in a thread
thread = threading.Thread(target=process_frame)
thread.start()

# Wait for the processing to complete
thread.join()
