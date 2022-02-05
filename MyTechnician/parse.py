#!/usr/bin/env python3

import argparse, mido, bz2
from mido import Message, MidiFile, MidiTrack
import mytechnician

parser = argparse.ArgumentParser()
parser.add_argument("filename", help="Load <FILENAME> for plotting, analysis or dumping in a text file")
action = parser.add_mutually_exclusive_group(required=True)
action.add_argument("-d", "--dump", help="Dump the content of FILENAME on the terminal", action="store_true")
action.add_argument("-p", "--plot", help="Plot the content of FILENAME with matplotlib", action="store_true")
action.add_argument("-s", "--stat", help="Print summary statistics about FILENAME", action="store_true")
action.add_argument("-a", "--analysis", help="Plot analysis for MIDI velocity from ADC dump", action="store_true")
parser.add_argument("--ignore-midi-time", help="Use the ADC values sequentially, disregarding MIDI time", action="store_true")
parser.add_argument("-q", "--quiet", help="Do not report housekeeping messages", action="store_true")
args = parser.parse_args()

mt = mytechnician.mt()

def load_data():
    x = 0
    for msg in MidiFile(file=bz2.open(args.filename, 'rb')).play():
        if (msg.type == 'sysex' and
            msg.data[0] == defined.MIDI_VENDOR):

                if msg.data[1] <= defined.MIDI_MAX_ADC_VALUE:
                    yield x, msg.data[2] + msg.data[1] * 128, msg.data[3]
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
    first_note = False
    for xi, yi, note in load_data():
        if not first_note:
            first_note = note
        if first_note == note:
            x.append(xi)
            y.append(yi)
        else:
            print("Ignoring note", note)

    fig, ax = plt.subplots()
    ax.plot(x,y, label="MIDI note " + str(note))
    ax.set_ylim(0, 4096);
    ax.set_xlabel('time (s)')
    ax.set_ylabel('Raw ADC value')
    ax.legend()
    plt.show()
else:
    print("Time_(s)  ADC_value MIDI_note")
    for xi, yi, note in load_data():
        print(xi, yi, note)
