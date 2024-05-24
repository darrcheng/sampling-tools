import math
import schedule
import u3
import time
import ljtickdac
import os
import csv
import datetime as dt
from simple_pid import PID

PID_TIME = 1   # how often pid runs (secs)
DIGI_TIME = 0.25 # how often read from digihelic
WRITE_TIME = 1 # write to csv file

use_pid = False
stop_running = False

class CSVFile:
    def __init__(self):
        self.previous_measurement = None
        self.previous_count = None
        self.filename = ''
        self.rpm = 0
    
    #csv file
    def setFilename(self):
        current_date = dt.datetime.today().strftime("%m-%d-%Y")
        self.filename = f'Blower_Data/blower_data_{current_date}.csv'

    def set_count_and_measure(self, measure, count):
        self.previous_measurement = measure
        self.previous_count = count

    #get voltage from prev line
    def getPrevVoltage(self):
        count_rows = 0
        with open(self.filename, 'r') as csv_file:
            csv_reader = csv.reader(csv_file)
            for row in csv_reader:
                count_rows +=1
            
        if (count_rows > 1): 
            with open(self.filename) as csv_file:
                last_line = csv_file.readlines()[-1] 
            return(last_line.split(',')[0])
        else:
            return 'n/a'  #no voltages have been sent to blower yet

    def writeToCSV(self, volts, rpm, flow, avgVolts, avgFlow, gains):
        filename = self.filename 
        # rpm = time_label.cget("text")[12:]
        time = dt.datetime.now().strftime("%H:%M:%S")

        with open(filename, 'a', newline='') as csv_file:
            csv_writer = csv.writer(csv_file)
            checkSize = os.path.getsize(filename)
           
            if (checkSize == 0):  # writing header
                csv_writer.writerow(['Voltage Sent', 'RPM', 'Flow Rate', 'Current Time'])
            
            if (volts != None): #not sure this condition is needed anymore
                csv_writer.writerow([volts, rpm, flow, time]) 
            else:
                preVolts = self.getPrevVoltage()
                csv_writer.writerow([preVolts, rpm, flow, time])

class PIDObject:
    def __init__(self):
        # pid controller (needs tuning)
        kP, kI, kD = (0.0034, 0.0001722, 0.0003) 
        self.setpoint = 400 #lpm
        self.flow_rate = 0
        self.pid = PID(kP, kI, kD, self.setpoint, output_limits=(0,5), starting_output=3.75)

        # for reseting
        # kP, kI, kD = (0.0,0.00,0)
        # self.pid = PID(kP, kI, kD, self.setpoint, output_limits=(0,5), starting_output=0)

        self.digi_voltage = []
        self.data = {
        'time': [],
        'Flow Rate (avg)': [],
        'Flow Rate (curr)': [],
        'Setpoint': [],
        }
        self.volts_sent = 0
        self.average_volts = 0

    def updateDigiVoltage(self, d):
        global DIGI_TIME
        global PID_TIME
        
        cs_voltage = d.getAIN(1)
        print("cs: ", cs_voltage)
        self.digi_voltage.append(cs_voltage)

        maxLength = (PID_TIME / DIGI_TIME) 
        if (maxLength < 1): #if pid less than digi
            maxLength = 1
        if len(self.digi_voltage) > maxLength: 
            self.digi_voltage.pop(0)

    def averageDigiVoltage(self):
        sum = 0
        length = len(self.digi_voltage)
        for i in range(length):
            sum += self.digi_voltage[i]
        self.average_volts = (sum/length)

    def calcFlowRate(self, volts, updateSelf=True):
        #convert volts to pressure
        mA = 8.475 * volts  # according to labjack website
        p_wc = (mA/64) - (1/16) # in wc
        p_atm = 101325 # Pa
        p_Pa = (p_wc * 248.84) + p_atm # convert to pascals and absolute
        
        # convert pressure to flow rate, using bernoulli
        density = 1.225 # kg/m^3
        deltaP = p_Pa - p_atm

        velocity = math.sqrt(2*(deltaP)/density) #might be negative, need to check
        
        d = 2 * 0.0254 # units: m
        area = math.pi/4*(d*d)
        flow_rate = area * velocity #m^3/s
        flow_rate_lpm = flow_rate * 60000 

        if (updateSelf):    #change flow rate
            self.flow_rate = flow_rate_lpm
        else:
            return flow_rate_lpm

    def update_graph_data(self, d): #not using, for testing only
        global data #change, due to callback

        time = dt.datetime.now().strftime("%H:%M:%S")
        self.data['time'].append(time)
        self.data['Flow Rate (avg)'].append(self.flow_rate)
        v = d.getAIN(1) #remove eventually
        currFlow = self.calcFlowRate(v, False)
        self.data['Flow Rate (curr)'].append(currFlow)
        self.data['Setpoint'].append(self.setpoint)
        data = self.data
        #print('D: ', data)

