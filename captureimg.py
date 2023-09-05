import cv2
from PIL import Image, ImageDraw, ImageFont
import time
import datetime
import numpy as np
import os
import io
import sys


class MultiWriter:
    def __init__(self, *outputs):
        self.outputs = outputs

    def write(self, data):
        for output in self.outputs:
            output.write(data)

    def flush(self):
        for output in self.outputs:
            output.flush()


def add_timestamp(image):
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(image)
    draw = ImageDraw.Draw(pil_image)
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    font_size = 30
    font = ImageFont.truetype("arial.ttf", font_size)
    text_position = (image.shape[1] - 300, image.shape[0] - 50)
    draw.text(text_position, current_time, (255, 255, 255), font=font)
    image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    return image


# Initialize the webcam
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

# Create a root directory 'images' if not exists
if not os.path.exists("images"):
    os.makedirs("images")


class WebcamError(Exception):
    pass


# Redirect stderr to a buffer
sys.stderr = buffer = io.StringIO()
original_stderr = sys.stderr

while True:
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    folder_path = os.path.join("images", current_date)

    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    log_filepath = f"{folder_path}/error_log_{current_date}.txt"
    log_file = open(log_filepath, "a")
    sys.stderr = MultiWriter(original_stderr, log_file)

    try:
        start_time = time.time()

        ret, frame = cap.read()

        if not ret:
            raise WebcamError("Failed to grab frame")

        frame_with_timestamp = add_timestamp(frame)
        display_frame = cv2.resize(frame_with_timestamp, (640, 360))
        # current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        # folder_path = os.path.join("images", current_date)

        # if not os.path.exists(folder_path):
        #     os.makedirs(folder_path)

        filename = f"{folder_path}/image_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
        cv2.imwrite(filename, frame_with_timestamp)
        cv2.imshow("Webcam", display_frame)

        end_time = time.time()
        elapsed_time = end_time - start_time
        sleep_time = 5 - elapsed_time

        if sleep_time > 0:
            time.sleep(sleep_time)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    except WebcamError:
        current_timestamp = datetime.datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        error_message = f"{current_timestamp}: Webcam error"
        print(error_message)  # This will now print to both stderr and the log

        # Attempt to re-initialize the webcam
        cap.release()
        time.sleep(2)  # Give it a short break before re-initializing
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

    except Exception as e:
        current_timestamp = datetime.datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        error_message = f"{current_timestamp}: {str(e)}"

        # Print error message to screen
        print(error_message)

        # Append the error to a daily log file
        with open(
            f"{folder_path}/error_log_{current_date}.txt", "a"
        ) as log_file:
            log_file.write(error_message + "\n")

    finally:
        # Close the log file and revert stderr after each iteration
        log_file.close()
        sys.stderr = original_stderr


cap.release()
cv2.destroyAllWindows()
