#!/usr/bin/env python3

import argparse

parser = argparse.ArgumentParser(description = "Parser of High Resolution binary (not MIDI) files")
parser.add_argument("filename", help="Load <FILENAME> for plotting, analysis or dumping in a text file")

action = parser.add_mutually_exclusive_group(required=True)
action.add_argument("-d", "--dump", help="Dump the content of FILENAME on the terminal", action="store_true")
action.add_argument("-p", "--plot", help="Plot the content of FILENAME with matplotlib", action="store_true")

file_format = parser.add_mutually_exclusive_group(required=True)
file_format.add_argument("-12", help="Assume the file has two 12-bit data points from same      ADC channel per timestamp",
        dest="bits_12", action="store_true")
file_format.add_argument("-8", help="Assume the file has three 8-bit data points from different ADC channel per timestamp",
        dest="bits_8", action="store_true")
args = parser.parse_args()

def parse_2_12(b0, b1, b2):
    d2 = b0 + ((b1 & 0x0F) << 8)
    d1 = (b2 << 4) + ((b1 & 0xF0) >> 4)
    return d1, d2

if args.plot:
    import matplotlib.pyplot as plt      # importing here to allow saving without GTK
    import numpy as np

if args.bits_12:
    data = []
    time = []

    with open(args.filename, mode='rb') as file:
        b = file.read()
        for i in range(0, len(b), 4):
            d1, d2 = parse_2_12(b[i], b[i+1], b[i+2])
            data.append(d1)
            data.append(d2)
            time.append(b[i+3])

    if args.dump:
        print("Time\tadc_at_time\tadc_at_time_plus")
        for i in range(len(time)):
            print(time[i], data[2*i], "", data[2*i+1], sep="\t")
    else:
        fig, ax = plt.subplots()
        ax.plot(time, data)
        ax.set_ylim(0, 4096)
        ax.set_xlabel('time (s)')
        ax.set_ylabel('Raw ADC value')
        plt.show()

else:
    data1 = []
    data2 = []
    data3 = []
    time = []

    with open(args.filename, mode='rb') as file:
        b = file.read()
        old_time = b[3]
        for i in range(0, len(b), 4):
            data1.append(b[i])
            data2.append(b[i+1])
            data3.append(b[i+2])
            curr_time = b[i+3]
            while (curr_time < old_time):
                curr_time += 256
            time.append(curr_time)
            old_time = curr_time

    if args.dump:
        print("Time\tadc1\tadc2\tadc3")
        for i in range(len(time)):
            print(time[i], data1[i], data2[i], data3[i], sep="\t")
    else:
        fig, ax = plt.subplots()
        ax.plot(time, data1, label="ADC1")
        ax.plot(time, data2, label="ADC2")
        ax.plot(time, data3, label="ADC3")
        ax.set_ylim(0, 256)
        ax.set_xlabel('time (us)')
        ax.set_ylabel('Raw ADC value')
        ax.legend()
        plt.show()
