import numpy as np
import cv2
import threading
import time
from queue import Queue

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
cv2.moveWindow("Trackbars", 0, 0)  # Move window to top-left corner
# Modified default values for better arrow detection
cv2.createTrackbar("L-H", "Trackbars", 0, 179, nothing)    # Lower hue
cv2.createTrackbar("L-S", "Trackbars", 50, 255, nothing)   # Lower saturation
cv2.createTrackbar("L-V", "Trackbars", 50, 255, nothing)   # Lower value
cv2.createTrackbar("U-H", "Trackbars", 179, 179, nothing)  # Upper hue
cv2.createTrackbar("U-S", "Trackbars", 255, 255, nothing)  # Upper saturation
cv2.createTrackbar("U-V", "Trackbars", 255, 255, nothing)  # Upper value

# Create windows for debugging
cv2.namedWindow("Mask")
cv2.namedWindow("Frame")
cv2.moveWindow("Mask", 650, 0)  # Position mask window next to the frame

# Create a queue for frame processing
frame_queue = Queue(maxsize=2)
processed_queue = Queue(maxsize=2)
running = True

# Process frames in a separate thread
def process_frame():
    global running
    while running:
        if not frame_queue.empty():
            frame = frame_queue.get()
            
            # Apply Gaussian Blur to smooth edges
            blurred_frame = cv2.GaussianBlur(frame, (7, 7), 0)  # Increased blur kernel
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
            
            # Apply morphological operations
            kernel = np.ones((5, 5), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)  # Remove noise
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)  # Fill gaps
            
            # Detect contours
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Draw all contours for debugging
            contour_frame = frame.copy()
            cv2.drawContours(contour_frame, contours, -1, (0, 255, 0), 1)
            
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area > 1000:  # Reduced minimum area
                    perimeter = cv2.arcLength(cnt, True)
                    approx = cv2.approxPolyDP(cnt, 0.02 * perimeter, True)  # Adjusted epsilon
                    
                    # Check if shape could be an arrow (between 5 and 8 corners)
                    if 5 <= len(approx) <= 8:
                        x, y, w, h = cv2.boundingRect(cnt)
                        aspect_ratio = float(w)/h
                        
                        # Additional checks for arrow-like shapes
                        if 0.5 <= aspect_ratio <= 2.0:  # Reasonable aspect ratio for arrows
                            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
                            cv2.drawContours(frame, [approx], -1, (0, 255, 0), 2)
                            
                            # Draw center point
                            M = cv2.moments(cnt)
                            if M["m00"] != 0:
                                cx = int(M["m10"] / M["m00"])
                                cy = int(M["m01"] / M["m00"])
                                cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)
            
            # Create a composite frame with both mask and processed frame
            processed_data = {
                'frame': frame,
                'mask': mask
            }
            
            # Put processed frame in the queue
            if not processed_queue.full():
                processed_queue.put(processed_data)
        else:
            time.sleep(0.01)  # Small delay to prevent busy waiting

# Start processing thread
process_thread = threading.Thread(target=process_frame)
process_thread.start()

# Main loop for capturing and displaying frames
try:
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        # Put frame in processing queue
        if not frame_queue.full():
            frame_queue.put(frame.copy())
        
        # Display processed frame if available
        if not processed_queue.empty():
            processed_data = processed_queue.get()
            cv2.imshow('Frame', processed_data['frame'])
            cv2.imshow('Mask', processed_data['mask'])
        
        # Handle window events and check for exit
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break

finally:
    # Cleanup
    running = False
    process_thread.join()
    cap.release()
    cv2.destroyAllWindows()
