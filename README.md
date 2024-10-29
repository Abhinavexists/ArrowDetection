# Arrow Detection with OpenCV

This project captures real-time video from a webcam to detect arrow shapes using color-based HSV filtering and contour detection in OpenCV. Dynamic HSV thresholds can be adjusted using trackbars to refine the color range for detecting specific shapes in varying lighting conditions.

## Features
- **Real-Time Video Processing**: Continuously captures frames from the webcam and applies color-based shape detection.
- **Adjustable HSV Thresholds**: Trackbars enable real-time adjustment of HSV color values for fine-tuning detection sensitivity.
- **Shape Detection**: Uses contour approximation to identify arrow shapes, highlighting them by drawing bounding boxes and contours.

## Requirements
- **Python 3.6+**

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/Abhinavks1405/ArrowDetection.git
    cd ArrowDetection
    ```

2. Install dependencies using `requirements.txt`:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1. Run the program:
    ```bash
    python main.py
    ```

2. Use the trackbars displayed in the "Trackbars" window to adjust the HSV threshold values:
    - **L-H, L-S, L-V**: Lower bounds for hue, saturation, and value.
    - **U-H, U-S, U-V**: Upper bounds for hue, saturation, and value.
   
3. Press `q` to exit the application.

## Code Explanation

### Main Components

- **Trackbars**: Allow real-time adjustments to the HSV range, helping filter specific colors.
- **Gaussian Blur**: Applied to each frame to smooth edges, which improves contour detection.
- **HSV Masking**: The filtered range is isolated to highlight potential shapes in the specified color range.
- **Contour Detection**: Detects shapes, approximates contours, and calculates corner counts to identify arrow shapes.
- **Multithreading**: Runs the frame processing in a separate thread for improved performance.

### Shape Detection Logic
- A contour is classified as an arrow if it meets specified criteria for shape, based on contour approximation.
- Detected arrows are highlighted with bounding boxes and contours in the video frame.

## Customization

You can modify HSV ranges and the contour area threshold in the code to detect different shapes or adjust sensitivity. The contour area threshold (`1500` in this case) can be adjusted depending on the size and distance of shapes in the video frame.

## Troubleshooting

If you encounter an exit code or memory error:
- Ensure OpenCV is up-to-date:
    ```bash
    pip install --upgrade opencv-python
    ```
- Lower the resolution or adjust the HSV ranges if detection is not accurate.

## License
This project is licensed under the MIT License.