def runPID(pid_obj, tdac, d):
    pid_obj.averageDigiVoltage()
    avg_cs_voltage = pid_obj.average_volts
    pid_obj.calcFlowRate(avg_cs_voltage)
    flow_rate = pid_obj.flow_rate
    
    #pid_obj.update_graph_data(d)
    volts_to_blower = pid_obj.pid(flow_rate)

    tdac.update(float(volts_to_blower), 0.0)
    pid_obj.volts_sent = volts_to_blower

def update_time_difference(csv, pid_obj, d, timer, counter):
    startMeasures = d.getFeedback(timer, counter)
    current_measurement = startMeasures[0]
    current_count = startMeasures[1]

    volts = pid_obj.volts_sent 
    #flow_rate = pid_obj.flow_rate #change
    currVolts = d.getAIN(1)
    flow_rate = pid_obj.calcFlowRate(currVolts, False)
    avgVolts = pid_obj.average_volts
    if (avgVolts != 0):    
        avgFlow_Rate = pid_obj.calcFlowRate(avgVolts, False)
    else:
        avgFlow_Rate = None
    gains = pid_obj.pid.tunings
    
    if csv.previous_measurement is not None:
        time_diff = (current_measurement - csv.previous_measurement) / 4000000
        count_diff = current_count - csv.previous_count
        current_rpm = (count_diff / 6) / (time_diff / 60)
        # time_label.config(text="Blower RPM: {:.2f}".format(current_rpm))
        csv.writeToCSV(volts, current_rpm, flow_rate, avgVolts, avgFlow_Rate, gains) 

    csv.set_count_and_measure(current_measurement, current_count)

# run blower without pid controller, using pid setpoint
def runBlower(tdac, pid_obj):  
    volts = (0.0131 * pid_obj.setpoint) + 0.7221
    pid_obj.calcFlowRate(volts) # so csv file gets updated

    if (volts < 2): volts = 0

    tdac.update(float(volts), 0.0)
    pid_obj.volts_sent = volts


def main():
    global WRITE_TIME
    global PID_TIME
    global DIGI_TIME
    global use_pid
    # Open the LabJack U3
    d = u3.U3()
    d.configIO(
        NumberOfTimersEnabled=1,
        EnableCounter1=1,
        TimerCounterPinOffset=4,
        FIOAnalog=15,
        EIOAnalog=0,
    )
    #set up the ljtickdac 
    dioPin = 6 
    tdac = ljtickdac.LJTickDAC(d, dioPin)

    # Set the configuration for the first timer:
    t0Config = u3.TimerConfig(0, TimerMode=10, Value=0)

    d.getFeedback(t0Config)
    d.configTimerClock(TimerClockBase=None, TimerClockDivisor=None)
    counter = u3.Counter(1)
    timer = u3.Timer(0)

    #check for file
    filepath='./Blower_Data'
    if not os.path.exists(filepath):
        os.mkdir(filepath)

    csv = CSVFile()
    csv.setFilename()
    pid_obj = PIDObject()

    schedule.every(DIGI_TIME).seconds.do(pid_obj.updateDigiVoltage, d) 
    if (use_pid):
        schedule.every(PID_TIME).seconds.do(runPID, pid_obj, tdac, d)
    else:
        schedule.every(PID_TIME).seconds.do(runBlower, tdac, pid_obj)

    schedule.every(WRITE_TIME).seconds.do(update_time_difference, csv, pid_obj, d, timer, counter)
    #runs serially, not in parallel 
    #(only problem if run time greater than intervals), which it is not

    while not stop_running: 
        schedule.run_pending()
        time.sleep(1)

def stop_schedules():
    global stop_running
    stop_running = True

if __name__ == '__main__':
    main()
