import cv2
import os
import tkinter as tk
from tkinter import filedialog
from datetime import datetime, timedelta


def select_folder(title="Select a folder"):
    folder_selected = filedialog.askdirectory(title=title)
    return folder_selected


def extract_timestamp(filename):
    try:
        # Extract timestamp from format: image_YYYYMMDDHHMMSS
        timestamp_str = filename.split("_")[1].split(".")[0]
        return datetime.strptime(timestamp_str, "%Y%m%d%H%M%S")
    except:
        return None


def log_to_file(log_file, message):
    with open(log_file, "a") as f:
        f.write(message + "\n")


def create_timelapse(input_folder, output_folder, fps=30):
    # Extract the folder name, which is assumed to be a date
    date_str = os.path.basename(input_folder)

    # Output video file name
    output_path = os.path.join(output_folder, f"timelapse_{date_str}.avi")
    log_file_path = os.path.join(output_folder, f"log_{date_str}.txt")

    # Get all files from the folder
    images = [
        img
        for img in os.listdir(input_folder)
        if img.endswith(".png") or img.endswith(".jpg")
    ]

    # Sort the images by name
    images.sort()

    # Log the timestamp of the first and last frame
    first_timestamp = extract_timestamp(images[0])
    last_timestamp = extract_timestamp(images[-1])
    log_to_file(log_file_path, f"First frame timestamp: {first_timestamp}")
    log_to_file(log_file_path, f"Last frame timestamp: {last_timestamp}")

    # Check for time gaps more than 30 minutes and log
    for i in range(len(images) - 1):
        current_timestamp = extract_timestamp(images[i])
        next_timestamp = extract_timestamp(images[i + 1])

        if next_timestamp - current_timestamp > timedelta(minutes=30):
            log_to_file(
                log_file_path,
                f"Gap detected: {current_timestamp} to {next_timestamp}",
            )

    # Read the first image to get dimensions
    img = cv2.imread(os.path.join(input_folder, images[0]))
    height, width, layers = img.shape

    # Create a VideoCapture object
    fourcc = cv2.VideoWriter_fourcc(*"XVID")
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    total_images = len(images)
    last_percentage = 0
    progress_bar_length = 20  # Length of the progress bar in blocks

    # Initialize progress bar
    progress_bar = "-" * progress_bar_length

    # Loop through image files to create video
    for i in range(total_images):
        img = cv2.imread(os.path.join(input_folder, images[i]))
        out.write(img)

        # Calculate progress as a percentage
        progress = int((i + 1) / total_images * 100)

        # Update and print progress bar at 5% increments
        if progress >= last_percentage + 5:
            filled_blocks = int(progress / 5)
            progress_bar = "*" * filled_blocks + "-" * (
                progress_bar_length - filled_blocks
            )
            print(f"Progress: [{progress_bar}] {progress}%")
            last_percentage = progress

    out.release()
    cv2.destroyAllWindows()
    print("Timelapse creation complete!")


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()

    input_folder = select_folder("Select the folder containing the images")
    if not input_folder:
        print("No input folder selected. Exiting.")
        exit()

    # output_folder = select_folder(
    #     "Select the folder to save the timelapse video"
    # )
    output_folder = r"C:\Users\d95st\timelapse"
    if not output_folder:
        print(
            "No output folder selected. Using the current directory as default."
        )
        output_folder = "."

    create_timelapse(input_folder, output_folder)
