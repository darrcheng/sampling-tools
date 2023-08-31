import cv2
from PIL import Image, ImageDraw, ImageFont
import time
import datetime
import numpy as np
import os


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

# Manually set the resolution to 1920x1080
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)


# Confirm the frame width and height
print("Frame width:", cap.get(cv2.CAP_PROP_FRAME_WIDTH))
print("Frame height:", cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# Create a root directory 'images' if not exists
if not os.path.exists("images"):
    os.makedirs("images")

while True:
    start_time = time.time()

    ret, frame = cap.read()

    if not ret:
        print("Failed to grab frame")
        break

    frame_with_timestamp = add_timestamp(frame)

    # For display, resize the frame
    display_frame = cv2.resize(frame_with_timestamp, (640, 360))

    current_date = datetime.datetime.now().strftime("%Y-%m-%d")

    # Create a subfolder in 'images' with the current date if not exists
    folder_path = os.path.join("images", current_date)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    filename = f"{folder_path}/image_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
    cv2.imwrite(filename, frame_with_timestamp)

    cv2.imshow("Webcam", display_frame)

    end_time = time.time()
    elapsed_time = end_time - start_time
    sleep_time = 10 - elapsed_time  # Changed time to 5 seconds
    if sleep_time > 0:
        time.sleep(sleep_time)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
