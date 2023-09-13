import serial
import time
import os
import tkinter as tk
from tkinter import ttk


class WindDataLogger:
    def __init__(self, root, port="COM3"):
        self.root = root
        self.root.title("Wind Data Logger")

        self.ser = serial.Serial(
            port,
            38400,
            timeout=1,
            bytesize=serial.EIGHTBITS,
            stopbits=serial.STOPBITS_ONE,
            parity=serial.PARITY_NONE,
        )

        # For logging
        self.current_date = time.strftime("%Y%m%d")

        # Setup GUI components
        self.setup_gui()

        # Schedule data collection
        self.root.after(250, self.collect_data)

    def setup_gui(self):
        # Display area for windspeed and direction
        self.lbl_windspeed = ttk.Label(self.root, text="Windspeed (m/s): ")
        self.lbl_windspeed.grid(row=0, column=0, sticky="w", pady=5, padx=5)

        self.lbl_winddirection = ttk.Label(self.root, text="Wind Direction: ")
        self.lbl_winddirection.grid(row=1, column=0, sticky="w", pady=5, padx=5)

    def get_log_filename(self):
        # Create a folder named 'anemometer' if it doesn't exist
        if not os.path.exists("anemometer"):
            os.makedirs("anemometer")

        # Generate the filename based on the current date
        filename = time.strftime(
            "windspeed_%Y%m%d.csv"
        )  # Change the extension to .csv
        return os.path.join("anemometer", filename)

    def log_data(self, data):
        log_filename = self.get_log_filename()

        # If the date changes, reset the current date
        if self.current_date != time.strftime("%Y%m%d"):
            self.current_date = time.strftime("%Y%m%d")

        # Open the log file for the day
        with open(log_filename, "a") as f:
            # If the file is new/empty, add the header
            if f.tell() == 0:
                header = "Timestamp, Sensor Address, Windspeed (m/s), Wind Direction, Status\n"  # Added Timestamp column
                f.write(header)

            formatted_data = f"{time.ctime()}, {', '.join(data.split())}\n"
            f.write(formatted_data)

    def collect_data(self):
        line = b""
        while True:
            char = self.ser.read(1)  # Read a single byte
            if char == b"\r":  # If carriage return, break loop
                break
            line += char

        data = line.decode("utf-8").strip()
        if data:
            # Extract and display data
            _, windspeed, wind_direction, _ = data.split()
            self.lbl_windspeed["text"] = f"Windspeed (m/s): {windspeed}"
            self.lbl_winddirection["text"] = f"Wind Direction: {wind_direction}"

            # Log the data to file
            self.log_data(data)

        # Schedule the next data collection
        self.root.after(250, self.collect_data)


if __name__ == "__main__":
    root = tk.Tk()
    app = WindDataLogger(root)
    root.mainloop()
