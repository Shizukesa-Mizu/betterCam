import cv2  # to record and perform motion detection
import collections  # to store buffers in deque data structures
import time  # to for buffer and timeout time measurement
import datetime  # to display current time on recording

# ==========================================
# SETTINGS
# ==========================================

buffer = 3  # seconds of video to record before motion happened
timeout = 10  # seconds of video to record after motion has ceased
MIN_CONTOUR_AREA = 500  # Minimum area to consider as valid motion
OUTPUT_FILENAME = "recorded.mp4"
vid_src = 0

# ==========================================
# INITIALIZATION
# ==========================================


# intialize video capture source and returns the cap object and video properties.
def setup_camera(source):
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return None, 0, 0, 0

    # get relevant information about the video stream
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    # if FPS is not reported or reportly 0, assume it to be 30
    if fps == 0.0:
        fps = 30.0

    return cap, fps, frame_width, frame_height


# makes the VideoWriter object for saving the recording to a file
def setup_video_writer(filename, fps, width, height):
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")  # specify file encode and extension
    frame_size = (width, height)  # specify dimensions, taken from video source
    return cv2.VideoWriter(filename, fourcc, fps, frame_size)  # return the VideoWriter


# make a buffer of fixed size based on fps and how long of a buffer to keep
# uses the deque data structure which is more efficient than python lists
def initialize_buffer(fps, buffer_seconds):
    buffer_size = int(fps * buffer_seconds)
    return collections.deque(maxlen=buffer_size)


# ==========================================
# MOTION DETECTION
# ==========================================


# detect motion by applying background subtraction
def detect_motion_contours(frame, back_sub):
    # apply background subtraction
    fg_mask = back_sub.apply(frame)

    # apply erosion algorithm to remove noise
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    mask_eroded = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)

    # find contours edge, boundary of moving pixels
    contours, _ = cv2.findContours(
        mask_eroded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    # filter contours by size
    valid_contours = [
        cnt for cnt in contours if cv2.contourArea(cnt) > MIN_CONTOUR_AREA
    ]

    return valid_contours


# draw boxes to check view movement and adjust sensitivity
def draw_bounding_boxes(frame, contours):
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
    frame_buffer = initialize_buffer(fps, buffer)

    # MOG2 Background Subtractor
    back_sub = cv2.createBackgroundSubtractorMOG2(detectShadows=False)

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
            font_scale = 0.5
            color = (255, 255, 255)  # White color (BGR)
            thickness = 1
            cv2.putText(
                frame, text, position, font, font_scale, color, thickness, cv2.LINE_AA
            )
            if is_recording:
                if time.time() - last_motion_time > timeout:
                    is_recording = False
                    print(f"Recording stopped. No motion for {timeout}s.")
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
    start_surveillance(vid_src)
