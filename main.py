import cv2
import collections
import time
import datetime

# ==========================================
# SETTINGS
# ==========================================
PRE_MOTION_BUFFER_SECONDS = 3
RECORDER_TIMEOUT_SECONDS = 10
MIN_CONTOUR_AREA = 500  # Minimum area to consider as valid motion
OUTPUT_FILENAME = "recorded.mp4"

# ==========================================
# INITIALIZATION
# ==========================================


def setup_camera(source=0):
    """
    Initializes the video capture source and returns the cap object
    along with video properties (fps, width, height).
    """
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return None, 0, 0, 0

    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    # Fallback if FPS is not detected
    if fps == 0.0:
        fps = 30.0

    return cap, fps, frame_width, frame_height


def setup_video_writer(filename, fps, width, height):
    """
    Initializes the VideoWriter object for saving the output.
    """
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    frame_size = (width, height)
    return cv2.VideoWriter(filename, fourcc, fps, frame_size)


def initialize_buffer(fps, buffer_seconds):
    """
    Creates a fixed-size circular buffer (deque) to store frames
    before motion is detected.
    """
    buffer_size = int(fps * buffer_seconds)
    return collections.deque(maxlen=buffer_size)


# ==========================================
# MOTION DETECTION
# ==========================================


def detect_motion_contours(frame, back_sub):
    """
    Processes a frame to detect motion using Background Subtraction.
    Returns a list of contours that exceed the minimum area threshold.
    """
    # 1. Apply background subtraction
    fg_mask = back_sub.apply(frame)

    # 2. Apply global threshold to remove shadows (ensure binary mask)
    _, mask_thresh = cv2.threshold(fg_mask, 180, 255, cv2.THRESH_BINARY)

    # 3. Apply morphological erosion to remove noise/speckles
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    mask_eroded = cv2.morphologyEx(mask_thresh, cv2.MORPH_OPEN, kernel)

    # 4. Find contours
    contours, _ = cv2.findContours(
        mask_eroded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    # 5. Filter contours by size
    valid_contours = [
        cnt for cnt in contours if cv2.contourArea(cnt) > MIN_CONTOUR_AREA
    ]

    return valid_contours


def draw_bounding_boxes(frame, contours):
    """
    Draws rectangles around detected motion contours.
    """
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 200), 3)
    return frame


# ==========================================
# PUT IT ALL TOGETHER
# ==========================================


def start_surveillance(cam_source=0):
    # --- Initialization ---
    cap, fps, width, height = setup_camera(cam_source)
    if cap is None:
        return

    out = setup_video_writer(OUTPUT_FILENAME, fps, width, height)
    frame_buffer = initialize_buffer(fps, PRE_MOTION_BUFFER_SECONDS)

    # MOG2 Background Subtractor
    back_sub = cv2.createBackgroundSubtractorMOG2()

    # State variables
    is_recording = False
    last_motion_time = time.time()

    print(f"Surveillance started. FPS: {fps:.2f}. Press 'q' to exit.")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Always add current frame to the circular buffer
            frame_buffer.append(frame)

            # --- Motion Detection Phase ---
            motion_contours = detect_motion_contours(frame, back_sub)
            motion_detected_now = len(motion_contours) > 0

            # Create a copy for drawing so we don't save drawn boxes to raw footage
            # (Note: If you WANT boxes in the saved video, use 'frame' directly)
            display_frame = frame.copy()

            if motion_detected_now:
                last_motion_time = time.time()
                draw_bounding_boxes(display_frame, motion_contours)

            # --- Recording Logic Phase ---

            # CASE A: Motion just started, and we aren't recording yet
            if motion_detected_now and not is_recording:
                is_recording = True
                print("MOTION DETECTED! Writing pre-motion buffer...")

                # Dump the pre-motion buffer into the video file
                for buffered_frame in list(frame_buffer):
                    out.write(buffered_frame)

            # CASE B: Currently recording (handling timeout)
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            text = f"Time: {current_time}"
            font = cv2.FONT_HERSHEY_SIMPLEX
            position = (10, 30)  # Top-left corner (x, y)
            font_scale = 1
            color = (255, 255, 255)  # White color (BGR)
            thickness = 2
            cv2.putText(
                frame, text, position, font, font_scale, color, thickness, cv2.LINE_AA
            )
            if is_recording:
                if time.time() - last_motion_time > RECORDER_TIMEOUT_SECONDS:
                    is_recording = False
                    print(
                        f"Recording stopped. No motion for {RECORDER_TIMEOUT_SECONDS}s."
                    )
                else:
                    # Write the current frame with detections
                    # (User's original code wrote the frame with boxes)

                    draw_bounding_boxes(frame, motion_contours)
                    out.write(frame)

            # 2. Define text parameters

            # 3. Draw the text on the frame_out (which is always displayed)
            # --- Display Phase ---
            cv2.imshow("Surveillance Feed", display_frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    finally:
        # --- Cleanup ---
        print("Cleaning up resources...")
        cap.release()
        out.release()
        cv2.destroyAllWindows()


# ==========================================
# ENTRY POINT
# ==========================================

if __name__ == "__main__":
    start_surveillance(0)
