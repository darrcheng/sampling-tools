import time

from labjack import ljm

# Load Labjack
handle = ljm.openS("T7", "ANY", "ANY")
relay_input = "DIO6"

try:
    while True:
        # Close valve
        ljm.eWriteName(handle, relay_input, 0)
        time.sleep(0.1)

        # Open valve
        ljm.eWriteName(handle, relay_input, 1)
        time.sleep(0.1)
except KeyboardInterrupt:
    # Close valve
    ljm.eWriteName(handle, relay_input, 0)
    time.sleep(0.1)


# import time
# from labjack import u3

# # Open the first found LabJack U3
# device = u3.U3()

# # Configure FIO6 as digital output
# device.configIO(FIOAnalog=0)

# try:
#     # Loop to toggle FIO6
#     while True:
#         # Set FIO6 to high (True)
#         device.setFIOState(6, 1)
#         time.sleep(0.1)  # Wait for 0.1 seconds

#         # Set FIO6 to low (False)
#         device.setFIOState(6, 0)
#         time.sleep(0.1)  # Wait for 0.1 seconds

# except KeyboardInterrupt:
#     # Clean up and reset the pin to low before exiting if user interrupts (Ctrl+C)
#     device.setFIOState(6, 0)
#     print("Exiting and cleaning up.")
#     device.close()
