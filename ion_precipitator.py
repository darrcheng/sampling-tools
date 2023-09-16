import tkinter as tk
from tkinter import ttk, font
from threading import Thread
import time
import csv
import os
from datetime import datetime
import u3
import ljtickdac

# Initialize LabJack U3
d = u3.U3()
d.getCalibrationData()
d.configIO(FIOAnalog=0x0F)
dioPin = 4
tdac = ljtickdac.LJTickDAC(d, dioPin)

# Initialize parameters
scaling_factor = 500
toggle_time = 30.0
state = "OFF"
running = False


# Function to get new CSV filename
def get_csv_filename():
    """Generate a new CSV filename based on the current date and time."""
    return f"ion_data/ion_precipitator_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"


# Create an "ion_data" folder if it doesn't exist
if not os.path.exists("ion_data"):
    os.makedirs("ion_data")

csv_filename = get_csv_filename()


def voltage_loop():
    """Main loop for toggling voltage and updating GUI."""
    global state, running, toggle_time, csv_filename
    toggle_timer = 0.0

    while running:
        start_time = time.time()
        set_voltage = float(entry_set_voltage.get())
        toggle_time = float(entry_toggle_time.get())
        dacA_on = set_voltage / scaling_factor
        toggle_timer += 1.0

        # Toggle voltage
        if toggle_timer >= toggle_time:
            if state == "ON":
                state = "OFF"
                tdac.update(0.0, 0.0)
            else:
                state = "ON"
                tdac.update(dacA_on, 0.0)
            toggle_timer = 0

        # Update GUI
        volt = d.getAIN(0) * scaling_factor
        current_time = datetime.now().strftime("%H:%M:%S")
        time_label.config(text=f"Current Time: {current_time}")
        status_label.config(text=f"Voltage Status: {state}")
        monitor_label.config(text=f"Voltage Monitor: {volt} V")

        # Log to CSV
        with open(csv_filename, "a", newline="") as csv_file:
            csv_writer = csv.writer(csv_file)
            if csv_file.tell() == 0:
                csv_writer.writerow(
                    [
                        "Timestamp",
                        "State",
                        "Set Voltage (V)",
                        "AIN0 Voltage (V)",
                    ]
                )
            csv_writer.writerow(
                [current_time, state, set_voltage if state == "ON" else 0, volt]
            )

        # Sleep
        elapsed_time = time.time() - start_time
        time.sleep(max(0, 1.0 - elapsed_time))

        # Check if it's a new day and create a new CSV file
        if datetime.now().strftime("%H:%M:%S") == "00:00:00":
            csv_filename = get_csv_filename()


def start_stop():
    """Start or stop the voltage toggling loop."""
    global running
    if btn_start["text"] == "Start":
        running = True
        btn_start.config(text="Stop")
        thread = Thread(target=voltage_loop)
        thread.daemon = True
        thread.start()
    else:
        running = False
        btn_start.config(text="Start")


def close_app():
    """Close the application."""
    global running
    running = False
    d.close()
    root.quit()
    root.destroy()


# Initialize Tkinter GUI
root = tk.Tk()
root.title("Voltage Controller")
root.geometry("400x250")
root.configure(bg="light gray")

# Create a style
style = ttk.Style(root)
style.configure("TButton", font=("Helvetica", 12))
style.configure("TLabel", font=("Helvetica", 12))

app_font = font.nametofont("TkDefaultFont")
app_font.config(size=12)

# Center widgets by adjusting row and column weights
for i in range(2):
    root.grid_columnconfigure(i, weight=1)
for i in range(6):
    root.grid_rowconfigure(i, weight=1)

# Entry for Set Voltage
lbl_set_voltage = ttk.Label(root, text="Set Voltage (V):", font=app_font)
lbl_set_voltage.grid(column=0, row=0, sticky="nsew", padx=10, pady=5)
entry_set_voltage = ttk.Entry(root, font=app_font)
entry_set_voltage.grid(column=1, row=0, sticky="nsew", padx=10, pady=5)
entry_set_voltage.insert(0, "1000")

# Entry for Voltage Interval
lbl_toggle_time = ttk.Label(root, text="Voltage Interval (s):", font=app_font)
lbl_toggle_time.grid(column=0, row=1, sticky="nsew", padx=10, pady=5)
entry_toggle_time = ttk.Entry(root, font=app_font)
entry_toggle_time.grid(column=1, row=1, sticky="nsew", padx=10, pady=5)
entry_toggle_time.insert(0, "30")

# Display fields
time_label = ttk.Label(root, text="Current Time: ", font=app_font)
time_label.grid(column=0, row=2, columnspan=2, sticky="nsew", padx=10, pady=5)

status_label = ttk.Label(root, text="Voltage Status: ", font=app_font)
status_label.grid(column=0, row=3, columnspan=2, sticky="nsew", padx=10, pady=5)

monitor_label = ttk.Label(root, text="Voltage Monitor: ", font=app_font)
monitor_label.grid(
    column=0, row=4, columnspan=2, sticky="nsew", padx=10, pady=5
)

# Start/Stop Button
btn_start = ttk.Button(root, text="Start", command=start_stop, style="TButton")
btn_start.grid(column=0, row=5, sticky="nsew", padx=10, pady=10)

# Close Button
btn_close = ttk.Button(root, text="Close", command=close_app, style="TButton")
btn_close.grid(column=1, row=5, sticky="nsew", padx=10, pady=10)


root.mainloop()
