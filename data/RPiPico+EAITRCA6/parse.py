#!/usr/bin/env python3

import argparse

parser = argparse.ArgumentParser(description = "Parser of High Resolution binary (not MIDI) files")
parser.add_argument("filename", help="Load <FILENAME> for plotting, analysis or dumping in a text file")

action = parser.add_mutually_exclusive_group(required=True)
action.add_argument("-d", "--dump", help="Dump the content of FILENAME on the terminal", action="store_true")
action.add_argument("-p", "--plot", help="Plot the content of FILENAME with matplotlib", action="store_true")
args = parser.parse_args()

data = []
time = []

print("Count\ttime\tadc_at_time\tadc_at_time_plus")

with open(args.filename, mode='rb') as file:
    b = file.read()
    for i in range(0, len(b), 4):
        d2 = b[i] + ((b[i+1] & 0x0F) << 8)
        d1 = (b[i+2] << 4) + ((b[i+1] & 0xF0) >> 4)
        data.append(d1)
        data.append(d2)
        time.append(b[i+3])
        print(i, time[-1], data[-2], "", data[-1], sep="\t")

