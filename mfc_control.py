import csv
from datetime import datetime
import os
import time
import tkinter as tk
from tkinter import ttk
from labjack import ljm
import yaml
import threading


# Load config file
program_path = os.path.dirname(os.path.realpath(__file__))
with open("mfc_config.yml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

num_mfc = config["num_mfc"]

# Create file
start_time = datetime.now()
current_date = start_time.strftime("%Y-%m-%d")
subfolder_path = os.path.join(os.getcwd(), current_date)
os.makedirs(subfolder_path, exist_ok=True)

# Create CSV file and writer
file_datetime = start_time.strftime("%Y%m%d_%H%M%S")
csv_filename = "MFC_" + file_datetime + ".csv"
csv_filepath = os.path.join(subfolder_path, csv_filename)

# Create file header
header = ["datetime"]
for i in range(num_mfc):
    header.append(config[f"mfc{i+1}"]["name"] + "_setpoint")
    header.append(config[f"mfc{i+1}"]["name"] + "_flowrate")

# Write CSV header
with open(csv_filepath, mode="w", newline="") as data_file:
    data_writer = csv.writer(data_file, delimiter=",")
    data_writer.writerow(header)

# Set the MFCs
handle = ljm.openS("T4", "ANY", "ANY")
for i in range(num_mfc):
    mfc = config[f"mfc{i+1}"]
    setpoint = mfc["setpoint"]
    scale = mfc["scale"]
    offset = mfc["offset"]
    ljm.eWriteName(handle, mfc["flow_set"], (setpoint - offset) / scale)

# Tkinter GUI setup
root = tk.Tk()
root.title("MFC Controller")

# Create MFC frames
mfc_labels = {}
mfc_setpoints = {}
mfc_flows = {}

for i in range(num_mfc):
    mfc_name = config[f"mfc{i+1}"]["name"]
    frame = ttk.Frame(root, padding=10)
    frame.grid(row=i, column=0, sticky="w")

    mfc_label = ttk.Label(
        frame, text=f"{mfc_name}:", font=("Arial", 12, "bold")
    )
    mfc_label.grid(row=0, column=0, sticky="w")

    setpoint_label = ttk.Label(
        frame, text=f"Setpoint: {config[f'mfc{i+1}']['setpoint']}"
    )
    setpoint_label.grid(row=1, column=0, sticky="w")
    mfc_setpoints[mfc_name] = setpoint_label

    flow_label = ttk.Label(frame, text="Flowrate: 0")
    flow_label.grid(row=2, column=0, sticky="w")
    mfc_flows[mfc_name] = flow_label

import random


def update_mfc_data():
    while True:
        try:
            data = [datetime.now()]
            for i in range(num_mfc):
                mfc_name = config[f"mfc{i+1}"]["name"]
                mfc = config[f"mfc{i+1}"]
                scale = mfc["scale"]
                offset = mfc["offset"]
                flowrate = ljm.eReadName(handle, mfc["flow_read"]) * scale + offset
                # flowrate = random.randint(0, 100)

                # Update flow rate in the GUI
                mfc_flows[mfc_name].config(text=f"Flowrate: {flowrate}")

                data.append(mfc["setpoint"])
                data.append(flowrate)

            # Write data to CSV
            with open(csv_filepath, mode="a", newline="") as data_file:
                data_writer = csv.writer(data_file, delimiter=",")
                data_writer.writerow(data)

            # Wait for the next read
            time.sleep(config["read_interval"])
        except:
            pass


# Run data update in a separate thread to keep GUI responsive
data_thread = threading.Thread(target=update_mfc_data, daemon=True)
data_thread.start()

# Run the Tkinter event loop
root.mainloop()


# import csv
# from datetime import datetime
# import os
# import time

# from labjack import ljm
# import yaml


# # Load Labjack
# # handle = ljm.openS("T7", "ANY", "ANY")

# # Load config file
# program_path = os.path.dirname(os.path.realpath(__file__))
# with open("mfc_config.yml", "r", encoding="utf-8") as f:
#     config = yaml.safe_load(f)

# num_mfc = config["num_mfc"]

# # Create file
# start_time = datetime.now()
# current_date = start_time.strftime("%Y-%m-%d")
# subfolder_path = os.path.join(os.getcwd(), current_date)
# os.makedirs(subfolder_path, exist_ok=True)

# # Create CSV file and writer
# file_datetime = start_time.strftime("%Y%m%d_%H%M%S")
# csv_filename = "MFC_" + file_datetime + ".csv"
# csv_filepath = os.path.join(subfolder_path, csv_filename)


# # Create file header
# header = ["datetime"]
# for i in range(num_mfc):
#     header.append(config[f"mfc{i+1}"]["name"] + "_setpoint")
#     header.append(config[f"mfc{i+1}"]["name"] + "_flowrate")

# # Write CSV header
# with open(csv_filepath, mode="w", newline="") as data_file:
#     data_writer = csv.writer(data_file, delimiter=",")
#     data_writer.writerow(header)

# # Set the MFCs
# for i in range(num_mfc):
#     mfc = config[f"mfc{i+1}"]
#     setpoint = mfc["setpoint"]
#     # ljm.eWriteName(handle, mfc["flow_set"], setpoint)

# # Every second read the MFCs and write to file
# start_time = time.monotonic()
# while True:
#     data = [datetime.now()]
#     for i in range(num_mfc):
#         mfc = config[f"mfc{i+1}"]
#         flowrate = 0  # ljm.eReadName(handle, mfc["flow_read"])
#         data.append(mfc["setpoint"])
#         data.append(flowrate)

#     with open(csv_filepath, mode="a", newline="") as data_file:
#         data_writer = csv.writer(data_file, delimiter=",")
#         data_writer.writerow(data)

#     # Wait until next read
#     curr_time = time.monotonic()
#     sleep_time = config["read_interval"] - (curr_time - start_time)
#     if sleep_time > 0:
#         time.sleep(sleep_time)
#     start_time = start_time + config["read_interval"]
