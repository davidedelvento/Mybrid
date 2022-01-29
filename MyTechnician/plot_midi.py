#!/usr/bin/env python3

import argparse
import mido
from mido import Message, MidiFile, MidiTrack
from cdefine import CDefine

parser = argparse.ArgumentParser()
parser.add_argument("filename", help="Load <FILENAME> for immediate plotting or text file dumping")
parser.add_argument("--dump", help="Dump the content of FILENAME on the terminal", action="store_true")
args = parser.parse_args()

defined = CDefine('../RaspberryPiPico/My_MIDI_constants.h')

def load_data():
    i = 0
    for msg in MidiFile(args.filename).play():
        if msg.type == 'sysex':
            if (msg.data[0] == defined.MIDI_VENDOR and
                msg.data[1] <= defined.MIDI_MAX_ADC_VALUE):

                i = i + 1
                yield i, msg.data[2] + msg.data[1] * 128

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
    for xi, yi in enumerate(load_data()):
        print(xi, yi)
