from flask import Flask, render_template, Response
from flask_socketio import SocketIO
import cv2
import numpy as np
import base64
from threading import Thread, Lock
import time

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins='*')

# Global variables
camera = None
camera_lock = Lock()
running = True

# Get camera source from environment variable or use default
CAMERA_SOURCE = os.getenv('CAMERA_SOURCE', '0')

def init_camera():
    """Initialize camera with fallback options"""
    try:
        # Try to open the camera
        camera = cv2.VideoCapture(int(CAMERA_SOURCE))
        if not camera.isOpened():
            raise Exception("Camera not available")
        return camera
    except Exception as e:
        print(f"Error initializing camera: {e}")
        # Try to use a test video file if available
        if os.path.exists('test_video.mp4'):
            return cv2.VideoCapture('test_video.mp4')
        # If no test video, create a dummy camera that generates a test pattern
        return create_dummy_camera()

def create_dummy_camera():
    """Create a dummy camera that generates a test pattern"""
    class DummyCamera:
        def __init__(self):
            self.frame_count = 0
            self.width = 640
            self.height = 480

        def isOpened(self):
            return True

        def read(self):
            # Create a test pattern
            frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
            # Draw a moving arrow
            center_x = int(self.width/2 + 50 * np.sin(self.frame_count/30))
            center_y = int(self.height/2 + 50 * np.cos(self.frame_count/30))
            cv2.arrowedLine(frame, 
                          (center_x-50, center_y), 
                          (center_x+50, center_y), 
                          (0, 0, 255), 5)
            self.frame_count += 1
            return True, frame

        def release(self):
            pass

    return DummyCamera()

# Initialize camera
camera = init_camera()

class VideoCamera:
    def __init__(self):
        self.video = cv2.VideoCapture(0)
        self.video.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.video.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.video.set(cv2.CAP_PROP_FPS, 15)
        
        # Initialize HSV values
        self.hsv_values = {
            'l_h': 0, 'l_s': 50, 'l_v': 50,
            'u_h': 179, 'u_s': 255, 'u_v': 255
        }
        
        # Store the latest frames
        self.latest_processed = None
        self.latest_mask = None
        self.frame_lock = Lock()
    
    def __del__(self):
        self.video.release()

    def get_frame(self):
        success, frame = self.video.read()
        if not success:
            return None, None

        # Process frame
        processed_frame, mask = self.process_frame(frame)
        
        # Store the latest frames
        with self.frame_lock:
            self.latest_processed = processed_frame
            self.latest_mask = mask
        
        # Convert frames to JPEG
        ret, jpeg = cv2.imencode('.jpg', processed_frame)
        ret_mask, jpeg_mask = cv2.imencode('.jpg', mask)
        
        return jpeg.tobytes(), jpeg_mask.tobytes()

    def get_latest_processed(self):
        with self.frame_lock:
            if self.latest_processed is not None:
                ret, jpeg = cv2.imencode('.jpg', self.latest_processed)
                return jpeg.tobytes()
        return None

    def get_latest_mask(self):
        with self.frame_lock:
            if self.latest_mask is not None:
                ret, jpeg = cv2.imencode('.jpg', self.latest_mask)
                return jpeg.tobytes()
        return None

    def process_frame(self, frame):
        if frame is None:
            return None, None

        # Apply Gaussian Blur
        blurred_frame = cv2.GaussianBlur(frame, (7, 7), 0)
        imgHSV = cv2.cvtColor(blurred_frame, cv2.COLOR_BGR2HSV)
        
        # Create mask using current HSV values
        lower = np.array([self.hsv_values['l_h'], self.hsv_values['l_s'], self.hsv_values['l_v']])
        upper = np.array([self.hsv_values['u_h'], self.hsv_values['u_s'], self.hsv_values['u_v']])
        mask = cv2.inRange(imgHSV, lower, upper)
        
        # Apply morphological operations
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        # Convert mask to BGR for visualization
        mask_colored = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
        
        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Draw all contours for debugging
        cv2.drawContours(mask_colored, contours, -1, (0, 255, 0), 1)
        
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > 1000:
                perimeter = cv2.arcLength(cnt, True)
                approx = cv2.approxPolyDP(cnt, 0.02 * perimeter, True)
                
                if 5 <= len(approx) <= 8:
                    x, y, w, h = cv2.boundingRect(cnt)
                    aspect_ratio = float(w)/h
                    
                    if 0.5 <= aspect_ratio <= 2.0:
                        # Draw on both frames
                        cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
                        cv2.drawContours(frame, [approx], -1, (0, 255, 0), 2)
                        cv2.rectangle(mask_colored, (x, y), (x + w, y + h), (255, 0, 0), 2)
                        cv2.drawContours(mask_colored, [approx], -1, (0, 255, 0), 2)
                        
                        M = cv2.moments(cnt)
                        if M["m00"] != 0:
                            cx = int(M["m10"] / M["m00"])
                            cy = int(M["m01"] / M["m00"])
                            cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)
                            cv2.circle(mask_colored, (cx, cy), 5, (0, 0, 255), -1)
        
        return frame, mask_colored

    def update_hsv(self, values):
        self.hsv_values.update(values)

def gen_processed_frames():
    global camera, running
    while running:
        with camera_lock:
            if camera:
                frame_data = camera.get_latest_processed()
                if frame_data:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n')
        time.sleep(0.033)  # Limit to ~30 fps

def gen_mask_frames():
    global camera, running
    while running:
        with camera_lock:
            if camera:
                mask_data = camera.get_latest_mask()
                if mask_data:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + mask_data + b'\r\n')
        time.sleep(0.033)  # Limit to ~30 fps

# Background frame processing thread
def process_frames():
    global camera, running
    while running:
        with camera_lock:
            if camera:
                camera.get_frame()  # This will update both frames
        time.sleep(0.033)  # Limit to ~30 fps

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed_processed')
def video_feed_processed():
    return Response(gen_processed_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed_mask')
def video_feed_mask():
    return Response(gen_mask_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@socketio.on('connect')
def handle_connect():
    global camera
    print("Client connected")
    with camera_lock:
        if camera is None:
            camera = VideoCamera()
            # Start the frame processing thread
            Thread(target=process_frames, daemon=True).start()

@socketio.on('disconnect')
def handle_disconnect():
    global camera, running
    print("Client disconnected")
    with camera_lock:
        if camera:
            camera.__del__()
            camera = None
    running = False

@socketio.on('update_hsv')
def handle_hsv_update(data):
    global camera
    print("Updating HSV values:", data)
    with camera_lock:
        if camera:
            camera.update_hsv(data)

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True) 
