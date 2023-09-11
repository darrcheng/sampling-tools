import serial
import time
import os
import tkinter as tk
from tkinter import ttk
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


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
        # For rolling average
        self.data_buffer = []

        # Setup GUI components
        self.setup_gui()

        # Schedule data collection
        self.root.after(250, self.collect_data)

    def setup_gui(self):
        # # Display area for windspeed and direction
        # self.lbl_windspeed = ttk.Label(self.root, text="Windspeed (m/s): ")
        # self.lbl_windspeed.grid(row=0, column=0, sticky="w", pady=5, padx=5)

        # self.lbl_winddirection = ttk.Label(self.root, text="Wind Direction: ")
        # self.lbl_winddirection.grid(row=1, column=0, sticky="w", pady=5, padx=5)

        # Polar plot for rolling average
        self.figure = Figure(figsize=(5, 5))
        self.ax = self.figure.add_subplot(111, projection="polar")
        self.ax.set_theta_zero_location("N")  # 0 degrees at the top
        self.ax.set_theta_direction(-1)  # Clockwise
        self.canvas = FigureCanvasTkAgg(self.figure, self.root)
        self.canvas.get_tk_widget().grid(row=2, column=0, padx=5, pady=5)

        # Labels to display current wind speed and direction below the graph
        self.lbl_current_windspeed = ttk.Label(self.root, text="")
        self.lbl_current_winddirection = ttk.Label(self.root, text="")
        self.lbl_current_windspeed.grid(row=3, column=0, pady=2)
        self.lbl_current_winddirection.grid(row=4, column=0, pady=2)

        # Close button
        self.btn_close = ttk.Button(
            self.root, text="Close", command=self.close_app
        )
        self.btn_close.grid(row=5, column=0, pady=10)

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

    def update_plot(self):
        self.ax.clear()

        if len(self.data_buffer) >= 8:
            windspeeds = [entry[0] for entry in self.data_buffer[-8:]]
            wind_directions = [
                np.deg2rad(entry[1]) for entry in self.data_buffer[-8:]
            ]
            avg_speed = np.mean(windspeeds)
            avg_direction = np.mean(wind_directions)

            self.ax.bar(
                avg_direction, avg_speed, width=0.1, alpha=0.6
            )  # Set width for a narrower bar

            # Update labels below the graph
            self.lbl_current_windspeed[
                "text"
            ] = f"Current Windspeed: {windspeeds[-1]:.2f} m/s"
            self.lbl_current_winddirection[
                "text"
            ] = f"Current Wind Direction: {wind_directions[-1]*180/np.pi:.2f}°"

        self.canvas.draw()

    def close_app(self):
        self.ser.close()  # Close the serial port
        self.root.quit()

    def collect_data(self):
        start_time = time.time()

        data = self.read_data_until(b"\r")
        if data:
            # Extract and display data
            _, windspeed, wind_direction, _ = data.split()
            # self.lbl_windspeed["text"] = f"Windspeed (m/s): {windspeed}"
            # self.lbl_winddirection["text"] = f"Wind Direction: {wind_direction}"

            # Log the data to file
            self.log_data(data)

            # Save data for plotting
            self.data_buffer.append((float(windspeed), float(wind_direction)))
            if len(self.data_buffer) > 8:
                self.data_buffer.pop(0)

            self.update_plot()

            # Force an update to the GUI
            self.root.update_idletasks()

        elapsed_time = time.time() - start_time
        sleep_duration = max(250 - (elapsed_time * 1000), 0)
        self.root.after(int(sleep_duration), self.collect_data)

    def read_data_until(self, delimiter):
        buffer = b""
        while True:
            char = self.ser.read(1)  # Read a single byte
            if char:
                buffer += char
                if buffer.endswith(
                    delimiter
                ):  # If the delimiter is found, break the loop
                    break
            else:  # If there's a long pause (no data), then clear the buffer to avoid stale data accumulation.
                buffer = b""
        return buffer.decode("utf-8").strip()


if __name__ == "__main__":
    root = tk.Tk()
    app = WindDataLogger(root)
    root.mainloop()
