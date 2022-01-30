#!/usr/bin/env python3

import argparse, mido, bz2
from mido import Message, MidiFile, MidiTrack
from cdefine import CDefine
import mytechnician

parser = argparse.ArgumentParser()
parser.add_argument("filename", help="Load <FILENAME> for immediate plotting or text file dumping")
parser.add_argument("--dump", help="Dump the content of FILENAME on the terminal", action="store_true")
parser.add_argument("-i", "--ignore-midi-time", help="Use the ADC values sequentially, disregarding MIDI time packets", action="store_true")
parser.add_argument("-s", "--silent", help="Do not report housekeeping messages", action="store_true")
args = parser.parse_args()

defined = CDefine('../RaspberryPiPico/My_MIDI_constants.h')
mt = mytechnician.mt()

def load_data():
    x = 0
    for msg in MidiFile(file=bz2.open(args.filename, 'rb')).play():
        if (msg.type == 'sysex' and
            msg.data[0] == defined.MIDI_VENDOR):

                if msg.data[1] <= defined.MIDI_MAX_ADC_VALUE:
                    yield x, msg.data[2] + msg.data[1] * 128
                elif not args.silent:
                    mt.pretty_print(msg.data, exclude=['MIDI_MAX_ADC_VALUE', 'MIDI_RTC'])

                if args.ignore_midi_time:
                    x = x + 1
                elif msg.data[1] == defined.MIDI_RTC:
                    old_x = x
                    x = (msg.data[1] + msg.data[2] * 128.) / 1000000 # us
                    while (x < old_x):
                        x += 16384 / 1000000 # us

if not args.dump:
    import matplotlib.pyplot as plt      # importing here to allow saving without GTK
    x = []
    y = []
    i = 0

    for xi, yi in load_data():
        x.append(xi)
        y.append(yi)

    fig, ax = plt.subplots()
    ax.plot(x,y)
    ax.set_ylim(0, 4096);
    plt.show()
else:
    print("Time (s)  ADC_value")
    for xi, yi in load_data():
        print(xi, yi)
